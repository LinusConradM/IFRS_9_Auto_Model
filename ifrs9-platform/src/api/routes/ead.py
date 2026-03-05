"""EAD (Exposure at Default) Calculation API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import date

from src.api.dependencies import get_db
from src.api.routes.auth import get_current_user
from src.services.ead_calculation import ead_calculation_service
from src.db.models import User, FacilityType

router = APIRouter(prefix="/ead", tags=["ead-calculation"])


# Request/Response Models
class EADCalculationRequest(BaseModel):
    instrument_id: str = Field(..., description="Financial instrument ID")
    facility_type: FacilityType = Field(..., description="Facility type")
    outstanding_balance: Decimal = Field(..., gt=0, description="Outstanding balance")
    undrawn_commitment: Decimal = Field(default=Decimal("0"), ge=0, description="Undrawn commitment amount")
    reporting_date: date = Field(..., description="Reporting date for calculation")


class EADCalculationResponse(BaseModel):
    instrument_id: str
    facility_type: FacilityType
    outstanding_balance: Decimal
    undrawn_commitment: Decimal
    ccf: Decimal
    ead_on_balance: Decimal
    ead_off_balance: Decimal
    total_ead: Decimal
    reporting_date: date


class CCFConfigRequest(BaseModel):
    facility_type: FacilityType
    ccf_value: Decimal = Field(..., ge=0, le=1, description="CCF value (0-1)")


class CCFConfigResponse(BaseModel):
    facility_type: FacilityType
    ccf_value: Decimal
    updated_at: Optional[str]


class OffBalanceSheetExposure(BaseModel):
    instrument_id: str
    facility_type: FacilityType
    undrawn_commitment: Decimal
    ccf: Decimal
    ead_off_balance: Decimal


@router.post("/calculate", response_model=EADCalculationResponse)
async def calculate_ead(
    request: EADCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate Exposure at Default (EAD) for a financial instrument.
    
    EAD calculation includes:
    - On-balance sheet exposure (outstanding balance)
    - Off-balance sheet exposure (undrawn commitment × CCF)
    - Total EAD = On-balance + Off-balance
    
    **Parameters:**
    - **instrument_id**: Financial instrument identifier
    - **facility_type**: Type of facility (determines CCF)
    - **outstanding_balance**: Current outstanding balance
    - **undrawn_commitment**: Undrawn commitment amount (default: 0)
    - **reporting_date**: Date for calculation
    """
    try:
        from src.db.models import FinancialInstrument
        
        # Fetch instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == request.instrument_id
        ).first()
        
        if not instrument:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Instrument {request.instrument_id} not found"
            )
        
        # Calculate EAD using service
        result = ead_calculation_service.calculate_ead(
            db=db,
            instrument=instrument,
            reporting_date=request.reporting_date
        )
        
        return EADCalculationResponse(
            instrument_id=request.instrument_id,
            facility_type=request.facility_type,
            outstanding_balance=request.outstanding_balance,
            undrawn_commitment=request.undrawn_commitment,
            ccf=result.ccf,
            ead_on_balance=result.drawn_amount,
            ead_off_balance=result.undrawn_amount * result.ccf,
            total_ead=result.ead_amount,
            reporting_date=request.reporting_date
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate EAD: {str(e)}"
        )


@router.get("/ccf", response_model=Dict[str, Decimal])
async def get_ccf_configuration(
    facility_type: Optional[FacilityType] = Query(None, description="Filter by facility type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Credit Conversion Factor (CCF) configuration.
    
    Returns CCF values for all facility types or a specific type.
    
    **Parameters:**
    - **facility_type**: Optional filter for specific facility type
    """
    try:
        if facility_type:
            ccf = ead_calculation_service._get_ccf(db, type('obj', (), {'facility_type': facility_type, 'credit_conversion_factor': None})())
            return {facility_type.value: ccf}
        else:
            # Return all default CCF configurations
            return {ft.value: float(ccf) for ft, ccf in ead_calculation_service.DEFAULT_CCF.items()}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve CCF configuration: {str(e)}"
        )


@router.post("/ccf", response_model=CCFConfigResponse)
async def update_ccf_configuration(
    request: CCFConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update Credit Conversion Factor (CCF) for a facility type.
    
    Requires appropriate permissions.
    
    **Parameters:**
    - **facility_type**: Facility type to update
    - **ccf_value**: New CCF value (0-1, where 1 = 100%)
    """
    try:
        config = ead_calculation_service.update_ccf_config(
            db=db,
            facility_type=request.facility_type,
            ccf_value=request.ccf_value,
            effective_date=date.today(),
            updated_by=current_user.user_id
        )
        
        return CCFConfigResponse(
            facility_type=request.facility_type,
            ccf_value=request.ccf_value,
            updated_at=date.today().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update CCF configuration: {str(e)}"
        )


@router.get("/off-balance-sheet", response_model=List[OffBalanceSheetExposure])
async def list_off_balance_sheet_exposures(
    min_exposure: Optional[Decimal] = Query(None, ge=0, description="Minimum exposure amount"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List off-balance sheet exposures with EAD calculations.
    
    Returns instruments with undrawn commitments and their calculated off-balance sheet EAD.
    
    **Parameters:**
    - **min_exposure**: Optional minimum exposure filter
    - **skip**: Pagination offset
    - **limit**: Maximum results (1-1000)
    """
    try:
        from src.db.models import FinancialInstrument
        
        query = db.query(FinancialInstrument).filter(
            FinancialInstrument.undrawn_commitment_amount > 0
        )
        
        instruments = query.offset(skip).limit(limit).all()
        
        exposures = []
        for instrument in instruments:
            if instrument.facility_type:
                ccf = ead_calculation_service._get_ccf(db, instrument)
                undrawn = instrument.undrawn_commitment_amount or Decimal("0")
                ead_off_balance = undrawn * ccf
                
                if min_exposure is None or ead_off_balance >= min_exposure:
                    exposures.append(
                        OffBalanceSheetExposure(
                            instrument_id=instrument.instrument_id,
                            facility_type=instrument.facility_type,
                            undrawn_commitment=undrawn,
                            ccf=ccf,
                            ead_off_balance=ead_off_balance
                        )
                    )
        
        return exposures
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve off-balance sheet exposures: {str(e)}"
        )
