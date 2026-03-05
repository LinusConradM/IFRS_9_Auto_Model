"""Reporting API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from src.api.dependencies import get_db
from src.db.models import (
    FinancialInstrument, ECLCalculation, StageTransition,
    Customer, Stage, InstrumentStatus
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reporting"])


@router.get("/portfolio-summary", response_model=Dict[str, Any])
def get_portfolio_summary(
    reporting_date: Optional[str] = Query(None, description="Reporting date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get portfolio summary metrics.
    
    Returns:
        Portfolio summary with exposure, ECL, coverage ratios
    """
    try:
        # Use provided date or current date
        report_date = datetime.strptime(reporting_date, '%Y-%m-%d').date() if reporting_date else date.today()
        
        # Get active instruments
        instruments = db.query(FinancialInstrument).filter(
            FinancialInstrument.status == InstrumentStatus.ACTIVE
        ).all()
        
        # Calculate totals
        total_instruments = len(instruments)
        total_exposure = sum(float(i.principal_amount) for i in instruments)
        total_outstanding = sum(float(i.outstanding_balance) if i.outstanding_balance else 0 for i in instruments)
        
        # Get latest ECL calculations
        latest_ecl = db.query(
            func.sum(ECLCalculation.ecl_amount).label('total_ecl')
        ).filter(
            ECLCalculation.reporting_date == report_date
        ).first()
        
        total_ecl = float(latest_ecl.total_ecl) if latest_ecl and latest_ecl.total_ecl else 0
        
        # Stage distribution
        stage_dist = {}
        for stage in Stage:
            count = sum(1 for i in instruments if i.current_stage == stage)
            exposure = sum(float(i.principal_amount) for i in instruments if i.current_stage == stage)
            stage_dist[stage.value] = {
                "count": count,
                "exposure": exposure
            }
        
        # Coverage ratio
        coverage_ratio = (total_ecl / total_outstanding * 100) if total_outstanding > 0 else 0
        
        return {
            "reporting_date": report_date.isoformat(),
            "total_instruments": total_instruments,
            "total_exposure": total_exposure,
            "total_outstanding": total_outstanding,
            "total_ecl": total_ecl,
            "coverage_ratio": coverage_ratio,
            "stage_distribution": stage_dist
        }
        
    except Exception as e:
        logger.error(f"Error generating portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ecl-reconciliation", response_model=Dict[str, Any])
def get_ecl_reconciliation(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get ECL reconciliation report showing movements.
    
    Returns:
        ECL reconciliation with opening, movements, and closing balances
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Opening ECL
        opening_ecl_query = db.query(
            func.sum(ECLCalculation.ecl_amount).label('total')
        ).filter(
            ECLCalculation.reporting_date == start
        ).first()
        
        opening_ecl = float(opening_ecl_query.total) if opening_ecl_query and opening_ecl_query.total else 0
        
        # Closing ECL
        closing_ecl_query = db.query(
            func.sum(ECLCalculation.ecl_amount).label('total')
        ).filter(
            ECLCalculation.reporting_date == end
        ).first()
        
        closing_ecl = float(closing_ecl_query.total) if closing_ecl_query and closing_ecl_query.total else 0
        
        # Calculate movement
        net_movement = closing_ecl - opening_ecl
        
        # Get stage transitions during period
        transitions = db.query(StageTransition).filter(
            StageTransition.transition_date >= start,
            StageTransition.transition_date <= end
        ).all()
        
        stage_movements = {
            "stage_1_to_2": len([t for t in transitions if t.from_stage == Stage.STAGE_1 and t.to_stage == Stage.STAGE_2]),
            "stage_2_to_1": len([t for t in transitions if t.from_stage == Stage.STAGE_2 and t.to_stage == Stage.STAGE_1]),
            "stage_2_to_3": len([t for t in transitions if t.from_stage == Stage.STAGE_2 and t.to_stage == Stage.STAGE_3]),
            "stage_1_to_3": len([t for t in transitions if t.from_stage == Stage.STAGE_1 and t.to_stage == Stage.STAGE_3])
        }
        
        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "opening_ecl": opening_ecl,
            "closing_ecl": closing_ecl,
            "net_movement": net_movement,
            "stage_movements": stage_movements,
            "reconciliation_complete": True
        }
        
    except Exception as e:
        logger.error(f"Error generating ECL reconciliation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regulatory/monthly-impairment", response_model=Dict[str, Any])
