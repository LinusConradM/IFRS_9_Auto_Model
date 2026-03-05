"""Macroeconomic scenario API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from src.api.dependencies import get_db, get_current_user_id
from src.db.models import MacroScenario
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])


@router.get("", response_model=List[Dict[str, Any]])
def get_scenarios(
    effective_date: Optional[str] = Query(None, description="Filter by effective date"),
    limit: Optional[int] = Query(100, description="Limit number of results"),
    db: Session = Depends(get_db)
):
    """Get all macroeconomic scenarios."""
    try:
        query = db.query(MacroScenario)
        
        if effective_date:
            eff_date = datetime.strptime(effective_date, '%Y-%m-%d').date()
            query = query.filter(MacroScenario.effective_date == eff_date)
        
        query = query.order_by(MacroScenario.effective_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        scenarios = query.all()
        
        return [
            {
                "scenario_id": s.scenario_id,
                "scenario_name": s.scenario_name,
                "effective_date": s.effective_date.isoformat(),
                "probability_weight": float(s.probability_weight),
                "gdp_growth_rate": s.gdp_growth_rate,
                "inflation_rate": s.inflation_rate,
                "created_by": s.created_by
            }
            for s in scenarios
        ]
        
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_scenario(
    scenario_data: Dict[str, Any],
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new macroeconomic scenario."""
    try:
        scenario_id = str(uuid.uuid4())
        
        scenario = MacroScenario(
            scenario_id=scenario_id,
            scenario_name=scenario_data['scenario_name'],
            effective_date=datetime.strptime(scenario_data['effective_date'], '%Y-%m-%d').date(),
            probability_weight=Decimal(str(scenario_data['probability_weight'])),
            gdp_growth_rate=scenario_data.get('gdp_growth_rate'),
            inflation_rate=scenario_data.get('inflation_rate'),
            created_by=user_id
        )
        
        db.add(scenario)
        db.commit()
        
        return {"scenario_id": scenario_id, "status": "created"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
