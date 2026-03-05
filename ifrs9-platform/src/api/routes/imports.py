"""Data import API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.api.dependencies import get_db, get_current_user_id
from src.services.data_import import DataImportService
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/imports", tags=["imports"])


@router.post("/loan-portfolio", response_model=Dict[str, Any])
async def import_loan_portfolio(
    file: UploadFile = File(...),
    auto_approve: bool = False,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Import loan portfolio data from CSV or JSON file.
    
    Args:
        file: Uploaded file (CSV or JSON)
        auto_approve: If True, import directly; if False, stage for approval
        db: Database session
        user_id: Current user ID
        
    Returns:
        Import result with statistics
    """
    try:
        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # Determine file format
        file_format = 'csv' if file.filename.endswith('.csv') else 'json'
        
        logger.info(f"Importing loan portfolio: {file.filename}, format={file_format}, user={user_id}, auto_approve={auto_approve}")
        
        # Import data
        import_service = DataImportService(db)
        result = import_service.import_loan_portfolio(
            file_content=file_content,
            file_format=file_format,
            auto_approve=auto_approve,
            user_id=user_id,
            filename=file.filename
        )
        
        return {
            'import_id': result.import_id,
            'status': result.status,
            'records_processed': result.records_processed,
            'records_imported': result.records_imported,
            'records_failed': result.records_failed,
            'errors': result.errors[:100]  # Limit to first 100 errors
        }
        
    except Exception as e:
        logger.error(f"Error importing loan portfolio: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/customer-data", response_model=Dict[str, Any])
async def import_customer_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Import customer master data from CSV or JSON file.
    
    Args:
        file: Uploaded file (CSV or JSON)
        db: Database session
        user_id: Current user ID
        
    Returns:
        Import result with statistics
    """
    try:
        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # Determine file format
        file_format = 'csv' if file.filename.endswith('.csv') else 'json'
        
        logger.info(f"Importing customer data: {file.filename}, user={user_id}")
        
        # Import data
        import_service = DataImportService(db)
        result = import_service.import_customer_data(
            file_content=file_content,
            file_format=file_format
        )
        
        return {
            'import_id': result.import_id,
            'status': result.status,
            'records_processed': result.records_processed,
            'records_imported': result.records_imported,
            'records_failed': result.records_failed,
            'errors': result.errors[:100]
        }
        
    except Exception as e:
        logger.error(f"Error importing customer data: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/macro-scenarios", response_model=Dict[str, Any])
async def import_macro_scenarios(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Import macroeconomic scenario data from CSV or JSON file.
    
    Args:
        file: Uploaded file (CSV or JSON)
        db: Database session
        user_id: Current user ID
        
    Returns:
        Import result with statistics
    """
    try:
        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # Determine file format
        file_format = 'csv' if file.filename.endswith('.csv') else 'json'
        
        logger.info(f"Importing macro scenarios: {file.filename}, user={user_id}")
        
        # Import data
        import_service = DataImportService(db)
        result = import_service.import_macro_data(
            file_content=file_content,
            file_format=file_format
        )
        
        return {
            'import_id': result.import_id,
            'status': result.status,
            'records_processed': result.records_processed,
            'records_imported': result.records_imported,
            'records_failed': result.records_failed,
            'errors': result.errors[:100]
        }
        
    except Exception as e:
        logger.error(f"Error importing macro scenarios: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{import_id}", response_model=Dict[str, Any])
async def get_import_status(
    import_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get status of an import batch.
    
    Args:
        import_id: Import batch ID
        db: Database session
        user_id: Current user ID
        
    Returns:
        Import status details
    """
    try:
        import_service = DataImportService(db)
        status = import_service.get_import_status(import_id)
        return status
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{import_id}/approve", response_model=Dict[str, Any])
async def approve_import(
    import_id: str,
    notes: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Approve a pending import and commit data to main tables.
    
    Args:
        import_id: Import batch ID
        notes: Optional approval notes
        db: Database session
        user_id: Current user ID
        
    Returns:
        Approval result
    """
    try:
        logger.info(f"Approving import {import_id} by user {user_id}")
        
        import_service = DataImportService(db)
        result = import_service.approve_import(import_id, user_id, notes)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{import_id}/reject", response_model=Dict[str, Any])
async def reject_import(
    import_id: str,
    notes: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Reject a pending import and delete staged data.
    
    Args:
        import_id: Import batch ID
        notes: Optional rejection notes
        db: Database session
        user_id: Current user ID
        
    Returns:
        Rejection result
    """
    try:
        logger.info(f"Rejecting import {import_id} by user {user_id}")
        
        import_service = DataImportService(db)
        result = import_service.reject_import(import_id, user_id, notes)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting import: {e}")
        raise HTTPException(status_code=500, detail=str(e))
