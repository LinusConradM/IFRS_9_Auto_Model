"""Staging Override API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal

from src.api.dependencies import get_db
from src.api.routes.auth import get_current_user
from src.services.staging_override import staging_override_service
from src.db.models import User, Stage, OverrideStatus

router = APIRouter(prefix="/staging/overrides", tags=["staging-overrides"])


# Request/Response Models
class OverrideRequestCreate(BaseModel):
    instrument_id: str = Field(..., description="Financial instrument ID")
    override_stage: Stage = Field(..., description="Proposed override stage")
    justification: str = Field(..., min_length=10, description="Business justification")
    expiry_date: Optional[date] = Field(None, description="Override expiry date (default: 90 days)")


class OverrideApproveRequest(BaseModel):
    approved_by: Optional[str] = None  # Will be set from current user


class OverrideRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=10, description="Reason for rejection")


class ECLImpactResponse(BaseModel):
    before_ecl: Decimal
    after_ecl: Decimal
    impact_amount: Decimal
    impact_percentage: Decimal


class OverrideResponse(BaseModel):
    override_id: str
    instrument_id: str
    original_stage: Stage
    override_stage: Stage
    justification: str
    status: OverrideStatus
    requested_by: str
    requested_at: str
    approved_by: Optional[str]
    approved_at: Optional[str]
    rejected_by: Optional[str]
    rejected_at: Optional[str]
    rejection_reason: Optional[str]
    ecl_before_override: Optional[Decimal]
    ecl_after_override: Optional[Decimal]
    ecl_impact_amount: Optional[Decimal]
    expiry_date: Optional[date]
    workflow_id: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=OverrideResponse, status_code=status.HTTP_201_CREATED)
async def request_override(
    request: OverrideRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request a staging override for a financial instrument.
    
    Requires maker-checker approval before being applied.
    
    - **instrument_id**: ID of the financial instrument
    - **override_stage**: Proposed stage (STAGE_1, STAGE_2, or STAGE_3)
    - **justification**: Business justification (minimum 10 characters)
    - **expiry_date**: Optional expiry date (default: 90 days from now)
    """
    try:
        override = staging_override_service.request_override(
            db=db,
            instrument_id=request.instrument_id,
            override_stage=request.override_stage,
            justification=request.justification,
            requested_by=current_user.user_id,
            expiry_date=request.expiry_date
        )
        
        return OverrideResponse(
            override_id=override.override_id,
            instrument_id=override.instrument_id,
            original_stage=override.original_stage,
            override_stage=override.override_stage,
            justification=override.justification,
            status=override.status,
            requested_by=override.requested_by,
            requested_at=override.requested_at.isoformat(),
            approved_by=override.approved_by,
            approved_at=override.approved_at.isoformat() if override.approved_at else None,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at.isoformat() if override.rejected_at else None,
            rejection_reason=override.rejection_reason,
            ecl_before_override=override.ecl_before_override,
            ecl_after_override=override.ecl_after_override,
            ecl_impact_amount=override.ecl_impact_amount,
            expiry_date=override.expiry_date,
            workflow_id=override.workflow_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create override request: {str(e)}"
        )


