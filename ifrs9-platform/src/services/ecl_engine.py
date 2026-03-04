"""ECL calculation engine for IFRS 9"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
import uuid
from dateutil.relativedelta import relativedelta

from src.db.models import FinancialInstrument, Stage, ECLCalculation
from src.utils.logging_config import get_logger
from src.utils.cache import get_cache, set_cache

logger = get_logger(__name__)


class ECLResult:
    """ECL calculation result"""
    def __init__(self, calculation_id: str, ecl_amount: Decimal, pd: Decimal, 
                 lgd: Decimal, ead: Decimal, time_horizon: str, 
                 scenario_results: Optional[Dict[str, Decimal]] = None):
        self.calculation_id = calculation_id
        self.ecl_amount = ecl_amount
        self.pd = pd
        self.lgd = lgd
        self.ead = ead
        self.time_horizon = time_horizon
        self.scenario_results = scenario_results or {}


class ECLCalculationService:
    """Service for calculating Expected Credit Loss"""
    
    def __init__(self):
        # Default parameters (in production, these would be loaded from database)
        self.default_pd = Decimal("0.02")  # 2%
        self.default_lgd = Decimal("0.45")  # 45%
        self.default_discount_rate = Decimal("0.12")  # 12%
    
    def calculate_ecl(self, instrument: FinancialInstrument, stage: Stage, 
                     reporting_date: date, scenarios: Optional[List[Dict]] = None) -> ECLResult:
        """
        Calculate ECL for financial instrument.
        
        Property 10: Stage-ECL Type Consistency
        For any financial instrument, if it is in Stage 1, then 12-month ECL must be calculated; 
        if it is in Stage 2 or Stage 3, then Lifetime ECL must be calculated.
        
        Property 11: ECL Calculation Formula
        For any ECL calculation, the ECL amount must be computed using the formula: 
        ECL = Σ(PD_t × LGD_t × EAD_t × DF_t) where the sum is over the appropriate time horizon.
        
        Args:
            instrument: Financial instrument
            stage: Impairment stage
            reporting_date: Reporting date
            scenarios: Optional list of macroeconomic scenarios
            
        Returns:
            ECLResult with calculation details
        """
        logger.info(f"Calculating ECL for instrument {instrument.instrument_id}, stage {stage}")
        
        calculation_id = str(uuid.uuid4())
        
        # Property 10: Stage determines ECL type
        if stage == Stage.STAGE_1:
            ecl_amount = self.calculate_12m_ecl(instrument, reporting_date)
            time_horizon = "12_MONTH"
        else:  # Stage 2 or Stage 3
            ecl_amount = self.calculate_lifetime_ecl(instrument, reporting_date)
            time_horizon = "LIFETIME"
        
        # Get parameters
        pd = self._get_pd(instrument)
        lgd = self._get_lgd(instrument)
        ead = self._get_ead(instrument)
        
        # Apply scenario weighting if scenarios provided
        scenario_results = {}
        if scenarios:
            # Property 12: Scenario Weighting
            ecl_amount = self._apply_scenario_weighting(
                instrument, stage, reporting_date, scenarios, scenario_results
            )
        
        logger.info(f"ECL calculated: {ecl_amount} for instrument {instrument.instrument_id}")
        
        return ECLResult(
            calculation_id=calculation_id,
            ecl_amount=ecl_amount,
            pd=pd,
            lgd=lgd,
            ead=ead,
            time_horizon=time_horizon,
            scenario_results=scenario_results
        )
    
    def calculate_12m_ecl(self, instrument: FinancialInstrument, reporting_date: date) -> Decimal:
        """
        Calculate 12-month ECL for Stage 1 instruments.
        
        Property 11: ECL = Σ(PD_t × LGD_t × EAD_t × DF_t) for 12 months
        
        Args:
            instrument: Financial instrument
            reporting_date: Reporting date
            
        Returns:
            12-month ECL amount
        """
        pd = self._get_pd(instrument)
        lgd = self._get_lgd(instrument)
        ead = self._get_ead(instrument)
        discount_rate = self.default_discount_rate
        
        # Calculate ECL for 12 months
        # Simplified: ECL = PD × LGD × EAD × DF
        # In production, this would sum over monthly periods
        discount_factor = Decimal("1") / (Decimal("1") + discount_rate)
        
        ecl = pd * lgd * ead * discount_factor
        
        return ecl.quantize(Decimal("0.01"))
    
    def calculate_lifetime_ecl(self, instrument: FinancialInstrument, reporting_date: date) -> Decimal:
        """
        Calculate Lifetime ECL for Stage 2 and Stage 3 instruments.
        
        Property 11: ECL = Σ(PD_t × LGD_t × EAD_t × DF_t) for lifetime
        
        Args:
            instrument: Financial instrument
            reporting_date: Reporting date
            
        Returns:
            Lifetime ECL amount
        """
        pd = self._get_pd(instrument)
        lgd = self._get_lgd(instrument)
        ead = self._get_ead(instrument)
        discount_rate = self.default_discount_rate
        
        # Calculate remaining term in years
        remaining_term = (instrument.maturity_date - reporting_date).days / 365.0
        remaining_term = max(remaining_term, 0.1)  # Minimum 0.1 years
        
        # Calculate lifetime ECL (simplified)
        # In production, this would sum over all periods until maturity
        total_ecl = Decimal("0")
        for year in range(int(remaining_term) + 1):
            discount_factor = Decimal("1") / ((Decimal("1") + discount_rate) ** year)
            period_ecl = pd * lgd * ead * discount_factor
            total_ecl += period_ecl
        
        return total_ecl.quantize(Decimal("0.01"))
    
    def _get_pd(self, instrument: FinancialInstrument) -> Decimal:
        """
        Get Probability of Default for instrument.
        
        In production, this would:
        1. Check cache
        2. Query parameter_sets table with segmentation
        3. Apply macroeconomic adjustments
        
        Args:
            instrument: Financial instrument
            
        Returns:
            PD value
        """
    
    def _get_pd(self, instrument: FinancialInstrument) -> Decimal:
        """
        Get Probability of Default for instrument.
        
        For MVP, uses default PD values.
        In production, this would query parameter_sets table.
        
        Args:
            instrument: Financial instrument
            
        Returns:
            PD value
        """
        # For MVP, use default PD
        # In production, would query parameter_sets by customer_segment and stage
        return self.default_pd
    
    def _get_lgd(self, instrument: FinancialInstrument) -> Decimal:
        """
        Get Loss Given Default for instrument.
        
        For MVP, uses default LGD values.
        In production, this would query parameter_sets table.
        
        Args:
            instrument: Financial instrument
            
        Returns:
            LGD value
        """
        # For MVP, use default LGD
        # In production, would query parameter_sets by customer_segment
        # and adjust for collateral (Property 26)
        return self.default_lgd
    
    def _get_ead(self, instrument: FinancialInstrument) -> Decimal:
        """
        Get Exposure at Default for instrument.
        
        Args:
            instrument: Financial instrument
            
        Returns:
            EAD value
        """
        # For MVP, EAD = current principal amount
        # In production, would consider:
        # - Undrawn commitments
        # - Exposure profiles
        # - Credit conversion factors
        
        return instrument.principal_amount
    
    def _apply_scenario_weighting(self, instrument: FinancialInstrument, stage: Stage,
                                  reporting_date: date, scenarios: List[Dict],
                                  scenario_results: Dict) -> Decimal:
        """
        Apply macroeconomic scenario weighting.
        
        Property 12: Scenario Weighting
        For any probability-weighted ECL calculation with multiple scenarios, 
        the weighted ECL must equal the sum of (scenario_weight * scenario_ECL) for all scenarios, 
        and the sum of all scenario weights must equal 1.0.
        
        Args:
            instrument: Financial instrument
            stage: Impairment stage
            reporting_date: Reporting date
            scenarios: List of scenarios with weights
            scenario_results: Dict to store individual scenario results
            
        Returns:
            Probability-weighted ECL
        """
        total_weight = Decimal("0")
        weighted_ecl = Decimal("0")
        
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id", "unknown")
            weight = Decimal(str(scenario.get("weight", 0)))
            total_weight += weight
            
            # Calculate ECL under this scenario
            # In production, would adjust PD/LGD based on macro indicators
            if stage == Stage.STAGE_1:
                scenario_ecl = self.calculate_12m_ecl(instrument, reporting_date)
            else:
                scenario_ecl = self.calculate_lifetime_ecl(instrument, reporting_date)
            
            # Apply scenario adjustment (simplified for MVP)
            adjustment = Decimal(str(scenario.get("adjustment", 1.0)))
            scenario_ecl = scenario_ecl * adjustment
            
            scenario_results[scenario_id] = scenario_ecl
            weighted_ecl += weight * scenario_ecl
        
        # Property 12: Validate weights sum to 1.0
        if abs(total_weight - Decimal("1.0")) > Decimal("0.001"):
            logger.warning(f"Scenario weights sum to {total_weight}, not 1.0")
        
        return weighted_ecl.quantize(Decimal("0.01"))
    
    def recalculate_portfolio(self, instruments: List[FinancialInstrument], 
                            reporting_date: date) -> Dict[str, ECLResult]:
        """
        Calculate ECL for portfolio of instruments.
        
        Args:
            instruments: List of financial instruments
            reporting_date: Reporting date
            
        Returns:
            Dict mapping instrument_id to ECLResult
        """
        results = {}
        for instrument in instruments:
            result = self.calculate_ecl(instrument, instrument.current_stage, reporting_date)
            results[instrument.instrument_id] = result
        
        logger.info(f"Calculated ECL for {len(instruments)} instruments")
        return results


# Global service instance
ecl_engine = ECLCalculationService()
