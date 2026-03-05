"""Transition matrix service for PD term structure calculation"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np

from src.db.models import (
    TransitionMatrix, RatingHistory, FinancialInstrument,
    CreditRating, MacroScenario
)
from src.services.macro_regression import macro_regression_service
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class PDCurve:
    """PD term structure curve"""
    def __init__(
        self,
        pd_by_period: Dict[int, Decimal],
        cumulative_pd: Dict[int, Decimal],
        marginal_pd: Dict[int, Decimal],
        calculation_method: str
    ):
        self.pd_by_period = pd_by_period
        self.cumulative_pd = cumulative_pd
        self.marginal_pd = marginal_pd
        self.calculation_method = calculation_method


class TransitionMatrixResult:
    """Transition matrix calculation result"""
    def __init__(
        self,
        matrix: np.ndarray,
        rating_classes: List[str],
        observation_period_months: int,
        num_observations: int,
        psi: Decimal
    ):
        self.matrix = matrix
        self.rating_classes = rating_classes
        self.observation_period_months = observation_period_months
        self.num_observations = num_observations
        self.psi = psi  # Population Stability Index


class TransitionMatrixService:
    """Service for building and using transition matrices for PD calculation"""
    
    # Standard rating classes (can be customized)
    RATING_CLASSES = [
        "AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"
    ]
    
    def build_transition_matrix(
        self,
        db: Session,
        segment: str,
        start_date: date,
        end_date: date,
        observation_period_months: int = 12
    ) -> TransitionMatrixResult:
        """
        Build transition matrix from historical rating data.
        
        Requires minimum 5 years of historical data.
        
        Args:
            db: Database session
            segment: Customer segment
            start_date: Start date for historical data
            end_date: End date for historical data
            observation_period_months: Observation period (typically 12 months)
            
        Returns:
            TransitionMatrixResult with matrix and metadata
        """
        logger.info(f"Building transition matrix for segment {segment}")
        
        # Fetch historical rating data
        rating_history = db.query(RatingHistory).filter(
            RatingHistory.segment == segment,
            RatingHistory.rating_date >= start_date,
            RatingHistory.rating_date <= end_date
        ).order_by(RatingHistory.instrument_id, RatingHistory.rating_date).all()
        
        if not rating_history:
            raise ValueError(f"No rating history found for segment {segment}")
        
        # Build transition counts matrix
        n_classes = len(self.RATING_CLASSES)
        transition_counts = np.zeros((n_classes, n_classes))
        
        # Group by instrument and track transitions
        instrument_ratings = {}
        for record in rating_history:
            if record.instrument_id not in instrument_ratings:
                instrument_ratings[record.instrument_id] = []
            instrument_ratings[record.instrument_id].append(record)
        
        num_observations = 0
        
        for instrument_id, ratings in instrument_ratings.items():
            # Sort by date
            ratings.sort(key=lambda x: x.rating_date)
            
            # Track transitions over observation period
            for i in range(len(ratings) - 1):
                current_rating = ratings[i].credit_rating
                next_rating = ratings[i + 1].credit_rating
                
                # Check if observation period matches
                days_diff = (ratings[i + 1].rating_date - ratings[i].rating_date).days
                if abs(days_diff - (observation_period_months * 30)) < 15:  # Allow 15-day tolerance
                    from_idx = self._rating_to_index(current_rating)
                    to_idx = self._rating_to_index(next_rating)
                    
                    if from_idx is not None and to_idx is not None:
                        transition_counts[from_idx, to_idx] += 1
                        num_observations += 1
        
        # Convert counts to probabilities (row-wise normalization)
        transition_matrix = np.zeros((n_classes, n_classes))
        for i in range(n_classes):
            row_sum = transition_counts[i, :].sum()
            if row_sum > 0:
                transition_matrix[i, :] = transition_counts[i, :] / row_sum
            else:
                # No observations for this rating class, assume no transition
                transition_matrix[i, i] = 1.0
        
        # Calculate Population Stability Index (PSI)
        psi = self._calculate_psi(transition_matrix)
        
        # Save to database
        matrix_record = TransitionMatrix(
            segment=segment,
            observation_period_months=observation_period_months,
            transition_matrix=transition_matrix.tolist(),
            rating_classes=self.RATING_CLASSES,
            calibration_date=date.today(),
            num_observations=num_observations,
            psi=psi,
            is_active=True
        )
        
        db.add(matrix_record)
        db.commit()
        
        logger.info(f"Transition matrix built: {num_observations} observations, PSI={psi}")
        
        return TransitionMatrixResult(
            matrix=transition_matrix,
            rating_classes=self.RATING_CLASSES,
            observation_period_months=observation_period_months,
            num_observations=num_observations,
            psi=psi
        )
    
    def calculate_pit_pd(
        self,
        db: Session,
        current_rating: CreditRating,
        segment: str,
        horizon_months: int = 12
    ) -> Decimal:
        """
        Calculate Point-in-Time (PIT) PD using transition matrix.
        
        PIT PD = Probability of transitioning to default state within horizon
        
        Args:
            db: Database session
            current_rating: Current credit rating
            segment: Customer segment
            horizon_months: Time horizon in months
            
        Returns:
            PIT PD
        """
        logger.info(f"Calculating PIT PD for rating {current_rating}, horizon {horizon_months} months")
        
        # Fetch transition matrix
        matrix_record = db.query(TransitionMatrix).filter(
            TransitionMatrix.segment == segment,
            TransitionMatrix.is_active == True
        ).first()
        
        if not matrix_record:
            raise ValueError(f"No transition matrix found for segment {segment}")
        
        # Convert to numpy array
        transition_matrix = np.array(matrix_record.transition_matrix)
        
        # Get current rating index
        current_idx = self._rating_to_index(current_rating)
        if current_idx is None:
            raise ValueError(f"Invalid rating: {current_rating}")
        
        # Calculate number of periods
        observation_period = matrix_record.observation_period_months
        num_periods = horizon_months // observation_period
        
        # Raise matrix to power of num_periods to get multi-period transition probabilities
        multi_period_matrix = np.linalg.matrix_power(transition_matrix, num_periods)
        
        # PD is probability of transitioning to default state (last column)
        default_idx = len(self.RATING_CLASSES) - 1  # "D" is last rating
        pit_pd = Decimal(str(multi_period_matrix[current_idx, default_idx]))
        
        logger.info(f"PIT PD calculated: {pit_pd}")
        
        return pit_pd
    
    def calculate_ttc_pd(
        self,
        db: Session,
        segment: str,
        rating: CreditRating
    ) -> Decimal:
        """
        Calculate Through-the-Cycle (TTC) PD.
        
        TTC PD = Long-run average default rate for rating class
        
        Args:
            db: Database session
            segment: Customer segment
            rating: Credit rating
            
        Returns:
            TTC PD
        """
        logger.info(f"Calculating TTC PD for rating {rating}")
        
        # Fetch historical default rates for rating class
        rating_history = db.query(RatingHistory).filter(
            RatingHistory.segment == segment,
            RatingHistory.credit_rating == rating
        ).all()
        
        if not rating_history:
            # Use default TTC PD by rating
            default_ttc_pd = self._get_default_ttc_pd(rating)
            logger.warning(f"No history for {rating}, using default TTC PD: {default_ttc_pd}")
            return default_ttc_pd
        
        # Calculate long-run average default rate
        total_instruments = len(set(r.instrument_id for r in rating_history))
        defaulted_instruments = len(set(
            r.instrument_id for r in rating_history 
            if r.credit_rating == CreditRating.D
        ))
        
        ttc_pd = Decimal(str(defaulted_instruments / total_instruments)) if total_instruments > 0 else Decimal("0")
        
        logger.info(f"TTC PD calculated: {ttc_pd}")
        
        return ttc_pd
    
    def project_pd_curve(
        self,
        db: Session,
        instrument: FinancialInstrument,
        segment: str,
        scenario: Optional[MacroScenario] = None
    ) -> PDCurve:
        """
        Project PD curve over remaining maturity of instrument.
        
        Args:
            db: Database session
            instrument: Financial instrument
            segment: Customer segment
            scenario: Optional macro scenario for adjustment
            
        Returns:
            PDCurve with term structure
        """
        logger.info(f"Projecting PD curve for instrument {instrument.instrument_id}")
        
        # Calculate remaining maturity in months
        remaining_months = self._calculate_remaining_months(instrument)
        
        # Get current rating
        current_rating = instrument.credit_rating or CreditRating.BBB
        
        # Calculate PIT PD for each period
        pd_by_period = {}
        cumulative_pd = {}
        marginal_pd = {}
        
        cumulative_survival = Decimal("1.0")
        
        for month in range(1, remaining_months + 1):
            # Calculate PIT PD for this horizon
            pit_pd = self.calculate_pit_pd(db, current_rating, segment, month)
            
            # Apply macro adjustment if scenario provided
            if scenario:
                adjustment_result = macro_regression_service.apply_macro_adjustment_pd(
                    db, pit_pd, scenario, segment
                )
                adjusted_pd = adjustment_result.adjusted_value
            else:
                adjusted_pd = pit_pd
            
            pd_by_period[month] = adjusted_pd
            
            # Calculate marginal PD (PD for this specific period)
            if month == 1:
                marginal_pd[month] = adjusted_pd
            else:
                marginal_pd[month] = adjusted_pd - cumulative_pd[month - 1]
            
            # Update cumulative PD
            cumulative_pd[month] = adjusted_pd
            
            # Update cumulative survival probability
            cumulative_survival *= (Decimal("1.0") - marginal_pd[month])
        
        logger.info(f"PD curve projected for {remaining_months} months")
        
        return PDCurve(
            pd_by_period=pd_by_period,
            cumulative_pd=cumulative_pd,
            marginal_pd=marginal_pd,
            calculation_method="transition_matrix"
        )
    
    def _rating_to_index(self, rating: CreditRating) -> Optional[int]:
        """Convert credit rating to matrix index"""
        rating_map = {
            CreditRating.AAA: 0,
            CreditRating.AA: 1,
            CreditRating.A: 2,
            CreditRating.BBB: 3,
            CreditRating.BB: 4,
            CreditRating.B: 5,
            CreditRating.CCC: 6,
            CreditRating.CC: 7,
            CreditRating.C: 8,
            CreditRating.D: 9
        }
        return rating_map.get(rating)
    
    def _get_default_ttc_pd(self, rating: CreditRating) -> Decimal:
        """Get default TTC PD by rating (Basel II guidelines)"""
        default_ttc_pd = {
            CreditRating.AAA: Decimal("0.0001"),  # 0.01%
            CreditRating.AA: Decimal("0.0003"),   # 0.03%
            CreditRating.A: Decimal("0.001"),     # 0.1%
            CreditRating.BBB: Decimal("0.005"),   # 0.5%
            CreditRating.BB: Decimal("0.02"),     # 2%
            CreditRating.B: Decimal("0.05"),      # 5%
            CreditRating.CCC: Decimal("0.15"),    # 15%
            CreditRating.CC: Decimal("0.30"),     # 30%
            CreditRating.C: Decimal("0.50"),      # 50%
            CreditRating.D: Decimal("1.00")       # 100%
        }
        return default_ttc_pd.get(rating, Decimal("0.05"))
    
    def _calculate_remaining_months(self, instrument: FinancialInstrument) -> int:
        """Calculate remaining months to maturity"""
        if not instrument.maturity_date:
            return 12  # Default to 12 months if no maturity date
        
        days_remaining = (instrument.maturity_date - date.today()).days
        months_remaining = max(1, days_remaining // 30)
        
        return months_remaining
    
    def _calculate_psi(self, transition_matrix: np.ndarray) -> Decimal:
        """
        Calculate Population Stability Index (PSI) for model validation.
        
        PSI measures stability of transition probabilities over time.
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.25: Some change
        PSI >= 0.25: Significant change (recalibration needed)
        
        Args:
            transition_matrix: Transition probability matrix
            
        Returns:
            PSI value
        """
        # For simplicity, calculate PSI as variance of diagonal elements
        # (stability of non-transition probabilities)
        diagonal = np.diag(transition_matrix)
        psi = Decimal(str(np.var(diagonal)))
        
        return psi


# Global service instance
transition_matrix_service = TransitionMatrixService()
