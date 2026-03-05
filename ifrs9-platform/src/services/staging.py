"""Staging service for IFRS 9 three-stage impairment model"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
import uuid

from src.db.models import FinancialInstrument, Stage, StageTransition
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class SICRResult:
    """SICR evaluation result"""
    def __init__(self, sicr_detected: bool, indicators: List[str], details: Dict[str, Any]):
        self.sicr_detected = sicr_detected
        self.indicators = indicators
        self.details = details


class StagingResult:
    """Staging determination result"""
    def __init__(self, stage: Stage, previous_stage: Optional[Stage], 
                 sicr_result: Optional[SICRResult], credit_impaired: bool, rationale: str):
        self.stage = stage
        self.previous_stage = previous_stage
        self.sicr_result = sicr_result
        self.credit_impaired = credit_impaired
        self.rationale = rationale


class StagingService:
    """Service for determining impairment stages according to IFRS 9"""
    
    def __init__(self):
        # Configurable SICR thresholds (can be loaded from database)
        self.sicr_pd_relative_threshold = Decimal("1.0")  # 100% relative increase
        self.sicr_pd_absolute_threshold = Decimal("0.02")  # 2% absolute increase
        self.sicr_dpd_threshold = 30  # Days past due threshold
        self.credit_impaired_dpd_threshold = 90  # Credit impaired threshold
    
    def determine_stage(self, instrument: FinancialInstrument, reporting_date: date) -> StagingResult:
        """
        Determine appropriate impairment stage for financial instrument.
        
        Property 3: Stage Assignment Completeness
        For any financial instrument in the system, it must be assigned to exactly one stage 
        (Stage 1, Stage 2, or Stage 3) at any point in time.
        
        Property 4: Initial Recognition Stage
        For any financial instrument at initial recognition, the staging engine must assign it to Stage 1.
        
        Args:
            instrument: Financial instrument
            reporting_date: Reporting date for stage determination
            
        Returns:
            StagingResult with stage, SICR details, and rationale
        """
        logger.info(f"Determining stage for instrument {instrument.instrument_id}")
        
        previous_stage = instrument.current_stage
        
        # Property 4: Initial recognition always Stage 1
        if instrument.origination_date == reporting_date:
            return StagingResult(
                stage=Stage.STAGE_1,
                previous_stage=None,
                sicr_result=None,
                credit_impaired=False,
                rationale="Initial recognition - assigned to Stage 1"
            )
        
        # Check if credit impaired (Stage 3)
        is_credit_impaired = self.check_credit_impaired(instrument)
        
        if is_credit_impaired:
            # Property 6: Credit Impairment Stage Transition
            return StagingResult(
                stage=Stage.STAGE_3,
                previous_stage=previous_stage,
                sicr_result=None,
                credit_impaired=True,
                rationale=f"Credit impaired: DPD={instrument.days_past_due} days"
            )
        
        # Check for SICR (Stage 2)
        sicr_result = self.evaluate_sicr(instrument)
        
        if sicr_result.sicr_detected:
            # Property 5: SICR Stage Transition
            return StagingResult(
                stage=Stage.STAGE_2,
                previous_stage=previous_stage,
                sicr_result=sicr_result,
                credit_impaired=False,
                rationale=f"SICR detected: {', '.join(sicr_result.indicators)}"
            )
        
        # No SICR and not credit impaired
        if previous_stage == Stage.STAGE_2:
            # Property 7: SICR Reversal Stage Transition
            return StagingResult(
                stage=Stage.STAGE_1,
                previous_stage=previous_stage,
                sicr_result=sicr_result,
                credit_impaired=False,
                rationale="SICR no longer present - reverting to Stage 1"
            )
        
        # Remain in or assign to Stage 1
        return StagingResult(
            stage=Stage.STAGE_1,
            previous_stage=previous_stage,
            sicr_result=sicr_result,
            credit_impaired=False,
            rationale="No SICR detected - Stage 1"
        )
    
    def evaluate_sicr(self, instrument: FinancialInstrument) -> SICRResult:
        """
        Evaluate Significant Increase in Credit Risk (SICR).
        
        Property 8: Days Past Due SICR Threshold
        For any financial instrument with days past due exceeding 30 days, 
        the staging engine must identify a SICR.
        
        Args:
            instrument: Financial instrument
            
        Returns:
            SICRResult with detection status and indicators
        """
        indicators = []
        details = {}
        
        # Quantitative indicator 1: Days past due > 30 (backstop)
        # Property 8: DPD > 30 days triggers SICR
        if instrument.days_past_due > self.sicr_dpd_threshold:
            indicators.append("DPD_THRESHOLD")
            details["days_past_due"] = instrument.days_past_due
            details["dpd_threshold"] = self.sicr_dpd_threshold
        
        # Quantitative indicator 2: PD increase
        if instrument.initial_recognition_pd:
            # Assume current PD is stored or calculated (for MVP, we'll use a placeholder)
            # In production, this would fetch current PD from parameter service
            current_pd = instrument.initial_recognition_pd * Decimal("1.5")  # Placeholder
            
            # Relative increase check
            if current_pd > instrument.initial_recognition_pd * (1 + self.sicr_pd_relative_threshold):
                indicators.append("PD_RELATIVE_INCREASE")
                details["pd_at_origination"] = float(instrument.initial_recognition_pd)
                details["current_pd"] = float(current_pd)
                details["relative_increase"] = float(
                    (current_pd - instrument.initial_recognition_pd) / instrument.initial_recognition_pd
                )
            
            # Absolute increase check
            if current_pd - instrument.initial_recognition_pd > self.sicr_pd_absolute_threshold:
                indicators.append("PD_ABSOLUTE_INCREASE")
                details["absolute_increase"] = float(current_pd - instrument.initial_recognition_pd)
        
        # Qualitative indicators - Phase 1 enhancements
        # Check watchlist status
        if hasattr(instrument, 'watchlist_status') and instrument.watchlist_status:
            indicators.append("WATCHLIST")
            details["watchlist_status"] = instrument.watchlist_status
        
        # Check restructuring flag
        if hasattr(instrument, 'is_restructured') and instrument.is_restructured:
            indicators.append("RESTRUCTURED")
            if hasattr(instrument, 'restructuring_date') and instrument.restructuring_date:
                details["restructuring_date"] = str(instrument.restructuring_date)
        
        # Check forbearance
        if hasattr(instrument, 'forbearance_granted') and instrument.forbearance_granted:
            indicators.append("FORBEARANCE")
            if hasattr(instrument, 'forbearance_date') and instrument.forbearance_date:
                details["forbearance_date"] = str(instrument.forbearance_date)
        
        # Check sector risk rating downgrade (requires customer relationship)
        if hasattr(instrument, 'customer') and instrument.customer:
            if hasattr(instrument.customer, 'sector_risk_rating') and instrument.customer.sector_risk_rating:
                # Assume rating scale: AAA, AA, A, BBB, BB, B, CCC, CC, C
                # Downgrade from investment grade (BBB+) to sub-investment grade triggers SICR
                risky_ratings = ['BB', 'B', 'CCC', 'CC', 'C', 'D']
                if instrument.customer.sector_risk_rating in risky_ratings:
                    indicators.append("SECTOR_DOWNGRADE")
                    details["sector_risk_rating"] = instrument.customer.sector_risk_rating
        
        # Legacy check for is_modified (backward compatibility)
        if instrument.is_modified and "FORBEARANCE" not in indicators:
            indicators.append("FORBEARANCE")
            details["modification_date"] = str(instrument.modification_date)
        
        sicr_detected = len(indicators) > 0
        
        return SICRResult(
            sicr_detected=sicr_detected,
            indicators=indicators,
            details=details
        )
    
    def check_credit_impaired(self, instrument: FinancialInstrument) -> bool:
        """
        Check if instrument is credit impaired (Stage 3).
        
        Property 9: Days Past Due Credit Impairment Threshold
        For any financial instrument with days past due exceeding 90 days, 
        the staging engine must classify it as credit-impaired.
        
        Args:
            instrument: Financial instrument
            
        Returns:
            True if credit impaired, False otherwise
        """
        # Property 9: DPD > 90 days triggers credit impairment
        if instrument.days_past_due > self.credit_impaired_dpd_threshold:
            return True
        
        # Other objective evidence of impairment (simplified for MVP)
        # In production, would check for:
        # - Borrower bankruptcy
        # - Debt restructuring under distress
        # - Disappearance of active market
        
        return False
    
    def get_stage_transitions(self, instrument_id: str, start_date: date, 
                            end_date: date) -> List[StageTransition]:
        """
        Get stage transition history for instrument.
        
        Args:
            instrument_id: Instrument ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of stage transitions
        """
        # TODO: Implement database query
        logger.info(f"Fetching stage transitions for {instrument_id}")
        return []
    
    def apply_staging_rules(self, instruments: List[FinancialInstrument], 
                          reporting_date: date) -> Dict[str, StagingResult]:
        """
        Apply staging rules to portfolio of instruments.
        
        Args:
            instruments: List of financial instruments
            reporting_date: Reporting date
            
        Returns:
            Dict mapping instrument_id to StagingResult
        """
        results = {}
        for instrument in instruments:
            result = self.determine_stage(instrument, reporting_date)
            results[instrument.instrument_id] = result
        
        logger.info(f"Staged {len(instruments)} instruments")
        return results


# Global service instance
staging_service = StagingService()
