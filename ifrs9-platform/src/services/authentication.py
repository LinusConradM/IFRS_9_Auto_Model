"""Authentication service for user management and JWT tokens"""
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.models import User, UserActivityLog


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthenticationService:
    """Service for user authentication and JWT token management"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_complexity(password: str) -> tuple[bool, str]:
        """
        Validate password complexity requirements:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password meets complexity requirements"
    
    def register_user(
        self,
        db: Session,
        username: str,
        email: str,
        password: str,
        created_by: str = "system"
    ) -> tuple[Optional[User], Optional[str]]:
        """
        Register a new user
        
        Returns:
            (User, None) if successful
            (None, error_message) if failed
        """
        # Validate password complexity
        is_valid, message = self.validate_password_complexity(password)
        if not is_valid:
            return None, message
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return None, "Username already exists"
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return None, "Email already exists"
        
        # Create new user
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            is_active=True,
            failed_login_attempts=0
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Log user creation
        self._log_activity(
            db=db,
            user_id=user.user_id,
            activity_type="USER_REGISTERED",
            description=f"User {username} registered",
            ip_address=None
        )
        
        return user, None
    
    def login(
        self,
        db: Session,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user and generate JWT tokens
        
        Returns:
            (tokens_dict, None) if successful
            (None, error_message) if failed
        """
        # Find user
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None, "Invalid username or password"
        
        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            remaining_minutes = int((user.account_locked_until - datetime.utcnow()).total_seconds() / 60)
            return None, f"Account is locked. Try again in {remaining_minutes} minutes"
        
        # Check if account is active
        if not user.is_active:
            return None, "Account is inactive"
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                db.commit()
                
                self._log_activity(
                    db=db,
                    user_id=user.user_id,
                    activity_type="ACCOUNT_LOCKED",
                    description=f"Account locked due to {MAX_FAILED_ATTEMPTS} failed login attempts",
                    ip_address=ip_address
                )
                
                return None, f"Account locked due to too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes"
            
            db.commit()
            
            self._log_activity(
                db=db,
                user_id=user.user_id,
                activity_type="LOGIN_FAILED",
                description=f"Failed login attempt ({user.failed_login_attempts}/{MAX_FAILED_ATTEMPTS})",
                ip_address=ip_address
            )
            
            return None, "Invalid username or password"
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Generate tokens
        access_token = self._create_access_token(user.user_id, user.username)
        refresh_token = self._create_refresh_token(user.user_id, user.username)
        
        # Log successful login
        self._log_activity(
            db=db,
            user_id=user.user_id,
            activity_type="LOGIN_SUCCESS",
            description=f"User {username} logged in successfully",
            ip_address=ip_address
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email
            }
        }, None
    
    def refresh_token(
        self,
        db: Session,
        refresh_token: str
    ) -> tuple[Optional[Dict[str, str]], Optional[str]]:
        """
        Refresh access token using refresh token
        
        Returns:
            (tokens_dict, None) if successful
            (None, error_message) if failed
        """
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if token_type != "refresh":
                return None, "Invalid token type"
            
            if user_id is None:
                return None, "Invalid token"
            
            # Verify user exists and is active
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user or not user.is_active:
                return None, "User not found or inactive"
            
            # Generate new access token
            access_token = self._create_access_token(user.user_id, user.username)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }, None
            
        except JWTError:
            return None, "Invalid or expired token"
    
    def logout(
        self,
        db: Session,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Logout user (in a real implementation, this would blacklist the token)
        
        Returns:
            True if successful
        """
        # Log logout
        self._log_activity(
            db=db,
            user_id=user_id,
            activity_type="LOGOUT",
            description="User logged out",
            ip_address=ip_address
        )
        
        # In a production system, you would:
        # 1. Add the token to a blacklist (Redis)
        # 2. Set expiry on the blacklist entry
        
        return True
    
    def verify_token(self, token: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Verify and decode JWT token
        
        Returns:
            (payload_dict, None) if valid
            (None, error_message) if invalid
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            token_type: str = payload.get("type")
            
            if user_id is None or token_type != "access":
                return None, "Invalid token"
            
            return {
                "user_id": user_id,
                "username": username
            }, None
            
        except JWTError as e:
            return None, f"Token validation failed: {str(e)}"
    
    def change_password(
        self,
        db: Session,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> tuple[bool, Optional[str]]:
        """
        Change user password
        
        Returns:
            (True, None) if successful
            (False, error_message) if failed
        """
        # Find user
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.verify_password(old_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password complexity
        is_valid, message = self.validate_password_complexity(new_password)
        if not is_valid:
            return False, message
        
        # Update password
        user.password_hash = self.hash_password(new_password)
        db.commit()
        
        # Log password change
        self._log_activity(
            db=db,
            user_id=user_id,
            activity_type="PASSWORD_CHANGED",
            description="User changed password",
            ip_address=None
        )
        
        return True, None
    
    def _create_access_token(self, user_id: str, username: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "username": username,
            "type": "access",
            "exp": expire
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def _create_refresh_token(self, user_id: str, username: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user_id,
            "username": username,
            "type": "refresh",
            "exp": expire
        }
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def _log_activity(
        self,
        db: Session,
        user_id: str,
        activity_type: str,
        description: str,
        ip_address: Optional[str] = None,
        request_data: Optional[Dict] = None
    ):
        """Log user activity"""
        log = UserActivityLog(
            log_id=str(uuid.uuid4()),
            user_id=user_id,
            activity_type=activity_type,
            activity_description=description,
            ip_address=ip_address,
            request_data=request_data,
            timestamp=datetime.utcnow()
        )
        db.add(log)
        db.commit()


# Global service instance
authentication_service = AuthenticationService()
