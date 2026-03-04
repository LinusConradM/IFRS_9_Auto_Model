"""Audit trail API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.api.dependencies import get_db
from src.services.audit_trail import AuditQueryService
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/entries", response_model=List[Dict[str, Any]])
def get_audit_entries(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get audit trail entries with filters.
    
    Args:
        entity_type: Filter by entity type (optional)
        entity_id: Filter by entity ID (optional)
        user_id: Filter by user ID (optional)
        action: Filter by action (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of audit entries
    """
    try:
        audit_service = AuditQueryService(db)
        entries = audit_service.query_audit_trail(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return [
            {
                'id': e.id,
                'timestamp': e.timestamp.isoformat(),
                'user_id': e.user_id,
                'action': e.action,
                'entity_type': e.entity_type,
                'entity_id': e.entity_id,
                'before_state': e.before_state,
                'after_state': e.after_state,
                'changes': e.changes,
                'ip_address': e.ip_address,
                'session_id': e.session_id
            }
            for e in entries
        ]
        
    except Exception as e:
        logger.error(f"Error getting audit entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entries/{audit_id}", response_model=Dict[str, Any])
def get_audit_entry(
    audit_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific audit entry details.
    
    Args:
        audit_id: Audit entry ID
        db: Database session
        
    Returns:
        Audit entry details
    """
    try:
        from src.db.models import AuditEntry
        
        entry = db.query(AuditEntry).filter(AuditEntry.id == audit_id).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"Audit entry {audit_id} not found")
        
        return {
            'id': entry.id,
            'timestamp': entry.timestamp.isoformat(),
            'user_id': entry.user_id,
            'action': entry.action,
            'entity_type': entry.entity_type,
            'entity_id': entry.entity_id,
            'before_state': entry.before_state,
            'after_state': entry.after_state,
            'changes': entry.changes,
            'ip_address': entry.ip_address,
            'session_id': entry.session_id,
            'integrity_hash': entry.integrity_hash
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instrument/{instrument_id}", response_model=Dict[str, Any])
def get_instrument_audit_trail(
    instrument_id: str,
    db: Session = Depends(get_db)
):
    """
    Get complete audit trail for a financial instrument.
    
    Args:
        instrument_id: Instrument ID
        db: Database session
        
    Returns:
        Audit report for instrument
    """
    try:
        audit_service = AuditQueryService(db)
        report = audit_service.generate_audit_report(
            entity_type='FinancialInstrument',
            entity_id=instrument_id
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error getting instrument audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
def get_user_audit_trail(
    user_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get audit trail for a specific user.
    
    Args:
        user_id: User ID
        limit: Maximum number of results
        db: Database session
        
    Returns:
        List of audit entries for user
    """
    try:
        audit_service = AuditQueryService(db)
        entries = audit_service.query_audit_trail(
            user_id=user_id,
            limit=limit
        )
        
        return [
            {
                'id': e.id,
                'timestamp': e.timestamp.isoformat(),
                'action': e.action,
                'entity_type': e.entity_type,
                'entity_id': e.entity_id,
                'changes': e.changes
            }
            for e in entries
        ]
        
    except Exception as e:
        logger.error(f"Error getting user audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))
