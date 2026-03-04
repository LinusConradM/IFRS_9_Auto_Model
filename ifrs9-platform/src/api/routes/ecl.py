"""ECL calculation API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import date
from decimal import Decimal

from src.api.dependencies import get_db, get_current_user_id, get_client_ip
from src.services.ecl_engine import ECLCalculationService
from src.services.audit_trail import AuditTrailService
from src.db.models import FinancialInstrument, ECLCalculation
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/ecl", tags=["ecl"])


class CalculateECLRequest(BaseModel):
    """Request to calculate ECL for an instrument"""
    instrument_id: str
    reporting_date: date
    scenarios: Optional[List[Dict[str, Any]]] = None


class CalculateECLResponse(BaseModel):
    """ECL calculation result"""
    calculation_id: str
    instrument_id: str
    stage: str
    ecl_amount: float
    time_horizon: str
    pd: float
    lgd: float
    ead: float
    scenario_results: Dict[str, float]


@router.post("/calculate", response_model=CalculateECLResponse)
def calculate_ecl(
    request: CalculateECLRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    ip_address: str = Depends(get_client_ip)
):
    """
    Calculate ECL for a financial instrument.
    
    Calculates 12-month ECL for Stage 1 or Lifetime ECL for Stage 2/3.
    
    Args:
        request: ECL calculation request
        db: Database session
        user_id: Current user ID
        ip_address: Client IP address
        
    Returns:
        ECL calculation result
    """
    try:
        # Get instrument
        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == request.instrument_id
        ).first()
        
        if not instrument:
            raise HTTPException(status_code=404, detail=f"Instrument {request.instrument_id} not found")
        
        logger.info(f"Calculating ECL for instrument {request.instrument_id}, stage {instrument.current_stage.value}")
        
        # Calculate ECL
        ecl_service = ECLCalculationService()
        result = ecl_service.calculate_ecl(
            instrument=instrument,
            stage=instrument.current_stage,
            reporting_date=request.reporting_date,
            scenarios=request.scenarios
        )
        
        # Save calculation to database
        ecl_calculation = ECLCalculation(
            calculation_id=result.calculation_id,
            instrument_id=instrument.instrument_id,
            reporting_date=request.reporting_date,
            stage=instrument.current_stage,
            ecl_amount=result.ecl_amount,
            pd=result.pd,
            lgd=result.lgd,
            ead=result.ead,
            discount_rate=ecl_service.default_discount_rate,
            calculation_method='STANDARD',
            time_horizon=result.time_horizon
        )
        
        db.add(ecl_calculation)
        db.commit()
        
        # Log to audit trail
        audit_service = AuditTrailService(db, user_id, ip_address)
        audit_service.log_ecl_calculation(
            instrument_id=request.instrument_id,
            calculation_id=result.calculation_id,
            stage=instrument.current_stage.value,
            ecl_amount=float(result.ecl_amount),
            pd=float(result.pd),
            lgd=float(result.lgd),
            ead=float(result.ead),
            reporting_date=request.reporting_date.isoformat()
        )
        db.commit()
        
        return CalculateECLResponse(
            calculation_id=result.calculation_id,
            instrument_id=request.instrument_id,
            stage=instrument.current_stage.value,
            ecl_amount=float(result.ecl_amount),
            time_horizon=result.time_horizon,
            pd=float(result.pd),
            lgd=float(result.lgd),
            ead=float(result.ead),
            scenario_results={k: float(v) for k, v in result.scenario_results.items()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ECL: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class CalculatePortfolioRequest(BaseModel):
    """Request to calculate ECL for portfolio"""
    reporting_date: date
    instrument_ids: Optional[List[str]] = None  # If None, calculate for all active instruments


@router.post("/calculate-portfolio", response_model=Dict[str, Any])
def calculate_portfolio_ecl(
    request: CalculatePortfolioRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Calculate ECL for portfolio of instruments.
    
    Args:
        request: Portfolio calculation request
        db: Database session
        user_id: Current user ID
        
    Returns:
        Portfolio ECL calculation summary
    """
    try:
        # Get instruments
        query = db.query(FinancialInstrument).filter(
            FinancialInstrument.status == 'ACTIVE'
        )
        
        if request.instrument_ids:
            query = query.filter(FinancialInstrument.instrument_id.in_(request.instrument_ids))
        
        instruments = query.all()
        
        logger.info(f"Calculating ECL for {len(instruments)} instruments")
        
        # Calculate ECL for each instrument
        ecl_service = ECLCalculationService()
        results = ecl_service.recalculate_portfolio(instruments, request.reporting_date)
        
        # Calculate totals
        total_ecl = Decimal("0")
        stage_totals = {
            'STAGE_1': Decimal("0"),
            'STAGE_2': Decimal("0"),
            'STAGE_3': Decimal("0")
        }
        
        for instrument_id, result in results.items():
            total_ecl += result.ecl_amount
            
            # Get instrument stage
            instrument = next(i for i in instruments if i.instrument_id == instrument_id)
            stage_totals[instrument.current_stage.value] += result.ecl_amount
        
        return {
            'reporting_date': request.reporting_date.isoformat(),
            'instruments_calculated': len(results),
            'total_ecl': float(total_ecl),
            'stage_totals': {k: float(v) for k, v in stage_totals.items()},
            'user_id': user_id
        }
        
    except Exception as e:
        logger.error(f"Error calculating portfolio ECL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculations", response_model=List[Dict[str, Any]])
