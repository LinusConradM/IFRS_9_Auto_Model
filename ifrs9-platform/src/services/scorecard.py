"""Scorecard service for behavioral scoring and PD mapping"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

from src.db.models import BehavioralScorecard, CustomerScore, FinancialInstrument, ProductType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ScorecardPerformance:
    """Scorecard performance metrics"""
    def __init__(
        self,
        gini_coefficient: Decimal,
        ks_statistic: Decimal,
        auc_roc: Decimal,
        num_observations: int
    ):
        self.gini_coefficient = gini_coefficient
        self.ks_statistic = ks_statistic
        self.auc_roc = auc_roc
        self.num_observations = num_observations


class PDMapping:
    """Score-to-PD mapping result"""
    def __init__(
        self,
        score: int,
        pd_band: str,
        pd_value: Decimal,
        score_range: Tuple[int, int]
    ):
        self.score = score
        self.pd_band = pd_band
        self.pd_value = pd_value
        self.score_range = score_range


class ScorecardService:
    """Service for behavioral scorecard management and PD estimation"""
    
    # Default PD bands (can be customized)
    PD_BANDS = [
        ("Excellent", (800, 850), Decimal("0.005")),   # 0.5%
        ("Very Good", (740, 799), Decimal("0.01")),    # 1%
        ("Good", (670, 739), Decimal("0.02")),         # 2%
        ("Fair", (580, 669), Decimal("0.05")),         # 5%
        ("Poor", (500, 579), Decimal("0.10")),         # 10%
        ("Very Poor", (300, 499), Decimal("0.20"))     # 20%
    ]
    
    def map_score_to_pd(
        self,
        db: Session,
        score: int,
        product_type: ProductType
    ) -> PDMapping:
        """
        Map behavioral score to PD.
        
        Args:
            db: Database session
            score: Behavioral score (typically 300-850)
            product_type: Product type
            
        Returns:
            PDMapping with PD band and value
        """
        logger.info(f"Mapping score {score} to PD for product {product_type}")
        
        # Fetch scorecard configuration
        scorecard = db.query(BehavioralScorecard).filter(
            BehavioralScorecard.product_type == product_type,
            BehavioralScorecard.is_active == True
        ).first()
        
        if not scorecard:
            logger.warning(f"No scorecard found for {product_type}, using default mapping")
            return self._default_score_to_pd(score)
        
        # Find PD band for score
        score_bands = scorecard.score_bands
        
        for band_name, (min_score, max_score), pd_value in score_bands:
            if min_score <= score <= max_score:
                return PDMapping(
                    score=score,
                    pd_band=band_name,
                    pd_value=Decimal(str(pd_value)),
                    score_range=(min_score, max_score)
                )
        
        # Score outside defined bands, use default
        logger.warning(f"Score {score} outside defined bands, using default")
        return self._default_score_to_pd(score)
    
    def _default_score_to_pd(self, score: int) -> PDMapping:
        """Default score-to-PD mapping"""
        for band_name, (min_score, max_score), pd_value in self.PD_BANDS:
            if min_score <= score <= max_score:
                return PDMapping(
                    score=score,
                    pd_band=band_name,
                    pd_value=pd_value,
                    score_range=(min_score, max_score)
                )
        
        # Score below minimum, assign highest PD
        if score < 300:
            return PDMapping(
                score=score,
                pd_band="Very Poor",
                pd_value=Decimal("0.30"),
                score_range=(0, 299)
            )
        
        # Score above maximum, assign lowest PD
        return PDMapping(
            score=score,
            pd_band="Excellent",
            pd_value=Decimal("0.005"),
            score_range=(850, 999)
        )
    
    def calculate_gini_coefficient(
        self,
        db: Session,
        product_type: ProductType,
        validation_data: List[Dict[str, Any]]
    ) -> Decimal:
        """
        Calculate Gini coefficient for scorecard validation.
        
        Gini = 2 × AUC - 1
        
        Interpretation:
        - Gini > 0.4: Excellent discrimination
        - 0.3 < Gini <= 0.4: Good discrimination
        - 0.2 < Gini <= 0.3: Acceptable discrimination
        - Gini <= 0.2: Poor discrimination
        
        Args:
            db: Database session
            product_type: Product type
            validation_data: List of {score, actual_default} records
            
        Returns:
            Gini coefficient
        """
        logger.info(f"Calculating Gini coefficient for {product_type}")
        
        if not validation_data:
            raise ValueError("No validation data provided")
        
        # Extract scores and actual defaults
        scores = [record["score"] for record in validation_data]
        actuals = [record["actual_default"] for record in validation_data]
        
        # Calculate AUC-ROC
        auc = roc_auc_score(actuals, scores)
        
        # Calculate Gini
        gini = Decimal(str(2 * auc - 1))
        
        logger.info(f"Gini coefficient: {gini}")
        
        return gini
    
    def calculate_ks_statistic(
        self,
        db: Session,
        product_type: ProductType,
        validation_data: List[Dict[str, Any]]
    ) -> Decimal:
        """
        Calculate Kolmogorov-Smirnov (KS) statistic for scorecard validation.
        
        KS = max(|CDF_good - CDF_bad|)
        
        Interpretation:
        - KS > 0.4: Excellent discrimination
        - 0.3 < KS <= 0.4: Good discrimination
        - 0.2 < KS <= 0.3: Acceptable discrimination
        - KS <= 0.2: Poor discrimination
        
        Args:
            db: Database session
            product_type: Product type
            validation_data: List of {score, actual_default} records
            
        Returns:
            KS statistic
        """
        logger.info(f"Calculating KS statistic for {product_type}")
        
        if not validation_data:
            raise ValueError("No validation data provided")
        
        # Extract scores and actual defaults
        scores = np.array([record["score"] for record in validation_data])
        actuals = np.array([record["actual_default"] for record in validation_data])
        
        # Separate good and bad scores
        good_scores = scores[actuals == 0]
        bad_scores = scores[actuals == 1]
        
        # Calculate CDFs
        good_cdf = np.sort(good_scores)
        bad_cdf = np.sort(bad_scores)
        
        # Calculate KS statistic (maximum separation between CDFs)
        # Using ROC curve as proxy
        fpr, tpr, _ = roc_curve(actuals, scores)
        ks = Decimal(str(np.max(tpr - fpr)))
        
        logger.info(f"KS statistic: {ks}")
        
        return ks
    
    def recalibrate_scorecard(
        self,
        db: Session,
        product_type: ProductType,
        actual_defaults: List[Dict[str, Any]]
    ) -> BehavioralScorecard:
        """
        Recalibrate scorecard based on actual default experience.
        
        Args:
            db: Database session
            product_type: Product type
            actual_defaults: Historical default data with scores
            
        Returns:
            Updated BehavioralScorecard
        """
        logger.info(f"Recalibrating scorecard for {product_type}")
        
        # Fetch current scorecard
        scorecard = db.query(BehavioralScorecard).filter(
            BehavioralScorecard.product_type == product_type,
            BehavioralScorecard.is_active == True
        ).first()
        
        if not scorecard:
            raise ValueError(f"No scorecard found for {product_type}")
        
        # Calculate actual default rates by score band
        recalibrated_bands = []
        
        for band_name, (min_score, max_score), old_pd in scorecard.score_bands:
            # Filter defaults in this score band
            band_defaults = [
                d for d in actual_defaults 
                if min_score <= d["score"] <= max_score
            ]
            
            if band_defaults:
                # Calculate actual default rate
                total_count = len(band_defaults)
                default_count = sum(1 for d in band_defaults if d["actual_default"] == 1)
                actual_pd = Decimal(str(default_count / total_count))
                
                # Apply smoothing (blend 70% actual, 30% old PD)
                recalibrated_pd = (Decimal("0.7") * actual_pd) + (Decimal("0.3") * Decimal(str(old_pd)))
            else:
                # No data for this band, keep old PD
                recalibrated_pd = Decimal(str(old_pd))
            
            recalibrated_bands.append((band_name, (min_score, max_score), float(recalibrated_pd)))
        
        # Update scorecard
        scorecard.score_bands = recalibrated_bands
        scorecard.last_calibration_date = date.today()
        
        db.commit()
        
        logger.info(f"Scorecard recalibrated for {product_type}")
        
        return scorecard
    
    def generate_performance_report(
        self,
        db: Session,
        product_type: ProductType,
        validation_data: List[Dict[str, Any]]
    ) -> ScorecardPerformance:
        """
        Generate scorecard performance report.
        
        Args:
            db: Database session
            product_type: Product type
            validation_data: Validation data
            
        Returns:
            ScorecardPerformance with metrics
        """
        logger.info(f"Generating performance report for {product_type}")
        
        # Calculate metrics
        gini = self.calculate_gini_coefficient(db, product_type, validation_data)
        ks = self.calculate_ks_statistic(db, product_type, validation_data)
        
        # Calculate AUC-ROC
        scores = [record["score"] for record in validation_data]
        actuals = [record["actual_default"] for record in validation_data]
        auc = Decimal(str(roc_auc_score(actuals, scores)))
        
        performance = ScorecardPerformance(
            gini_coefficient=gini,
            ks_statistic=ks,
            auc_roc=auc,
            num_observations=len(validation_data)
        )
        
        logger.info(f"Performance report: Gini={gini}, KS={ks}, AUC={auc}")
        
        return performance
    
    def update_customer_score(
        self,
        db: Session,
        customer_id: str,
        score: int,
        score_date: date,
        score_source: str = "internal"
    ) -> CustomerScore:
        """
        Update customer behavioral score.
        
        Args:
            db: Database session
            customer_id: Customer ID
            score: Behavioral score
            score_date: Score date
            score_source: Score source (internal, bureau, etc.)
            
        Returns:
            CustomerScore record
        """
        logger.info(f"Updating score for customer {customer_id}")
        
        # Create new score record
        customer_score = CustomerScore(
            customer_id=customer_id,
            score=score,
            score_date=score_date,
            score_source=score_source
        )
        
        db.add(customer_score)
        db.commit()
        
        logger.info(f"Customer score updated: {score}")
        
        return customer_score
    
    def get_customer_latest_score(
        self,
        db: Session,
        customer_id: str
    ) -> Optional[CustomerScore]:
        """
        Get customer's latest behavioral score.
        
        Args:
            db: Database session
            customer_id: Customer ID
            
        Returns:
            Latest CustomerScore or None
        """
        score = db.query(CustomerScore).filter(
            CustomerScore.customer_id == customer_id
        ).order_by(CustomerScore.score_date.desc()).first()
        
        return score


# Global service instance
scorecard_service = ScorecardService()
