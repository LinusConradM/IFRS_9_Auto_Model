"""FastAPI dependencies for dependency injection"""
from typing import Generator
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id() -> str:
    """
    Get current user ID from request context.
    
    For MVP, returns a default user.
    In production, this would extract user from JWT token.
    
    Returns:
        User ID
    """
    # TODO: Implement JWT authentication
    return "system_user"


def get_client_ip() -> str:
    """
    Get client IP address from request.
    
    For MVP, returns localhost.
    In production, would extract from request headers.
    
    Returns:
        IP address
    """
    # TODO: Extract from request
    return "127.0.0.1"
