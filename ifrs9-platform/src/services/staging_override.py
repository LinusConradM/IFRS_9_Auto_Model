"""Staging override service for manual stage adjustments with maker-checker approval"""
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
import uuid

from src.db.models import (
    StagingOverride, FinancialInstrument, Stage, 
    OverrideStatus, ApprovalWorkflow, WorkflowType
)
from src.services.maker_checker import maker_checker_service
from src.services.ecl_engine import ecl_calculation_service
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ECLImpact:
    """ECL impact calculation result"""
    def __init__(self, before_ecl: Decimal, after_ecl: Decimal, 
                 impact_amount: Decimal, impact_percentage: Decimal):
        self.before_ecl = before_ecl
        self.after_ecl = after_ecl
        self.impact_amount = impact_amount
        self.impact_percentage = impact_percentage


class StagingOverrideService:
    """Service for managing manual staging overrides with approval workflow"""
    
    def request_override(
        self,
        db: Session,
        instrument_id: str,
        override_stage: Stage,
        justification: str,
        requested_by: str,
        expiry_date: Optional[date] = None
    ) -> StagingOverride:
        """
        Request a manual staging override.
        
        Args:
            db: Database session
            instrument_id: Financial instrument ID
            override_stage: Proposed override stage
            justification: Business justification for override
            requested_by: User ID requesting override
            expiry_date: Optional expiry date for override
            
        Returns:
            StagingOverride record
        """
        logger.info(f"Requesting staging override for instrument {instrument_id}")
        
        # Fetch instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == instrument_id
        ).first()
        
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
        
        # Calculate ECL impact
        ecl_impact = self.calculate_ecl_impact(db, instrument, override_stage)
        
        # Create override record
        override = StagingOverride(
            override_id=str(uuid.uuid4()),
            instrument_id=instrument_id,
            original_stage=instrument.current_stage,
            override_stage=override_stage,
            justification=justification,
            requested_by=requested_by,
            requested_at=datetime.utcnow(),
            status=OverrideStatus.PENDING,
            ecl_before_override=ecl_impact.before_ecl,
            ecl_after_override=ecl_impact.after_ecl,
            ecl_impact_amount=ecl_impact.impact_amount,
            expiry_date=expiry_date or (date.today() + timedelta(days=90))
        )
        
        db.add(override)
        db.flush()
        
        # Create approval workflow
        workflow_data = {
            "override_id": override.override_id,
            "instrument_id": instrument_id,
            "original_stage": instrument.current_stage.value,
            "override_stage": override_stage.value,
            "ecl_impact": float(ecl_impact.impact_amount)
        }
        
        workflow = maker_checker_service.request_approval(
            db=db,
            workflow_type=WorkflowType.STAGING_OVERRIDE.value,
            request_data=workflow_data,
            requester_id=requested_by
        )
        
        override.workflow_id = workflow.workflow_id
        db.commit()
        
        logger.info(f"Staging override requested: {override.override_id}")
        return override
    
    def calculate_ecl_impact(
        self,
        db: Session,
        instrument: FinancialInstrument,
        proposed_stage: Stage
    ) -> ECLImpact:
        """
        Calculate ECL impact of staging override.
        
        Args:
            db: Database session
            instrument: Financial instrument
            proposed_stage: Proposed override stage
            
        Returns:
            ECLImpact with before/after ECL amounts
        """
        # Get current ECL
        current_ecl = instrument.current_ecl or Decimal("0")
        
        # Calculate ECL with proposed stage
        # Temporarily change stage for calculation
        original_stage = instrument.current_stage
        
        try:
            # Calculate ECL with new stage
            ecl_result = ecl_calculation_service.calculate_ecl(
                instrument=instrument,
                stage=proposed_stage,
                reporting_date=date.today()
            )
            proposed_ecl = ecl_result.ecl_amount
        finally:
            # Restore original stage (no need to change it back since we didn't commit)
            pass
        
        # Calculate impact
        impact_amount = proposed_ecl - current_ecl
        impact_percentage = (impact_amount / current_ecl * 100) if current_ecl > 0 else Decimal("0")
        
        return ECLImpact(
            before_ecl=current_ecl,
            after_ecl=proposed_ecl,
            impact_amount=impact_amount,
            impact_percentage=impact_percentage
        )
    
    def apply_override(
        self,
        db: Session,
        override_id: str,
        approved_by: str
    ) -> StagingOverride:
        """
        Apply approved staging override to instrument.
        
        Args:
            db: Database session
            override_id: Override ID
            approved_by: User ID approving override
            
        Returns:
            Updated StagingOverride record
        """
        logger.info(f"Applying staging override {override_id}")
        
        # Fetch override
        override = db.query(StagingOverride).filter(
            StagingOverride.override_id == override_id
        ).first()
        
        if not override:
            raise ValueError(f"Override {override_id} not found")
        
        if override.status != OverrideStatus.PENDING:
            raise ValueError(f"Override {override_id} is not pending (status: {override.status})")
        
        # Approve workflow
        success, error = maker_checker_service.approve_request(
            db=db,
            workflow_id=override.workflow_id,
            approver_id=approved_by
        )
        
        if not success:
            raise ValueError(f"Failed to approve workflow: {error}")
        
        # Fetch instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == override.instrument_id
        ).first()
        
        if not instrument:
            raise ValueError(f"Instrument {override.instrument_id} not found")
        
        # Apply override
        instrument.current_stage = override.override_stage
        instrument.stage_override_active = True
        instrument.stage_override_reason = override.justification
        
        # Update override status
        override.status = OverrideStatus.APPROVED
        override.approved_by = approved_by
        override.approved_at = datetime.utcnow()
        override.applied_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Staging override applied: {override_id}")
        return override
    
    def reject_override(
        self,
        db: Session,
        override_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> StagingOverride:
        """
        Reject staging override request.
        
        Args:
            db: Database session
            override_id: Override ID
            rejected_by: User ID rejecting override
            rejection_reason: Reason for rejection
            
        Returns:
            Updated StagingOverride record
        """
        logger.info(f"Rejecting staging override {override_id}")
        
        # Fetch override
        override = db.query(StagingOverride).filter(
            StagingOverride.override_id == override_id
        ).first()
        
        if not override:
            raise ValueError(f"Override {override_id} not found")
        
        if override.status != OverrideStatus.PENDING:
            raise ValueError(f"Override {override_id} is not pending")
        
        # Reject workflow
        success, error = maker_checker_service.reject_request(
            db=db,
            workflow_id=override.workflow_id,
            approver_id=rejected_by,
            rejection_reason=rejection_reason
        )
        
        if not success:
            raise ValueError(f"Failed to reject workflow: {error}")
        
        # Update override status
        override.status = OverrideStatus.REJECTED
        override.rejected_by = rejected_by
        override.rejected_at = datetime.utcnow()
        override.rejection_reason = rejection_reason
        
        db.commit()
        
        logger.info(f"Staging override rejected: {override_id}")
        return override
    
    def get_pending_overrides(
        self,
        db: Session,
        instrument_id: Optional[str] = None
    ) -> List[StagingOverride]:
        """
        Get pending staging overrides.
        
        Args:
            db: Database session
            instrument_id: Optional filter by instrument ID
            
        Returns:
            List of pending overrides
        """
        query = db.query(StagingOverride).filter(
            StagingOverride.status == OverrideStatus.PENDING
        )
        
        if instrument_id:
            query = query.filter(StagingOverride.instrument_id == instrument_id)
        
        return query.all()
    
    def check_expired_overrides(self, db: Session) -> List[StagingOverride]:
        """
        Check for expired overrides and revert instruments to original staging.
        
        Args:
            db: Database session
            
        Returns:
            List of expired overrides
        """
        logger.info("Checking for expired staging overrides")
        
        # Find active overrides past expiry date
        expired_overrides = db.query(StagingOverride).filter(
            StagingOverride.status == OverrideStatus.APPROVED,
            StagingOverride.expiry_date < date.today()
        ).all()
        
        for override in expired_overrides:
            # Fetch instrument
            instrument = db.query(FinancialInstrument).filter(
                FinancialInstrument.instrument_id == override.instrument_id
            ).first()
            
            if instrument and instrument.stage_override_active:
                # Revert to system-determined stage
                instrument.stage_override_active = False
                instrument.stage_override_reason = None
                
                # Update override status
                override.status = OverrideStatus.EXPIRED
                override.expired_at = datetime.utcnow()
                
                logger.info(f"Expired override {override.override_id} for instrument {instrument.instrument_id}")
        
        db.commit()
        
        return expired_overrides


# Global service instance
staging_override_service = StagingOverrideService()
