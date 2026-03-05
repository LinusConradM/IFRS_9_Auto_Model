"""Facility-level LGD calculation service with collateral haircuts and recovery rates"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db.models import (
    FinancialInstrument, Collateral, CollateralType, CollateralHaircutConfig,
    WorkoutRecovery, Stage
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class LGDResult:
    """LGD calculation result"""
    def __init__(
        self,
        lgd: Decimal,
        ead: Decimal,
        collateral_nrv: Decimal,
        unsecured_exposure: Decimal,
        base_lgd: Decimal,
        cure_rate: Decimal,
        recovery_rate: Decimal,
        time_to_recovery_months: int,
        discount_factor: Decimal,
        calculation_details: Dict[str, Any]
    ):
        self.lgd = lgd
        self.ead = ead
        self.collateral_nrv = collateral_nrv
        self.unsecured_exposure = unsecured_exposure
        self.base_lgd = base_lgd
        self.cure_rate = cure_rate
        self.recovery_rate = recovery_rate
        self.time_to_recovery_months = time_to_recovery_months
        self.discount_factor = discount_factor
        self.calculation_details = calculation_details


class FacilityLGDService:
    """Service for calculating facility-level Loss Given Default (LGD)"""
    
    # Default LGD values by collateral type (Basel III guidelines)
    DEFAULT_BASE_LGD = {
        "SECURED": Decimal("0.25"),  # 25% for secured
        "UNSECURED": Decimal("0.45"),  # 45% for unsecured
        "SUBORDINATED": Decimal("0.75")  # 75% for subordinated
    }
    
    # Default cure rates by stage
    DEFAULT_CURE_RATES = {
        Stage.STAGE_1: Decimal("0.00"),  # No cure rate for Stage 1
        Stage.STAGE_2: Decimal("0.30"),  # 30% cure rate for Stage 2
        Stage.STAGE_3: Decimal("0.10")  # 10% cure rate for Stage 3
    }
    
    def calculate_facility_lgd(
        self,
        db: Session,
        instrument: FinancialInstrument,
        ead: Decimal,
        reporting_date: date
    ) -> LGDResult:
        """
        Calculate facility-level LGD incorporating collateral and recovery rates.
        
        Formula:
        1. Calculate collateral Net Realizable Value (NRV) with haircuts
        2. Unsecured Exposure = max(0, EAD - Collateral NRV)
        3. Base LGD = Recovery rate from historical workout data
        4. Cure Rate adjustment for Stage 2
        5. Time-to-recovery discounting
        6. Final LGD = (Unsecured Exposure / EAD) × Base LGD × (1 - Cure Rate) × Discount Factor
        
        Args:
            db: Database session
            instrument: Financial instrument
            ead: Exposure at Default
            reporting_date: Reporting date
            
        Returns:
            LGDResult with calculated LGD and components
        """
        logger.info(f"Calculating facility LGD for instrument {instrument.instrument_id}")
        
        # Step 1: Calculate collateral NRV
        collateral_nrv = self._calculate_collateral_nrv(db, instrument, reporting_date)
        
        # Step 2: Calculate unsecured exposure
        unsecured_exposure = max(Decimal("0"), ead - collateral_nrv)
        
        # Step 3: Get base LGD from historical recovery rates
        base_lgd = self._get_base_lgd(db, instrument)
        
        # Step 4: Get cure rate (for Stage 2 only)
        cure_rate = self._get_cure_rate(instrument)
        
        # Step 5: Calculate time-to-recovery and discount factor
        time_to_recovery_months = self._estimate_time_to_recovery(instrument)
        discount_factor = self._calculate_discount_factor(
            instrument.effective_interest_rate or Decimal("0.10"),
            time_to_recovery_months
        )
        
        # Step 6: Calculate final LGD
        if ead > 0:
            lgd = (unsecured_exposure / ead) * base_lgd * (Decimal("1") - cure_rate) * discount_factor
        else:
            lgd = Decimal("0")
        
        # Cap LGD at 100%
        lgd = min(lgd, Decimal("1.00"))
        
        recovery_rate = Decimal("1") - base_lgd
        
        calculation_details = {
            "formula": "LGD = (Unsecured / EAD) × Base LGD × (1 - Cure Rate) × Discount Factor",
            "ead": float(ead),
            "collateral_nrv": float(collateral_nrv),
            "unsecured_exposure": float(unsecured_exposure),
            "base_lgd": float(base_lgd),
            "cure_rate": float(cure_rate),
            "time_to_recovery_months": time_to_recovery_months,
            "discount_factor": float(discount_factor),
            "final_lgd": float(lgd)
        }
        
        logger.info(f"LGD calculated: {lgd} for instrument {instrument.instrument_id}")
        
        return LGDResult(
            lgd=lgd,
            ead=ead,
            collateral_nrv=collateral_nrv,
            unsecured_exposure=unsecured_exposure,
            base_lgd=base_lgd,
            cure_rate=cure_rate,
            recovery_rate=recovery_rate,
            time_to_recovery_months=time_to_recovery_months,
            discount_factor=discount_factor,
            calculation_details=calculation_details
        )
    
    def _calculate_collateral_nrv(
        self,
        db: Session,
        instrument: FinancialInstrument,
        reporting_date: date
    ) -> Decimal:
        """
        Calculate Net Realizable Value of collateral with haircuts.
        
        NRV = Σ(Collateral Value × (1 - Haircut) - Disposal Costs)
        
        Args:
            db: Database session
            instrument: Financial instrument
            reporting_date: Reporting date
            
        Returns:
            Total collateral NRV
        """
        # Fetch collateral for instrument
        collaterals = db.query(Collateral).filter(
            Collateral.instrument_id == instrument.instrument_id
        ).all()
        
        if not collaterals:
            return Decimal("0")
        
        total_nrv = Decimal("0")
        
        for collateral in collaterals:
            # Get current valuation (use forced sale value if available)
            current_value = collateral.forced_sale_value or collateral.current_value or Decimal("0")
            
            # Get haircut for collateral type
            haircut = self._get_collateral_haircut(db, collateral.collateral_type)
            
            # Calculate NRV
            disposal_costs = collateral.disposal_costs or Decimal("0")
            nrv = (current_value * (Decimal("1") - haircut)) - disposal_costs
            
            total_nrv += max(Decimal("0"), nrv)
        
        return total_nrv
    
    def _get_collateral_haircut(
        self,
        db: Session,
        collateral_type: CollateralType
    ) -> Decimal:
        """
        Get haircut percentage for collateral type.
        
        Args:
            db: Database session
            collateral_type: Collateral type
            
        Returns:
            Haircut as Decimal (e.g., 0.20 for 20%)
        """
        # Fetch haircut config
        config = db.query(CollateralHaircutConfig).filter(
            CollateralHaircutConfig.collateral_type == collateral_type,
            CollateralHaircutConfig.is_active == True
        ).first()
        
        if config:
            return config.haircut_percentage
        
        # Default haircuts by collateral type
        default_haircuts = {
            CollateralType.REAL_ESTATE: Decimal("0.30"),  # 30%
            CollateralType.VEHICLE: Decimal("0.40"),  # 40%
            CollateralType.EQUIPMENT: Decimal("0.50"),  # 50%
            CollateralType.INVENTORY: Decimal("0.60"),  # 60%
            CollateralType.RECEIVABLES: Decimal("0.50"),  # 50%
            CollateralType.CASH: Decimal("0.00"),  # 0%
            CollateralType.SECURITIES: Decimal("0.20"),  # 20%
            CollateralType.OTHER: Decimal("0.70")  # 70% (conservative)
        }
        
        return default_haircuts.get(collateral_type, Decimal("0.70"))
    
    def _get_base_lgd(
        self,
        db: Session,
        instrument: FinancialInstrument
    ) -> Decimal:
        """
        Get base LGD from historical workout recovery data.
        
        Args:
            db: Database session
            instrument: Financial instrument
            
        Returns:
            Base LGD
        """
        # Query historical workout recoveries for similar instruments
        # Filter by product type and collateral status
        recoveries = db.query(WorkoutRecovery).filter(
            WorkoutRecovery.product_type == instrument.product_type
        ).all()
        
        if not recoveries:
            # Use default based on collateral status
            has_collateral = db.query(Collateral).filter(
                Collateral.instrument_id == instrument.instrument_id
            ).count() > 0
            
            if has_collateral:
                return self.DEFAULT_BASE_LGD["SECURED"]
            else:
                return self.DEFAULT_BASE_LGD["UNSECURED"]
        
        # Calculate average LGD from historical data
        total_lgd = sum(recovery.lgd_realized for recovery in recoveries)
        avg_lgd = total_lgd / len(recoveries)
        
        return avg_lgd
    
    def _get_cure_rate(self, instrument: FinancialInstrument) -> Decimal:
        """
        Get cure rate based on instrument stage.
        
        Cure rate represents probability of recovery without loss (Stage 2 only).
        
        Args:
            instrument: Financial instrument
            
        Returns:
            Cure rate
        """
        return self.DEFAULT_CURE_RATES.get(instrument.current_stage, Decimal("0"))
    
    def _estimate_time_to_recovery(self, instrument: FinancialInstrument) -> int:
        """
        Estimate time to recovery in months.
        
        Args:
            instrument: Financial instrument
            
        Returns:
            Time to recovery in months
        """
        # Default time to recovery by stage
        if instrument.current_stage == Stage.STAGE_1:
            return 0  # No default expected
        elif instrument.current_stage == Stage.STAGE_2:
            return 12  # 1 year
        else:  # Stage 3
            return 36  # 3 years
    
    def _calculate_discount_factor(
        self,
        effective_interest_rate: Decimal,
        months: int
    ) -> Decimal:
        """
        Calculate discount factor for time value of money.
        
        DF = 1 / (1 + r)^t
        
        Args:
            effective_interest_rate: Annual EIR
            months: Time period in months
            
        Returns:
            Discount factor
        """
        if months == 0:
            return Decimal("1.0")
        
        years = Decimal(str(months)) / Decimal("12")
        discount_factor = Decimal("1") / ((Decimal("1") + effective_interest_rate) ** years)
        
        return discount_factor


class CollateralRevaluationService:
    """Service for tracking collateral revaluations"""
    
    def revalue_collateral(
        self,
        db: Session,
        collateral_id: str,
        new_value: Decimal,
        revaluation_date: date,
        revalued_by: str,
        notes: Optional[str] = None
    ) -> Collateral:
        """
        Revalue collateral and update records.
        
        Args:
            db: Database session
            collateral_id: Collateral ID
            new_value: New valuation amount
            revaluation_date: Revaluation date
            revalued_by: User ID
            notes: Optional notes
            
        Returns:
            Updated Collateral record
        """
        logger.info(f"Revaluing collateral {collateral_id}")
        
        collateral = db.query(Collateral).filter(
            Collateral.collateral_id == collateral_id
        ).first()
        
        if not collateral:
            raise ValueError(f"Collateral {collateral_id} not found")
        
        # Update valuation
        collateral.current_value = new_value
        collateral.last_revaluation_date = revaluation_date
        
        db.commit()
        
        logger.info(f"Collateral {collateral_id} revalued to {new_value}")
        
        return collateral
    
    def get_revaluation_due(
        self,
        db: Session,
        revaluation_frequency_months: int = 12
    ) -> List[Collateral]:
        """
        Get collateral due for revaluation.
        
        Args:
            db: Database session
            revaluation_frequency_months: Revaluation frequency in months
            
        Returns:
            List of collateral due for revaluation
        """
        cutoff_date = date.today() - timedelta(days=revaluation_frequency_months * 30)
        
        collaterals = db.query(Collateral).filter(
            (Collateral.last_revaluation_date < cutoff_date) |
            (Collateral.last_revaluation_date == None)
        ).all()
        
        return collaterals


# Global service instances
facility_lgd_service = FacilityLGDService()
collateral_revaluation_service = CollateralRevaluationService()
