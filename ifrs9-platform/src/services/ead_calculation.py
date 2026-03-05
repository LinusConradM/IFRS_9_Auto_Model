"""EAD (Exposure at Default) calculation service for on-balance and off-balance sheet exposures"""
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from src.db.models import FinancialInstrument, CCFConfig, FacilityType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EADResult:
    """EAD calculation result"""
    def __init__(
        self,
        ead_amount: Decimal,
        drawn_amount: Decimal,
        undrawn_amount: Decimal,
        ccf: Decimal,
        facility_type: str,
        is_off_balance_sheet: bool,
        calculation_details: Dict[str, Any]
    ):
        self.ead_amount = ead_amount
        self.drawn_amount = drawn_amount
        self.undrawn_amount = undrawn_amount
        self.ccf = ccf
        self.facility_type = facility_type
        self.is_off_balance_sheet = is_off_balance_sheet
        self.calculation_details = calculation_details


class EADCalculationService:
    """Service for calculating Exposure at Default (EAD)"""
    
    # Default CCF values by facility type (Basel III guidelines)
    DEFAULT_CCF = {
        FacilityType.TERM_LOAN: Decimal("1.00"),  # Fully drawn
        FacilityType.REVOLVING_CREDIT: Decimal("0.75"),  # 75% CCF
        FacilityType.OVERDRAFT: Decimal("0.75"),  # 75% CCF
        FacilityType.CREDIT_CARD: Decimal("0.75"),  # 75% CCF
        FacilityType.LETTER_OF_CREDIT: Decimal("0.20"),  # 20% CCF
        FacilityType.GUARANTEE: Decimal("0.50"),  # 50% CCF
        FacilityType.COMMITMENT: Decimal("0.75"),  # 75% CCF
        FacilityType.OTHER: Decimal("1.00")  # Conservative default
    }
    
    def calculate_ead(
        self,
        db: Session,
        instrument: FinancialInstrument,
        reporting_date: date
    ) -> EADResult:
        """
        Calculate Exposure at Default (EAD) for financial instrument.
        
        For on-balance sheet: EAD = Drawn Balance
        For off-balance sheet: EAD = Drawn + (Undrawn × CCF)
        
        Args:
            db: Database session
            instrument: Financial instrument
            reporting_date: Reporting date
            
        Returns:
            EADResult with calculated EAD and details
        """
        logger.info(f"Calculating EAD for instrument {instrument.instrument_id}")
        
        # Get drawn and undrawn amounts
        drawn_amount = instrument.outstanding_balance or Decimal("0")
        undrawn_amount = instrument.undrawn_commitment_amount or Decimal("0")
        
        # Determine if off-balance sheet
        is_off_balance_sheet = instrument.is_off_balance_sheet or False
        
        if not is_off_balance_sheet:
            # On-balance sheet: EAD = Drawn Balance
            ead_amount = drawn_amount
            ccf = Decimal("1.00")
            
            calculation_details = {
                "calculation_type": "on_balance_sheet",
                "formula": "EAD = Drawn Balance",
                "drawn_balance": float(drawn_amount)
            }
        else:
            # Off-balance sheet: EAD = Drawn + (Undrawn × CCF)
            ccf = self._get_ccf(db, instrument)
            ead_amount = drawn_amount + (undrawn_amount * ccf)
            
            calculation_details = {
                "calculation_type": "off_balance_sheet",
                "formula": "EAD = Drawn + (Undrawn × CCF)",
                "drawn_balance": float(drawn_amount),
                "undrawn_commitment": float(undrawn_amount),
                "ccf": float(ccf),
                "ccf_component": float(undrawn_amount * ccf)
            }
        
        facility_type = instrument.facility_type.value if instrument.facility_type else "UNKNOWN"
        
        logger.info(f"EAD calculated: {ead_amount} for instrument {instrument.instrument_id}")
        
        return EADResult(
            ead_amount=ead_amount,
            drawn_amount=drawn_amount,
            undrawn_amount=undrawn_amount,
            ccf=ccf,
            facility_type=facility_type,
            is_off_balance_sheet=is_off_balance_sheet,
            calculation_details=calculation_details
        )
    
    def _get_ccf(
        self,
        db: Session,
        instrument: FinancialInstrument
    ) -> Decimal:
        """
        Get Credit Conversion Factor (CCF) for instrument.
        
        Priority:
        1. Instrument-specific CCF (if set)
        2. Facility-type-specific CCF from config table
        3. Default CCF by facility type
        
        Args:
            db: Database session
            instrument: Financial instrument
            
        Returns:
            CCF as Decimal
        """
        # Check instrument-specific CCF
        if instrument.credit_conversion_factor is not None:
            return instrument.credit_conversion_factor
        
        # Check facility-type-specific CCF from config
        if instrument.facility_type:
            ccf_config = db.query(CCFConfig).filter(
                CCFConfig.facility_type == instrument.facility_type,
                CCFConfig.is_active == True
            ).first()
            
            if ccf_config:
                return ccf_config.ccf_value
        
        # Use default CCF
        facility_type = instrument.facility_type or FacilityType.OTHER
        return self.DEFAULT_CCF.get(facility_type, Decimal("1.00"))
    
    def calibrate_ccf(
        self,
        db: Session,
        facility_type: FacilityType,
        historical_drawdown_data: Dict[str, Any]
    ) -> Decimal:
        """
        Calibrate CCF from internal drawdown data.
        
        CCF = Average(Drawn at Default / Limit) for defaulted facilities
        
        Args:
            db: Database session
            facility_type: Facility type
            historical_drawdown_data: Historical drawdown data
            
        Returns:
            Calibrated CCF
        """
        logger.info(f"Calibrating CCF for facility type {facility_type}")
        
        # Extract drawdown ratios from historical data
        drawdown_ratios = historical_drawdown_data.get("drawdown_ratios", [])
        
        if not drawdown_ratios:
            logger.warning(f"No historical data for {facility_type}, using default CCF")
            return self.DEFAULT_CCF.get(facility_type, Decimal("1.00"))
        
        # Calculate average drawdown ratio
        total_ratio = sum(Decimal(str(ratio)) for ratio in drawdown_ratios)
        avg_ratio = total_ratio / len(drawdown_ratios)
        
        # Cap CCF at 1.0 (100%)
        calibrated_ccf = min(avg_ratio, Decimal("1.00"))
        
        logger.info(f"Calibrated CCF for {facility_type}: {calibrated_ccf}")
        
        return calibrated_ccf
    
    def update_ccf_config(
        self,
        db: Session,
        facility_type: FacilityType,
        ccf_value: Decimal,
        effective_date: date,
        updated_by: str
    ) -> CCFConfig:
        """
        Update CCF configuration for facility type.
        
        Args:
            db: Database session
            facility_type: Facility type
            ccf_value: New CCF value
            effective_date: Effective date
            updated_by: User ID
            
        Returns:
            CCFConfig record
        """
        logger.info(f"Updating CCF config for {facility_type}")
        
        # Deactivate existing config
        existing_configs = db.query(CCFConfig).filter(
            CCFConfig.facility_type == facility_type,
            CCFConfig.is_active == True
        ).all()
        
        for config in existing_configs:
            config.is_active = False
        
        # Create new config
        new_config = CCFConfig(
            facility_type=facility_type,
            ccf_value=ccf_value,
            effective_date=effective_date,
            updated_by=updated_by,
            is_active=True
        )
        
        db.add(new_config)
        db.commit()
        
        logger.info(f"CCF config updated for {facility_type}: {ccf_value}")
        
        return new_config
    
    def model_dynamic_drawdown(
        self,
        instrument: FinancialInstrument,
        stress_scenario: str = "base"
    ) -> Decimal:
        """
        Model dynamic drawdown for revolving facilities under stress.
        
        Args:
            instrument: Financial instrument
            stress_scenario: Stress scenario (base, adverse, severe)
            
        Returns:
            Projected drawdown amount
        """
        logger.info(f"Modeling dynamic drawdown for {instrument.instrument_id}")
        
        # Get current utilization
        drawn = instrument.outstanding_balance or Decimal("0")
        limit = (instrument.outstanding_balance or Decimal("0")) + (instrument.undrawn_commitment_amount or Decimal("0"))
        
        if limit == 0:
            return Decimal("0")
        
        current_utilization = drawn / limit
        
        # Stress factors by scenario
        stress_factors = {
            "base": Decimal("1.0"),  # No stress
            "adverse": Decimal("1.2"),  # 20% increase in utilization
            "severe": Decimal("1.5")  # 50% increase in utilization
        }
        
        stress_factor = stress_factors.get(stress_scenario, Decimal("1.0"))
        
        # Project stressed utilization (capped at 100%)
        stressed_utilization = min(current_utilization * stress_factor, Decimal("1.0"))
        projected_drawn = limit * stressed_utilization
        
        logger.info(f"Projected drawdown: {projected_drawn} (scenario: {stress_scenario})")
        
        return projected_drawn


# Global service instance
ead_calculation_service = EADCalculationService()
