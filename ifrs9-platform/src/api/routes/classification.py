"""Classification API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from src.api.dependencies import get_db, get_current_user_id, get_client_ip
from src.services.classification import ClassificationService
from src.services.audit_trail import AuditTrailService
from src.db.models import FinancialInstrument
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/classification", tags=["classification"])


class ClassifyRequest(BaseModel):
    """Request to classify an instrument"""
    instrument_id: str


class ClassifyResponse(BaseModel):
    """Classification result"""
    instrument_id: str
    classification: str
    business_model: str
    sppi_passed: bool
    rationale: str


@router.post("/classify", response_model=ClassifyResponse)
def classify_instrument(
    request: ClassifyRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    ip_address: str = Depends(get_client_ip)
):
    """
    Classify a financial instrument.
    
    Performs business model test and SPPI test to determine classification
    (Amortized Cost, FVOCI, or FVTPL).
    
    Args:
        request: Classification request
        db: Database session
        user_id: Current user ID
        ip_address: Client IP address
        
    Returns:
        Classification result
    """
    try:
        # Get instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == request.instrument_id
        ).first()
        
        if not instrument:
            raise HTTPException(status_code=404, detail=f"Instrument {request.instrument_id} not found")
        
        logger.info(f"Classifying instrument {request.instrument_id}")
        
        # Classify instrument
        classification_service = ClassificationService()
        result = classification_service.classify_instrument(instrument)
        
        # Update instrument
        instrument.classification = result.classification
        instrument.business_model = result.business_model
        instrument.sppi_test_passed = result.sppi_passed
        instrument.classification_rationale = result.rationale
        
        db.commit()
        
        # Log to audit trail
        audit_service = AuditTrailService(db, user_id, ip_address)
        audit_service.log_classification(
            instrument_id=request.instrument_id,
            classification=result.classification.value,
            business_model=result.business_model.value,
            sppi_passed=result.sppi_passed,
            rationale=result.rationale
        )
        db.commit()
        
        return ClassifyResponse(
            instrument_id=request.instrument_id,
            classification=result.classification.value,
            business_model=result.business_model.value,
            sppi_passed=result.sppi_passed,
            rationale=result.rationale
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error classifying instrument: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instrument_id}/rationale", response_model=Dict[str, Any])
def get_classification_rationale(
    instrument_id: str,
    db: Session = Depends(get_db)
):
    """
    Get classification rationale for an instrument.
    
    Args:
        instrument_id: Instrument ID
        db: Database session
        
    Returns:
        Classification details and rationale
    """
    try:
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == instrument_id
        ).first()
        
        if not instrument:
            raise HTTPException(status_code=404, detail=f"Instrument {instrument_id} not found")
        
        return {
            'instrument_id': instrument_id,
            'classification': instrument.classification.value,
            'business_model': instrument.business_model.value,
            'sppi_passed': instrument.sppi_test_passed,
            'rationale': instrument.classification_rationale
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting classification rationale: {e}")
        raise HTTPException(status_code=500, detail=str(e))
