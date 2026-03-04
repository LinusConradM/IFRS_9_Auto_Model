"""Staging API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import date

from src.api.dependencies import get_db, get_current_user_id, get_client_ip
from src.services.staging import StagingService
from src.services.audit_trail import AuditTrailService
from src.db.models import FinancialInstrument, StageTransition
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/staging", tags=["staging"])


class DetermineStageRequest(BaseModel):
    """Request to determine stage for an instrument"""
    instrument_id: str
    reporting_date: date


class DetermineStageResponse(BaseModel):
    """Stage determination result"""
    instrument_id: str
    stage: str
    previous_stage: str
    reason: str
    sicr_detected: bool
    sicr_indicators: List[str]
    credit_impaired: bool


@router.post("/determine-stage", response_model=DetermineStageResponse)
def determine_stage(
    request: DetermineStageRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    ip_address: str = Depends(get_client_ip)
):
    """
    Determine impairment stage for a financial instrument.
    
    Evaluates SICR and credit impairment to assign Stage 1, 2, or 3.
    
    Args:
        request: Stage determination request
        db: Database session
        user_id: Current user ID
        ip_address: Client IP address
        
    Returns:
        Stage determination result
    """
    try:
        # Get instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == request.instrument_id
        ).first()
        
        if not instrument:
            raise HTTPException(status_code=404, detail=f"Instrument {request.instrument_id} not found")
        
        logger.info(f"Determining stage for instrument {request.instrument_id}")
        
        # Determine stage
        staging_service = StagingService(db)
        result = staging_service.determine_stage(instrument, request.reporting_date)
        
        previous_stage = instrument.current_stage
        
        # Update instrument if stage changed
        if result.stage != previous_stage:
            instrument.current_stage = result.stage
            
            # Create stage transition record
            transition = StageTransition(
                instrument_id=instrument.id,
                transition_date=request.reporting_date,
                from_stage=previous_stage,
                to_stage=result.stage,
                reason=result.reason,
                sicr_indicators=result.sicr_indicators,
                days_past_due=instrument.days_past_due,
                pd_increase_ratio=result.pd_increase_ratio
            )
            db.add(transition)
            
            db.commit()
            
            # Log to audit trail
            audit_service = AuditTrailService(db, user_id, ip_address)
            audit_service.log_staging(
                instrument_id=request.instrument_id,
                from_stage=previous_stage.value,
                to_stage=result.stage.value,
                reason=result.reason,
                sicr_indicators=result.sicr_indicators,
                days_past_due=instrument.days_past_due
            )
            db.commit()
        
        return DetermineStageResponse(
            instrument_id=request.instrument_id,
            stage=result.stage.value,
            previous_stage=previous_stage.value,
            reason=result.reason,
            sicr_detected=result.sicr_detected,
            sicr_indicators=result.sicr_indicators,
            credit_impaired=result.credit_impaired
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error determining stage: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-sicr/{instrument_id}", response_model=Dict[str, Any])
def evaluate_sicr(
    instrument_id: str,
    reporting_date: date,
    db: Session = Depends(get_db)
):
    """
    Evaluate SICR (Significant Increase in Credit Risk) for an instrument.
    
    Args:
        instrument_id: Instrument ID
        reporting_date: Reporting date
        db: Database session
        
    Returns:
        SICR evaluation result
    """
    try:
        # Get instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == instrument_id
        ).first()
        
        if not instrument:
            raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
        
        logger.info(f"Evaluating SICR for instrument {instrument_id}")
        
        # Evaluate SICR
        staging_service = StagingService(db)
        sicr_result = staging_service.evaluate_sicr(instrument, reporting_date)
        
        return {
            'instrument_id': instrument_id,
            'sicr_detected': sicr_result.sicr_detected,
            'indicators': sicr_result.indicators,
            'pd_increase_ratio': float(sicr_result.pd_increase_ratio) if sicr_result.pd_increase_ratio else None,
            'days_past_due': instrument.days_past_due,
            'is_forbearance': instrument.is_forbearance,
            'is_watchlist': instrument.is_watchlist
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating SICR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transitions", response_model=List[Dict[str, Any]])
def get_stage_transitions(
    instrument_id: str = None,
    start_date: date = None,
    end_date: date = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get stage transition history.
    
    Args:
        instrument_id: Filter by instrument ID (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of stage transitions
    """
    try:
        query = db.query(StageTransition)
        
        if instrument_id:
            instrument = db.query(FinancialInstrument).filter(
                FinancialInstrument.instrument_id == instrument_id
            ).first()
            if instrument:
                query = query.filter(StageTransition.instrument_id == instrument.id)
        
        if start_date:
            query = query.filter(StageTransition.transition_date >= start_date)
        if end_date:
            query = query.filter(StageTransition.transition_date <= end_date)
        
        query = query.order_by(StageTransition.transition_date.desc())
        query = query.limit(limit)
        
        transitions = query.all()
        
        return [
            {
                'id': t.id,
                'instrument_id': t.instrument.instrument_id,
                'transition_date': t.transition_date.isoformat(),
                'from_stage': t.from_stage.value,
                'to_stage': t.to_stage.value,
                'reason': t.reason,
                'sicr_indicators': t.sicr_indicators,
                'days_past_due': t.days_past_due
            }
            for t in transitions
        ]
        
    except Exception as e:
        logger.error(f"Error getting stage transitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
