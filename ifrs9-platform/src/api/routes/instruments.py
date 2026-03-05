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




@router.post("", response_model=dict, status_code=201)
def create_instrument(
    instrument_data: dict,
    db: Session = Depends(get_db)
):
    """
    Create a new financial instrument.
    """
    from src.db.models import InstrumentType, Classification, BusinessModel, Stage, InstrumentStatus
    from decimal import Decimal
    from datetime import datetime

    try:
        # Check if customer exists
        customer = db.query(Customer).filter(
            Customer.customer_id == instrument_data['customer_id']
        ).first()

        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer {instrument_data['customer_id']} not found")

        # Check for duplicate instrument_id
        existing = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == instrument_data['instrument_id']
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail=f"Instrument {instrument_data['instrument_id']} already exists")

        # Create instrument
        instrument = FinancialInstrument(
            instrument_id=instrument_data['instrument_id'],
            customer_id=customer.customer_id,
            instrument_type=InstrumentType[instrument_data['instrument_type']],
            classification=Classification[instrument_data.get('classification', 'AMORTIZED_COST')],
            business_model=BusinessModel[instrument_data.get('business_model', 'HOLD_TO_COLLECT')],
            sppi_test_result=instrument_data.get('sppi_test_result', True),
            current_stage=Stage[instrument_data.get('current_stage', 'STAGE_1')],
            status=InstrumentStatus[instrument_data.get('status', 'ACTIVE')],
            origination_date=datetime.strptime(instrument_data['origination_date'], '%Y-%m-%d').date(),
            maturity_date=datetime.strptime(instrument_data['maturity_date'], '%Y-%m-%d').date(),
            principal_amount=Decimal(str(instrument_data['principal_amount'])),
            interest_rate=Decimal(str(instrument_data['interest_rate'])),
            currency=instrument_data.get('currency', 'UGX'),
            days_past_due=instrument_data.get('days_past_due', 0),
            is_poci=instrument_data.get('is_poci', False),
            is_modified=instrument_data.get('is_modified', False)
        )

        db.add(instrument)
        db.commit()
        db.refresh(instrument)

        return {
            "instrument_id": instrument.instrument_id,
            "customer_id": instrument.customer_id,
            "instrument_type": instrument.instrument_type.value,
            "status": "created"
        }

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{instrument_id}", response_model=dict)
def update_instrument(
    instrument_id: str,
    instrument_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update an existing financial instrument.
    """
    from src.db.models import InstrumentType, Classification, BusinessModel, Stage, InstrumentStatus
    from decimal import Decimal
    from datetime import datetime

    instrument = db.query(FinancialInstrument).filter(
        FinancialInstrument.instrument_id == instrument_id
    ).first()

    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    try:
        # Update allowed fields
        if 'days_past_due' in instrument_data:
            instrument.days_past_due = instrument_data['days_past_due']

        if 'interest_rate' in instrument_data:
            instrument.interest_rate = Decimal(str(instrument_data['interest_rate']))

        if 'status' in instrument_data:
            instrument.status = InstrumentStatus[instrument_data['status']]

        if 'current_stage' in instrument_data:
            instrument.current_stage = Stage[instrument_data['current_stage']]

        if 'classification' in instrument_data:
            instrument.classification = Classification[instrument_data['classification']]

        if 'is_modified' in instrument_data:
            instrument.is_modified = instrument_data['is_modified']
            if instrument_data['is_modified']:
                instrument.modification_date = datetime.utcnow().date()

        instrument.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(instrument)

        return {
            "instrument_id": instrument.instrument_id,
            "status": "updated"
        }

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{instrument_id}", response_model=dict)
def delete_instrument(
    instrument_id: str,
    db: Session = Depends(get_db)
):
    """
    Soft delete a financial instrument (set status to DERECOGNIZED).
    """
    from src.db.models import InstrumentStatus
    from datetime import datetime

    instrument = db.query(FinancialInstrument).filter(
        FinancialInstrument.instrument_id == instrument_id
    ).first()

    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    # Soft delete by setting status to DERECOGNIZED
    instrument.status = InstrumentStatus.DERECOGNIZED
    instrument.updated_at = datetime.utcnow()

    db.commit()

    return {
        "instrument_id": instrument_id,
        "status": "deleted"
    }


@router.get("/{instrument_id}/history", response_model=dict)
def get_instrument_history(
    instrument_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete history for an instrument including stage transitions and ECL calculations.
    """
    from src.db.models import StageTransition, ECLCalculation

    instrument = db.query(FinancialInstrument).filter(
        FinancialInstrument.instrument_id == instrument_id
    ).first()

    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    # Get stage transitions
    transitions = db.query(StageTransition).filter(
        StageTransition.instrument_id == instrument_id
    ).order_by(StageTransition.transition_date.desc()).all()

    # Get ECL calculations
    ecl_calcs = db.query(ECLCalculation).filter(
        ECLCalculation.instrument_id == instrument_id
    ).order_by(ECLCalculation.reporting_date.desc()).limit(10).all()

    return {
        "instrument_id": instrument_id,
        "current_stage": instrument.current_stage.value if instrument.current_stage else None,
        "current_status": instrument.status.value,
        "stage_transitions": [
            {
                "transition_id": t.transition_id,
                "transition_date": t.transition_date.isoformat(),
                "from_stage": t.from_stage.value,
                "to_stage": t.to_stage.value,
                "transition_reason": t.transition_reason
            }
            for t in transitions
        ],
        "ecl_calculations": [
            {
                "calculation_id": e.calculation_id,
                "reporting_date": e.reporting_date.isoformat(),
                "stage": e.stage.value,
                "ecl_amount": float(e.ecl_amount),
                "pd": float(e.pd),
                "lgd": float(e.lgd),
                "ead": float(e.ead)
            }
            for e in ecl_calcs
        ]
    }


@router.get("/{instrument_id}/ecl-calculations", response_model=List[dict])
def get_instrument_ecl_calculations(
    instrument_id: str,
    limit: Optional[int] = Query(20, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    Get ECL calculation history for an instrument.
    """
    from src.db.models import ECLCalculation

    instrument = db.query(FinancialInstrument).filter(
        FinancialInstrument.instrument_id == instrument_id
    ).first()

    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    ecl_calcs = db.query(ECLCalculation).filter(
        ECLCalculation.instrument_id == instrument_id
    ).order_by(ECLCalculation.reporting_date.desc()).limit(limit).all()

    return [
        {
            "calculation_id": e.calculation_id,
            "reporting_date": e.reporting_date.isoformat(),
            "stage": e.stage.value,
            "ecl_amount": float(e.ecl_amount),
            "pd": float(e.pd),
            "lgd": float(e.lgd),
            "ead": float(e.ead),
            "calculation_method": e.calculation_method,
            "time_horizon": e.time_horizon,
            "calculation_timestamp": e.calculation_timestamp.isoformat() if e.calculation_timestamp else None
        }
        for e in ecl_calcs
    ]


@router.get("/{instrument_id}/stage-transitions", response_model=List[dict])
def get_instrument_stage_transitions(
    instrument_id: str,
    limit: Optional[int] = Query(20, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """
    Get stage transition history for an instrument.
    """
    from src.db.models import StageTransition

    instrument = db.query(FinancialInstrument).filter(
        FinancialInstrument.instrument_id == instrument_id
    ).first()

    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")

    transitions = db.query(StageTransition).filter(
        StageTransition.instrument_id == instrument_id
    ).order_by(StageTransition.transition_date.desc()).limit(limit).all()

    return [
        {
            "transition_id": t.transition_id,
            "transition_date": t.transition_date.isoformat(),
            "from_stage": t.from_stage.value,
            "to_stage": t.to_stage.value,
            "transition_reason": t.transition_reason,
            "sicr_indicators": t.sicr_indicators,
            "days_past_due": t.days_past_due,
            "is_automatic": t.is_automatic,
            "approved_by": t.approved_by
        }
        for t in transitions
    ]