def get_ecl_calculations(
    instrument_id: str = None,
    reporting_date: date = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get ECL calculation history.
    
    Args:
        instrument_id: Filter by instrument ID (optional)
        reporting_date: Filter by reporting date (optional)
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of ECL calculations
    """
    try:
        query = db.query(ECLCalculation)
        
        if instrument_id:
            # Filter directly by instrument_id string, not by instrument.id
            query = query.filter(ECLCalculation.instrument_id == instrument_id)
        
        if reporting_date:
            query = query.filter(ECLCalculation.reporting_date == reporting_date)
        
        query = query.order_by(ECLCalculation.calculation_timestamp.desc())
        query = query.limit(limit)
        
        calculations = query.all()
        
        return [
            {
                'id': c.calculation_id,
                'instrument_id': c.instrument.instrument_id,
                'reporting_date': c.reporting_date.isoformat(),
                'stage': c.stage.value,
                'ecl_amount': float(c.ecl_amount),
                'pd': float(c.pd),
                'lgd': float(c.lgd),
                'ead': float(c.ead),
                'created_at': c.calculation_timestamp.isoformat() if c.calculation_timestamp else None
            }
            for c in calculations
        ]
        
    except Exception as e:
        logger.error(f"Error getting ECL calculations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calculations/{calculation_id}", response_model=Dict[str, Any])
def get_ecl_calculation(
    calculation_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific ECL calculation details.
    
    Args:
        calculation_id: Calculation ID
        db: Database session
        
    Returns:
        ECL calculation details
    """
    try:
        calculation = db.query(ECLCalculation).filter(
            ECLCalculation.calculation_id == calculation_id
        ).first()
        
        if not calculation:
            raise HTTPException(status_code=404, detail=f"Calculation {calculation_id} not found")
        
        return {
            'id': calculation.calculation_id,
            'instrument_id': calculation.instrument.instrument_id,
            'reporting_date': calculation.reporting_date.isoformat(),
            'stage': calculation.stage.value,
            'ecl_amount': float(calculation.ecl_amount),
            'pd': float(calculation.pd),
            'lgd': float(calculation.lgd),
            'ead': float(calculation.ead),
            'discount_rate': float(calculation.discount_rate) if calculation.discount_rate else None,
            'calculation_method': calculation.calculation_method,
            'time_horizon': calculation.time_horizon,
            'created_at': calculation.calculation_timestamp.isoformat() if calculation.calculation_timestamp else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ECL calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
