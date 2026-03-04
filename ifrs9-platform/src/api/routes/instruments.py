"""Instruments API routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date

from src.api.dependencies import get_db
from src.db.models import FinancialInstrument, Customer
from src.db.schemas import FinancialInstrumentResponse

router = APIRouter(prefix="/instruments", tags=["instruments"])


@router.get("", response_model=List[dict])
def get_instruments(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    Get all financial instruments with optional filters.
    """
    query = db.query(FinancialInstrument)
    
    # Apply filters
    if stage:
        query = query.filter(FinancialInstrument.current_stage == stage)
    
    if status:
        query = query.filter(FinancialInstrument.status == status)
    
    # Apply limit
    if limit:
        query = query.limit(limit)
    
    instruments = query.all()
    
    # Convert to dict for JSON serialization
    result = []
    for instrument in instruments:
        result.append({
            "instrument_id": instrument.instrument_id,
            "customer_id": instrument.customer_id,
            "instrument_type": instrument.instrument_type.value,
            "principal_amount": float(instrument.principal_amount),
            "interest_rate": float(instrument.interest_rate),
            "currency": instrument.currency,
            "days_past_due": instrument.days_past_due,
            "current_stage": instrument.current_stage.value if instrument.current_stage else None,
            "status": instrument.status.value,
            "origination_date": instrument.origination_date.isoformat(),
            "maturity_date": instrument.maturity_date.isoformat(),
            "is_modified": instrument.is_modified,
            "classification": instrument.classification.value if instrument.classification else None,
        })
    
    return result


@router.get("/{instrument_id}", response_model=dict)
def get_instrument(
    instrument_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific financial instrument by ID.
    """
    instrument = db.query(FinancialInstrument).filter(
        FinancialInstrument.instrument_id == instrument_id
    ).first()
    
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    return {
        "instrument_id": instrument.instrument_id,
        "customer_id": instrument.customer_id,
        "instrument_type": instrument.instrument_type.value,
        "principal_amount": float(instrument.principal_amount),
        "interest_rate": float(instrument.interest_rate),
        "currency": instrument.currency,
        "days_past_due": instrument.days_past_due,
        "current_stage": instrument.current_stage.value if instrument.current_stage else None,
        "status": instrument.status.value,
        "origination_date": instrument.origination_date.isoformat(),
        "maturity_date": instrument.maturity_date.isoformat(),
        "is_modified": instrument.is_modified,
        "classification": instrument.classification.value if instrument.classification else None,
        "business_model": instrument.business_model.value if instrument.business_model else None,
        "sppi_test_result": instrument.sppi_test_result,
    }


@router.get("/customer/{customer_id}", response_model=List[dict])
def get_customer_instruments(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all instruments for a specific customer.
    """
    instruments = db.query(FinancialInstrument).filter(
        FinancialInstrument.customer_id == customer_id
    ).all()
    
    result = []
    for instrument in instruments:
        result.append({
            "instrument_id": instrument.instrument_id,
            "instrument_type": instrument.instrument_type.value,
            "principal_amount": float(instrument.principal_amount),
            "interest_rate": float(instrument.interest_rate),
            "days_past_due": instrument.days_past_due,
            "current_stage": instrument.current_stage.value if instrument.current_stage else None,
            "status": instrument.status.value,
        })
    
    return result