@router.get("", response_model=List[OverrideResponse])
async def list_overrides(
    instrument_id: Optional[str] = Query(None, description="Filter by instrument ID"),
    status_filter: Optional[OverrideStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List staging overrides with optional filters.
    
    - **instrument_id**: Filter by specific instrument
    - **status_filter**: Filter by status (PENDING, APPROVED, REJECTED, EXPIRED)
    - **skip**: Pagination offset
    - **limit**: Maximum results (1-1000)
    """
    from src.db.models import StagingOverride
    
    query = db.query(StagingOverride)
    
    if instrument_id:
        query = query.filter(StagingOverride.instrument_id == instrument_id)
    
    if status_filter:
        query = query.filter(StagingOverride.status == status_filter)
    
    overrides = query.offset(skip).limit(limit).all()
    
    return [
        OverrideResponse(
            override_id=o.override_id,
            instrument_id=o.instrument_id,
            original_stage=o.original_stage,
            override_stage=o.override_stage,
            justification=o.justification,
            status=o.status,
            requested_by=o.requested_by,
            requested_at=o.requested_at.isoformat(),
            approved_by=o.approved_by,
            approved_at=o.approved_at.isoformat() if o.approved_at else None,
            rejected_by=o.rejected_by,
            rejected_at=o.rejected_at.isoformat() if o.rejected_at else None,
            rejection_reason=o.rejection_reason,
            ecl_before_override=o.ecl_before_override,
            ecl_after_override=o.ecl_after_override,
            ecl_impact_amount=o.ecl_impact_amount,
            expiry_date=o.expiry_date,
            workflow_id=o.workflow_id
        )
        for o in overrides
    ]


@router.get("/pending", response_model=List[OverrideResponse])
async def get_pending_overrides(
    instrument_id: Optional[str] = Query(None, description="Filter by instrument ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending staging overrides awaiting approval.
    """
    overrides = staging_override_service.get_pending_overrides(
        db=db,
        instrument_id=instrument_id
    )
    
    return [
        OverrideResponse(
            override_id=o.override_id,
            instrument_id=o.instrument_id,
            original_stage=o.original_stage,
            override_stage=o.override_stage,
            justification=o.justification,
            status=o.status,
            requested_by=o.requested_by,
            requested_at=o.requested_at.isoformat(),
            approved_by=o.approved_by,
            approved_at=o.approved_at.isoformat() if o.approved_at else None,
            rejected_by=o.rejected_by,
            rejected_at=o.rejected_at.isoformat() if o.rejected_at else None,
            rejection_reason=o.rejection_reason,
            ecl_before_override=o.ecl_before_override,
            ecl_after_override=o.ecl_after_override,
            ecl_impact_amount=o.ecl_impact_amount,
            expiry_date=o.expiry_date,
            workflow_id=o.workflow_id
        )
        for o in overrides
    ]


@router.get("/{override_id}", response_model=OverrideResponse)
async def get_override(
    override_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific staging override.
    """
    from src.db.models import StagingOverride
    
    override = db.query(StagingOverride).filter(
        StagingOverride.override_id == override_id
    ).first()
    
    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Override {override_id} not found"
        )
    
    return OverrideResponse(
        override_id=override.override_id,
        instrument_id=override.instrument_id,
        original_stage=override.original_stage,
        override_stage=override.override_stage,
        justification=override.justification,
        status=override.status,
        requested_by=override.requested_by,
        requested_at=override.requested_at.isoformat(),
        approved_by=override.approved_by,
        approved_at=override.approved_at.isoformat() if override.approved_at else None,
        rejected_by=override.rejected_by,
        rejected_at=override.rejected_at.isoformat() if override.rejected_at else None,
        rejection_reason=override.rejection_reason,
        ecl_before_override=override.ecl_before_override,
        ecl_after_override=override.ecl_after_override,
        ecl_impact_amount=override.ecl_impact_amount,
        expiry_date=override.expiry_date,
        workflow_id=override.workflow_id
    )


@router.post("/{override_id}/approve", response_model=OverrideResponse)
async def approve_override(
    override_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a pending staging override.
    
    Applies the override to the instrument and updates its stage.
    Requires maker-checker: approver must be different from requester.
    """
    try:
        override = staging_override_service.apply_override(
            db=db,
            override_id=override_id,
            approved_by=current_user.user_id
        )
        
        return OverrideResponse(
            override_id=override.override_id,
            instrument_id=override.instrument_id,
            original_stage=override.original_stage,
            override_stage=override.override_stage,
            justification=override.justification,
            status=override.status,
            requested_by=override.requested_by,
            requested_at=override.requested_at.isoformat(),
            approved_by=override.approved_by,
            approved_at=override.approved_at.isoformat() if override.approved_at else None,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at.isoformat() if override.rejected_at else None,
            rejection_reason=override.rejection_reason,
            ecl_before_override=override.ecl_before_override,
            ecl_after_override=override.ecl_after_override,
            ecl_impact_amount=override.ecl_impact_amount,
            expiry_date=override.expiry_date,
            workflow_id=override.workflow_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve override: {str(e)}"
        )


@router.post("/{override_id}/reject", response_model=OverrideResponse)
async def reject_override(
    override_id: str,
    request: OverrideRejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a pending staging override.
    
    - **rejection_reason**: Reason for rejection (minimum 10 characters)
    """
    try:
        override = staging_override_service.reject_override(
            db=db,
            override_id=override_id,
            rejected_by=current_user.user_id,
            rejection_reason=request.rejection_reason
        )
        
        return OverrideResponse(
            override_id=override.override_id,
            instrument_id=override.instrument_id,
            original_stage=override.original_stage,
            override_stage=override.override_stage,
            justification=override.justification,
            status=override.status,
            requested_by=override.requested_by,
            requested_at=override.requested_at.isoformat(),
            approved_by=override.approved_by,
            approved_at=override.approved_at.isoformat() if override.approved_at else None,
            rejected_by=override.rejected_by,
            rejected_at=override.rejected_at.isoformat() if override.rejected_at else None,
            rejection_reason=override.rejection_reason,
            ecl_before_override=override.ecl_before_override,
            ecl_after_override=override.ecl_after_override,
            ecl_impact_amount=override.ecl_impact_amount,
            expiry_date=override.expiry_date,
            workflow_id=override.workflow_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject override: {str(e)}"
        )
