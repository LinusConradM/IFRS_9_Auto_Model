"""Authorization service for role-based access control (RBAC)"""
import uuid
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.models import User, Role, Permission, UserRole, RolePermission


class AuthorizationService:
    """Service for role-based access control"""
    
    def __init__(self):
        pass
    
    def create_role(
        self,
        db: Session,
        role_name: str,
        description: Optional[str] = None
    ) -> Role:
        """Create a new role"""
        role = Role(
            role_id=str(uuid.uuid4()),
            role_name=role_name,
            description=description
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    def create_permission(
        self,
        db: Session,
        permission_name: str,
        resource: str,
        action: str,
        description: Optional[str] = None
    ) -> Permission:
        """Create a new permission"""
        permission = Permission(
            permission_id=str(uuid.uuid4()),
            permission_name=permission_name,
            resource=resource,
            action=action,
            description=description
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    def assign_role_to_user(
        self,
        db: Session,
        user_id: str,
        role_id: str,
        assigned_by: Optional[str] = None
    ) -> bool:
        """Assign a role to a user"""
        # Check if assignment already exists
        existing = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        ).first()
        
        if existing:
            return False  # Already assigned
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        db.add(user_role)
        db.commit()
        return True
    
    def remove_role_from_user(
        self,
        db: Session,
        user_id: str,
        role_id: str
    ) -> bool:
        """Remove a role from a user"""
        user_role = db.query(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            )
        ).first()
        
        if not user_role:
            return False
        
        db.delete(user_role)
        db.commit()
        return True
    
    def assign_permission_to_role(
        self,
        db: Session,
        role_id: str,
        permission_id: str
    ) -> bool:
        """Assign a permission to a role"""
        # Check if assignment already exists
        existing = db.query(RolePermission).filter(
            and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            )
        ).first()
        
        if existing:
            return False  # Already assigned
        
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id
        )
        db.add(role_permission)
        db.commit()
        return True
    
    def remove_permission_from_role(
        self,
        db: Session,
        role_id: str,
        permission_id: str
    ) -> bool:
        """Remove a permission from a role"""
        role_permission = db.query(RolePermission).filter(
            and_(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            )
        ).first()
        
        if not role_permission:
            return False
        
        db.delete(role_permission)
        db.commit()
        return True
    
    def get_user_roles(self, db: Session, user_id: str) -> List[Role]:
        """Get all roles assigned to a user"""
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            return []
        
        roles = db.query(Role).filter(Role.role_id.in_(role_ids)).all()
        return roles
    
    def get_user_permissions(self, db: Session, user_id: str) -> Set[str]:
        """Get all permissions for a user (from all their roles)"""
        # Get user's roles
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            return set()
        
        # Get permissions for these roles
        role_permissions = db.query(RolePermission).filter(
            RolePermission.role_id.in_(role_ids)
        ).all()
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        if not permission_ids:
            return set()
        
        # Get permission names
        permissions = db.query(Permission).filter(
            Permission.permission_id.in_(permission_ids)
        ).all()
        
        return {p.permission_name for p in permissions}
    
    def check_permission(
        self,
        db: Session,
        user_id: str,
        permission_name: str
    ) -> bool:
        """Check if a user has a specific permission"""
        user_permissions = self.get_user_permissions(db, user_id)
        return permission_name in user_permissions
    
    def check_resource_action(
        self,
        db: Session,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """Check if a user can perform an action on a resource"""
        # Get user's roles
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        role_ids = [ur.role_id for ur in user_roles]
        
        if not role_ids:
            return False
        
        # Get permissions for these roles
        role_permissions = db.query(RolePermission).filter(
            RolePermission.role_id.in_(role_ids)
        ).all()
        permission_ids = [rp.permission_id for rp in role_permissions]
        
        if not permission_ids:
            return False
        
        # Check if any permission matches resource and action
        permission = db.query(Permission).filter(
            and_(
                Permission.permission_id.in_(permission_ids),
                Permission.resource == resource,
                Permission.action == action
            )
        ).first()
        
        return permission is not None
    
    def has_role(self, db: Session, user_id: str, role_name: str) -> bool:
        """Check if a user has a specific role"""
        user_roles = self.get_user_roles(db, user_id)
        return any(role.role_name == role_name for role in user_roles)
    
    def initialize_default_roles_and_permissions(self, db: Session):
        """Initialize default roles and permissions for the system"""
        
        # Define default roles
        default_roles = [
            ("Administrator", "Full system access"),
            ("Risk Manager", "Manage risk parameters and models"),
            ("Accountant", "View ECL calculations and generate reports"),
            ("Auditor", "Read-only access to audit trails and calculations"),
            ("Viewer", "Read-only access to dashboards and reports"),
            ("Data Steward", "Manage data imports and quality"),
            ("Model Validator", "Access model documentation and backtesting"),
            ("Executive", "Dashboard and executive reports only")
        ]
        
        # Define default permissions
        default_permissions = [
            # User management
            ("user:create", "user", "create", "Create new users"),
            ("user:read", "user", "read", "View user information"),
            ("user:update", "user", "update", "Update user information"),
            ("user:delete", "user", "delete", "Delete users"),
            
            # Parameter management
            ("parameter:create", "parameter", "create", "Create parameters"),
            ("parameter:read", "parameter", "read", "View parameters"),
            ("parameter:update", "parameter", "update", "Update parameters"),
            ("parameter:approve", "parameter", "approve", "Approve parameter changes"),
            
            # ECL calculations
            ("ecl:calculate", "ecl", "calculate", "Run ECL calculations"),
            ("ecl:read", "ecl", "read", "View ECL results"),
            ("ecl:recalculate", "ecl", "recalculate", "Trigger recalculations"),
            
            # Staging
            ("staging:read", "staging", "read", "View staging information"),
            ("staging:override", "staging", "override", "Request staging overrides"),
            ("staging:approve", "staging", "approve", "Approve staging overrides"),
            
            # Reports
            ("report:generate", "report", "generate", "Generate reports"),
            ("report:read", "report", "read", "View reports"),
            ("report:export", "report", "export", "Export reports"),
            
            # Audit
            ("audit:read", "audit", "read", "View audit trails"),
            
            # Data import
            ("import:create", "import", "create", "Upload data imports"),
            ("import:approve", "import", "approve", "Approve data imports"),
            ("import:reject", "import", "reject", "Reject data imports"),
            
            # Models
            ("model:calibrate", "model", "calibrate", "Calibrate models"),
            ("model:read", "model", "read", "View model details"),
            ("model:validate", "model", "validate", "Validate models"),
            
            # Scenarios
            ("scenario:create", "scenario", "create", "Create scenarios"),
            ("scenario:update", "scenario", "update", "Update scenarios"),
            ("scenario:approve", "scenario", "approve", "Approve scenario changes"),
        ]
        
        # Create roles
        roles = {}
        for role_name, description in default_roles:
            existing_role = db.query(Role).filter(Role.role_name == role_name).first()
            if not existing_role:
                role = self.create_role(db, role_name, description)
                roles[role_name] = role
            else:
                roles[role_name] = existing_role
        
        # Create permissions
        permissions = {}
        for perm_name, resource, action, description in default_permissions:
            existing_perm = db.query(Permission).filter(
                Permission.permission_name == perm_name
            ).first()
            if not existing_perm:
                perm = self.create_permission(db, perm_name, resource, action, description)
                permissions[perm_name] = perm
            else:
                permissions[perm_name] = existing_perm
        
        # Assign permissions to roles
        role_permission_mapping = {
            "Administrator": [  # Full access
                "user:create", "user:read", "user:update", "user:delete",
                "parameter:create", "parameter:read", "parameter:update", "parameter:approve",
                "ecl:calculate", "ecl:read", "ecl:recalculate",
                "staging:read", "staging:override", "staging:approve",
                "report:generate", "report:read", "report:export",
                "audit:read",
                "import:create", "import:approve", "import:reject",
                "model:calibrate", "model:read", "model:validate",
                "scenario:create", "scenario:update", "scenario:approve"
            ],
            "Risk Manager": [
                "parameter:create", "parameter:read", "parameter:update",
                "ecl:calculate", "ecl:read", "ecl:recalculate",
                "staging:read", "staging:override",
                "report:generate", "report:read", "report:export",
                "model:calibrate", "model:read",
                "scenario:create", "scenario:update"
            ],
            "Accountant": [
                "ecl:read",
                "staging:read",
                "report:generate", "report:read", "report:export"
            ],
            "Auditor": [
                "ecl:read",
                "staging:read",
                "report:read",
                "audit:read",
                "model:read"
            ],
            "Viewer": [
                "ecl:read",
                "staging:read",
                "report:read"
            ],
            "Data Steward": [
                "import:create",
                "parameter:read",
                "ecl:read",
                "report:read"
            ],
            "Model Validator": [
                "model:read",
                "model:validate",
                "parameter:read",
                "ecl:read",
                "audit:read"
            ],
            "Executive": [
                "report:read",
                "ecl:read"
            ]
        }
        
        # Assign permissions to roles
        for role_name, permission_names in role_permission_mapping.items():
            role = roles.get(role_name)
            if role:
                for perm_name in permission_names:
                    perm = permissions.get(perm_name)
                    if perm:
                        self.assign_permission_to_role(db, role.role_id, perm.permission_id)
        
        return roles, permissions


# Global service instance
authorization_service = AuthorizationService()
