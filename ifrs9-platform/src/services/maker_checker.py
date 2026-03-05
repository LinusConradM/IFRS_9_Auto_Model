"""Maker-Checker service for approval workflows"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.db.models import ApprovalWorkflow, User


class MakerCheckerService:
    """Service for maker-checker approval workflows"""
    
    def __init__(self):
        pass
    
    def request_approval(
        self,
        db: Session,
        workflow_type: str,
        request_data: Dict[str, Any],
        requester_id: str
    ) -> ApprovalWorkflow:
        """
        Create a new approval request
        
        Args:
            workflow_type: Type of workflow (PARAMETER_CHANGE, STAGING_OVERRIDE, etc.)
            request_data: Data for the approval request
            requester_id: ID of the user requesting approval
        
        Returns:
            ApprovalWorkflow object
        """
        workflow = ApprovalWorkflow(
            workflow_id=str(uuid.uuid4()),
            workflow_type=workflow_type,
            request_data=request_data,
            requester_id=requester_id,
            status="PENDING"
        )
        
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        
        return workflow
    
    def approve_request(
        self,
        db: Session,
        workflow_id: str,
        approver_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Approve an approval request
        
        Returns:
            (True, None) if successful
            (False, error_message) if failed
        """
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.workflow_id == workflow_id
        ).first()
        
        if not workflow:
            return False, "Workflow not found"
        
        if workflow.status != "PENDING":
            return False, f"Workflow is already {workflow.status}"
        
        # Check that approver is not the same as requester
        if workflow.requester_id == approver_id:
            return False, "Requester cannot approve their own request"
        
        # Update workflow
        workflow.status = "APPROVED"
        workflow.approver_id = approver_id
        workflow.approval_date = datetime.utcnow()
        
        db.commit()
        db.refresh(workflow)
        
        return True, None
    
    def reject_request(
        self,
        db: Session,
        workflow_id: str,
        approver_id: str,
        rejection_reason: str
    ) -> tuple[bool, Optional[str]]:
        """
        Reject an approval request
        
        Returns:
            (True, None) if successful
            (False, error_message) if failed
        """
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.workflow_id == workflow_id
        ).first()
        
        if not workflow:
            return False, "Workflow not found"
        
        if workflow.status != "PENDING":
            return False, f"Workflow is already {workflow.status}"
        
        # Update workflow
        workflow.status = "REJECTED"
        workflow.approver_id = approver_id
        workflow.approval_date = datetime.utcnow()
        workflow.rejection_reason = rejection_reason
        
        db.commit()
        db.refresh(workflow)
        
        return True, None
    
    def get_pending_approvals(
        self,
        db: Session,
        workflow_type: Optional[str] = None,
        requester_id: Optional[str] = None
    ) -> List[ApprovalWorkflow]:
        """
        Get all pending approval requests
        
        Args:
            workflow_type: Filter by workflow type (optional)
            requester_id: Filter by requester (optional)
        
        Returns:
            List of pending ApprovalWorkflow objects
        """
        query = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.status == "PENDING"
        )
        
        if workflow_type:
            query = query.filter(ApprovalWorkflow.workflow_type == workflow_type)
        
        if requester_id:
            query = query.filter(ApprovalWorkflow.requester_id == requester_id)
        
        return query.order_by(ApprovalWorkflow.request_date.desc()).all()
    
    def get_workflow_history(
        self,
        db: Session,
        workflow_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[ApprovalWorkflow]:
        """
        Get workflow history
        
        Args:
            workflow_type: Filter by workflow type (optional)
            status: Filter by status (optional)
            limit: Maximum number of records to return
        
        Returns:
            List of ApprovalWorkflow objects
        """
        query = db.query(ApprovalWorkflow)
        
        if workflow_type:
            query = query.filter(ApprovalWorkflow.workflow_type == workflow_type)
        
        if status:
            query = query.filter(ApprovalWorkflow.status == status)
        
        return query.order_by(ApprovalWorkflow.request_date.desc()).limit(limit).all()
    
    def get_workflow_by_id(
        self,
        db: Session,
        workflow_id: str
    ) -> Optional[ApprovalWorkflow]:
        """Get a specific workflow by ID"""
        return db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.workflow_id == workflow_id
        ).first()
    
    def get_user_pending_approvals_count(
        self,
        db: Session,
        user_id: str
    ) -> int:
        """Get count of pending approvals for a user"""
        return db.query(ApprovalWorkflow).filter(
            and_(
                ApprovalWorkflow.requester_id == user_id,
                ApprovalWorkflow.status == "PENDING"
            )
        ).count()
    
    def cancel_request(
        self,
        db: Session,
        workflow_id: str,
        requester_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Cancel a pending approval request (only by requester)
        
        Returns:
            (True, None) if successful
            (False, error_message) if failed
        """
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.workflow_id == workflow_id
        ).first()
        
        if not workflow:
            return False, "Workflow not found"
        
        if workflow.requester_id != requester_id:
            return False, "Only the requester can cancel the request"
        
        if workflow.status != "PENDING":
            return False, f"Cannot cancel workflow with status {workflow.status}"
        
        # Update workflow
        workflow.status = "CANCELLED"
        workflow.rejection_reason = "Cancelled by requester"
        
        db.commit()
        
        return True, None


# Global service instance
maker_checker_service = MakerCheckerService()
