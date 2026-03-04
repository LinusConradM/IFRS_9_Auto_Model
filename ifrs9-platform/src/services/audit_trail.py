"""Audit trail service for IFRS 9 platform"""
import hashlib
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.models import AuditEntry
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AuditTrailService:
    """
    Service for logging all system actions to audit trail.
    
    Property 29: Comprehensive Audit Trail
    All system actions must create corresponding audit entries.
    
    Property 30: Audit Trail Immutability
    Audit entries cannot be modified or hard deleted once created.
    """
    
    def __init__(self, db: Session, user_id: str, ip_address: Optional[str] = None,
                 session_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.ip_address = ip_address
        self.session_id = session_id
    
    def log_classification(self, instrument_id: str, classification: str,
                          business_model: str, sppi_passed: bool,
                          rationale: str) -> AuditEntry:
        """
        Log classification action.
        
        Args:
            instrument_id: Financial instrument ID
            classification: Classification result (AMORTIZED_COST, FVOCI, FVTPL)
            business_model: Business model determination
            sppi_passed: SPPI test result
            rationale: Classification rationale
            
        Returns:
            Created audit entry
        """
        after_state = {
            'classification': classification,
            'business_model': business_model,
            'sppi_passed': sppi_passed,
            'rationale': rationale,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self._create_audit_entry(
            action='CLASSIFICATION',
            entity_type='FinancialInstrument',
            entity_id=instrument_id,
            before_state=None,
            after_state=after_state
        )
    
    def log_staging(self, instrument_id: str, from_stage: Optional[str],
                   to_stage: str, reason: str, sicr_indicators: Optional[List[str]] = None,
                   days_past_due: Optional[int] = None) -> AuditEntry:
        """
        Log staging action.
        
        Args:
            instrument_id: Financial instrument ID
            from_stage: Previous stage (None for initial assignment)
            to_stage: New stage
            reason: Reason for stage assignment/transition
            sicr_indicators: List of SICR indicators detected
            days_past_due: Days past due
            
        Returns:
            Created audit entry
        """
        before_state = {'stage': from_stage} if from_stage else None
        after_state = {
            'stage': to_stage,
            'reason': reason,
            'sicr_indicators': sicr_indicators or [],
            'days_past_due': days_past_due,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self._create_audit_entry(
            action='STAGE_TRANSITION' if from_stage else 'STAGE_ASSIGNMENT',
            entity_type='FinancialInstrument',
            entity_id=instrument_id,
            before_state=before_state,
            after_state=after_state
        )
    
    def log_ecl_calculation(self, instrument_id: str, calculation_id: str,
                           stage: str, ecl_amount: float, pd: float,
                           lgd: float, ead: float, reporting_date: str) -> AuditEntry:
        """
        Log ECL calculation action.
        
        Args:
            instrument_id: Financial instrument ID
            calculation_id: ECL calculation ID
            stage: Impairment stage
            ecl_amount: Calculated ECL amount
            pd: Probability of default used
            lgd: Loss given default used
            ead: Exposure at default used
            reporting_date: Reporting date
            
        Returns:
            Created audit entry
        """
        after_state = {
            'calculation_id': calculation_id,
            'stage': stage,
            'ecl_amount': ecl_amount,
            'pd': pd,
            'lgd': lgd,
            'ead': ead,
            'reporting_date': reporting_date,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self._create_audit_entry(
            action='ECL_CALCULATION',
            entity_type='FinancialInstrument',
            entity_id=instrument_id,
            before_state=None,
            after_state=after_state
        )
    
    def log_parameter_change(self, parameter_id: str, parameter_type: str,
                            old_value: Optional[float], new_value: float,
                            segment: Optional[str] = None) -> AuditEntry:
        """
        Log parameter change action.
        
        Args:
            parameter_id: Parameter ID
            parameter_type: Type of parameter (PD, LGD, EAD, etc.)
            old_value: Previous value (None for new parameter)
            new_value: New value
            segment: Segmentation (customer type, product type, etc.)
            
        Returns:
            Created audit entry
        """
        before_state = {'value': old_value, 'segment': segment} if old_value is not None else None
        after_state = {
            'value': new_value,
            'segment': segment,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return self._create_audit_entry(
            action='PARAMETER_UPDATE' if old_value is not None else 'PARAMETER_CREATE',
            entity_type='ParameterSet',
            entity_id=parameter_id,
            before_state=before_state,
            after_state=after_state
        )
    
    def log_user_action(self, action: str, entity_type: str, entity_id: str,
                       description: Optional[str] = None,
                       before_state: Optional[Dict] = None,
                       after_state: Optional[Dict] = None) -> AuditEntry:
        """
        Log generic user action.
        
        Args:
            action: Action performed (CREATE, UPDATE, DELETE, etc.)
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            description: Optional description
            before_state: State before action
            after_state: State after action
            
        Returns:
            Created audit entry
        """
        if description:
            if after_state is None:
                after_state = {}
            after_state['description'] = description
        
        return self._create_audit_entry(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state
        )
    
    def _create_audit_entry(self, action: str, entity_type: str, entity_id: str,
                           before_state: Optional[Dict], after_state: Optional[Dict]) -> AuditEntry:
        """
        Create audit entry with integrity hash.
        
        Property 30: Audit Trail Immutability
        Once created, audit entries cannot be modified.
        
        Args:
            action: Action performed
            entity_type: Type of entity
            entity_id: Entity ID
            before_state: State before action
            after_state: State after action
            
        Returns:
            Created audit entry
        """
        # Generate integrity hash (SHA-256)
        hash_input = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': self.user_id,
            'action': action,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'before_state': before_state,
            'after_state': after_state
        }
        
        hash_string = json.dumps(hash_input, sort_keys=True, default=str)
        integrity_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        # Create audit entry
        audit_entry = AuditEntry(
            audit_id=str(uuid.uuid4()),
            user_id=self.user_id,
            event_type=action,  # Set event_type to the action
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            ip_address=self.ip_address,
            session_id=self.session_id,
            hash=integrity_hash
        )
        
        self.db.add(audit_entry)
        self.db.flush()  # Get audit_entry.id
        
        logger.info(f"Audit entry created: {action} on {entity_type}/{entity_id} by {self.user_id}")
        
        return audit_entry
    
    def _compute_changes(self, before: Dict, after: Dict) -> Dict:
        """
        Compute changes between before and after states.
        
        Args:
            before: State before action
            after: State after action
            
        Returns:
            Dict of changes
        """
        changes = {}
        
        # Find changed fields
        all_keys = set(before.keys()) | set(after.keys())
        
        for key in all_keys:
            before_val = before.get(key)
            after_val = after.get(key)
            
            if before_val != after_val:
                changes[key] = {
                    'from': before_val,
                    'to': after_val
                }
        
        return changes
    
    def verify_integrity(self, audit_entry: AuditEntry) -> bool:
        """
        Verify integrity hash of audit entry.
        
        Property 30: Audit Trail Immutability
        Verify that audit entry has not been tampered with.
        
        Args:
            audit_entry: Audit entry to verify
            
        Returns:
            True if integrity hash is valid
        """
        # Reconstruct hash input
        hash_input = {
            'timestamp': audit_entry.timestamp.isoformat(),
            'user_id': audit_entry.user_id,
            'action': audit_entry.action,
            'entity_type': audit_entry.entity_type,
            'entity_id': audit_entry.entity_id,
            'before_state': audit_entry.before_state,
            'after_state': audit_entry.after_state
        }
        
        hash_string = json.dumps(hash_input, sort_keys=True, default=str)
        computed_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        is_valid = computed_hash == audit_entry.integrity_hash
        
        if not is_valid:
            logger.error(f"Integrity check failed for audit entry {audit_entry.id}")
        
        return is_valid


class AuditQueryService:
    """Service for querying audit trail"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def query_audit_trail(self, entity_type: Optional[str] = None,
                         entity_id: Optional[str] = None,
                         user_id: Optional[str] = None,
                         action: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         limit: int = 100) -> List[AuditEntry]:
        """
        Query audit trail with filters.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user_id: Filter by user ID
            action: Filter by action
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
            
        Returns:
            List of audit entries
        """
        query = self.db.query(AuditEntry)
        
        if entity_type:
            query = query.filter(AuditEntry.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditEntry.entity_id == entity_id)
        if user_id:
            query = query.filter(AuditEntry.user_id == user_id)
        if action:
            query = query.filter(AuditEntry.action == action)
        if start_date:
            query = query.filter(AuditEntry.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditEntry.timestamp <= end_date)
        
        query = query.order_by(AuditEntry.timestamp.desc())
        query = query.limit(limit)
        
        return query.all()
    
    def generate_audit_report(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive audit report for an entity.
        
        Args:
            entity_type: Entity type
            entity_id: Entity ID
            
        Returns:
            Dict with audit report
        """
        entries = self.query_audit_trail(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=1000
        )
        
        report = {
            'entity_type': entity_type,
            'entity_id': entity_id,
            'total_actions': len(entries),
            'actions_by_type': {},
            'users': set(),
            'timeline': []
        }
        
        for entry in entries:
            # Count actions by type
            if entry.action not in report['actions_by_type']:
                report['actions_by_type'][entry.action] = 0
            report['actions_by_type'][entry.action] += 1
            
            # Track users
            report['users'].add(entry.user_id)
            
            # Build timeline
            report['timeline'].append({
                'timestamp': entry.timestamp.isoformat(),
                'action': entry.action,
                'user_id': entry.user_id,
                'changes': entry.changes
            })
        
        report['users'] = list(report['users'])
        
        return report