def get_monthly_impairment_report(
    reporting_date: str = Query(..., description="Reporting date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Generate monthly impairment provision report for Bank of Uganda.
    
    Returns:
        Monthly impairment report with ECL by stage and coverage ratios
    """
    try:
        report_date = datetime.strptime(reporting_date, '%Y-%m-%d').date()
        
        # Get ECL by stage
        ecl_by_stage = {}
        for stage in Stage:
            ecl_query = db.query(
                func.sum(ECLCalculation.ecl_amount).label('total'),
                func.count(ECLCalculation.calculation_id).label('count')
            ).filter(
                ECLCalculation.reporting_date == report_date,
                ECLCalculation.stage == stage
            ).first()
            
            ecl_by_stage[stage.value] = {
                "ecl_amount": float(ecl_query.total) if ecl_query and ecl_query.total else 0,
                "instrument_count": ecl_query.count if ecl_query else 0
            }
        
        # Get exposure by stage
        exposure_by_stage = {}
        for stage in Stage:
            instruments = db.query(FinancialInstrument).filter(
                FinancialInstrument.current_stage == stage,
                FinancialInstrument.status == InstrumentStatus.ACTIVE
            ).all()
            
            total_exposure = sum(float(i.principal_amount) for i in instruments)
            exposure_by_stage[stage.value] = total_exposure
        
        # Calculate coverage ratios
        coverage_ratios = {}
        for stage in Stage:
            exposure = exposure_by_stage.get(stage.value, 0)
            ecl = ecl_by_stage.get(stage.value, {}).get('ecl_amount', 0)
            coverage_ratios[stage.value] = (ecl / exposure * 100) if exposure > 0 else 0
        
        return {
            "report_type": "Monthly Impairment Provision Report",
            "reporting_date": report_date.isoformat(),
            "ecl_by_stage": ecl_by_stage,
            "exposure_by_stage": exposure_by_stage,
            "coverage_ratios": coverage_ratios,
            "total_ecl": sum(s['ecl_amount'] for s in ecl_by_stage.values()),
            "total_exposure": sum(exposure_by_stage.values())
        }
        
    except Exception as e:
        logger.error(f"Error generating monthly impairment report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-metrics", response_model=Dict[str, Any])
def get_dashboard_metrics(
    db: Session = Depends(get_db)
):
    """
    Get real-time dashboard metrics.
    
    Returns:
        Dashboard metrics for visualization
    """
    try:
        # Active instruments
        active_instruments = db.query(FinancialInstrument).filter(
            FinancialInstrument.status == InstrumentStatus.ACTIVE
        ).all()
        
        total_instruments = len(active_instruments)
        total_exposure = sum(float(i.principal_amount) for i in active_instruments)
        
        # Latest ECL
        latest_ecl = db.query(
            func.sum(ECLCalculation.ecl_amount).label('total')
        ).first()
        
        total_ecl = float(latest_ecl.total) if latest_ecl and latest_ecl.total else 0
        
        # Stage distribution
        stage_counts = {}
        for stage in Stage:
            count = sum(1 for i in active_instruments if i.current_stage == stage)
            stage_counts[stage.value] = count
        
        # High risk instruments (Stage 3 or DPD > 90)
        high_risk = sum(1 for i in active_instruments if i.current_stage == Stage.STAGE_3 or i.days_past_due > 90)
        
        return {
            "total_instruments": total_instruments,
            "total_exposure": total_exposure,
            "total_ecl": total_ecl,
            "coverage_ratio": (total_ecl / total_exposure * 100) if total_exposure > 0 else 0,
            "stage_distribution": stage_counts,
            "high_risk_count": high_risk
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
