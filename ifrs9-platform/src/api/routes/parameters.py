"""Parameter management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid

from src.api.dependencies import get_db, get_current_user_id
from src.db.models import ParameterSet, ParameterType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/parameters", tags=["parameters"])


@router.get("", response_model=List[Dict[str, Any]])
def get_parameters(
    parameter_type: Optional[str] = Query(None),
    customer_segment: Optional[str] = Query(None),
    limit: Optional[int] = Query(100),
    db: Session = Depends(get_db)
):
    """Get all parameters with optional filters."""
    try:
        query = db.query(ParameterSet)
        
        if parameter_type:
            query = query.filter(ParameterSet.parameter_type == ParameterType[parameter_type])
        
        if customer_segment:
            query = query.filter(ParameterSet.customer_segment == customer_segment)
        
        query = query.order_by(ParameterSet.effective_date.desc())
        
        if limit:
            query = query.limit(limit)
        
        parameters = query.all()
        
        return [
            {
                "parameter_id": p.parameter_id,
                "parameter_type": p.parameter_type.value,
                "effective_date": p.effective_date.isoformat(),
                "customer_segment": p.customer_segment,
                "parameter_value": float(p.parameter_value),
                "version": p.version
            }
            for p in parameters
        ]
        
    except Exception as e:
        logger.error(f"Error getting parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=Dict[str, Any], status_code=201)
def create_parameter(
    parameter_data: Dict[str, Any],
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Create a new parameter."""
    try:
        parameter_id = str(uuid.uuid4())
        
        parameter = ParameterSet(
            parameter_id=parameter_id,
            parameter_type=ParameterType[parameter_data['parameter_type']],
            effective_date=datetime.strptime(parameter_data['effective_date'], '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(parameter_data['expiry_date'], '%Y-%m-%d').date() if parameter_data.get('expiry_date') else None,
            customer_segment=parameter_data.get('customer_segment'),
            product_type=parameter_data.get('product_type'),
            parameter_value=Decimal(str(parameter_data['parameter_value'])),
            version=parameter_data.get('version', '1.0'),
            created_by=user_id
        )
        
        db.add(parameter)
        db.commit()
        
        return {"parameter_id": parameter_id, "status": "created"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
