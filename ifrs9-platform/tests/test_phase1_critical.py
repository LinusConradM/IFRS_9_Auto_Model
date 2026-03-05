"""
Critical unit tests for Phase 1 services and APIs.

Tests cover:
- Authentication (register, login, logout, token validation)
- Staging Override (request, approve, reject, maker-checker)
- EAD Calculation (calculate, CCF lookup)
- Authorization checks
- Error handling
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.api.dependencies import get_db
from src.db.models import Base, User, Customer, FinancialInstrument, Role, Stage, FacilityType, CreditRating, ProductType
from src.services.authentication import authentication_service


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_phase1.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user, error = authentication_service.register_user(
        db=db_session,
        username="testuser",
        email="test@example.com",
        password="Test@123456"
    )
    if error:
        raise Exception(f"Failed to create test user: {error}")
    return user


@pytest.fixture
def test_checker(db_session):
    """Create a test checker user"""
    user, error = authentication_service.register_user(
        db=db_session,
        username="testchecker",
        email="checker@example.com",
        password="Checker@123456"
    )
    if error:
        raise Exception(f"Failed to create test checker: {error}")
    return user


@pytest.fixture
def test_customer(db_session):
    """Create a test customer"""
    customer = Customer(
        customer_id="TEST001",
        customer_name="Test Customer",
        customer_type="CORPORATE",
        industry_sector="Technology",
        credit_rating=CreditRating.BBB
    )
    db_session.add(customer)
    db_session.commit()
    return customer


@pytest.fixture
def test_instrument(db_session, test_customer):
    """Create a test financial instrument"""
    instrument = FinancialInstrument(
        instrument_id="INST001",
        customer_id=test_customer.customer_id,
        product_type=ProductType.TERM_LOAN,
        facility_type=FacilityType.TERM_LOAN,
        outstanding_balance=Decimal("100000.00"),
        undrawn_commitment=Decimal("50000.00"),
        origination_date=date(2024, 1, 1),
        maturity_date=date(2027, 1, 1),
        interest_rate=Decimal("12.0"),
        current_stage=Stage.STAGE_1,
        days_past_due=0
    )
    db_session.add(instrument)
    db_session.commit()
    return instrument


@pytest.fixture
def auth_token(test_user):
    """Get authentication token for test user"""
    token = authentication_service.create_access_token({"sub": test_user.user_id})
    return token


@pytest.fixture
def checker_token(test_checker):
    """Get authentication token for checker user"""
    token = authentication_service.create_access_token({"sub": test_checker.user_id})
    return token


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_register_user_success(db_session):
    """Test successful user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewUser@123456"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_locked"] is False


def test_register_duplicate_username(db_session, test_user):
    """Test registration with duplicate username"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "Another@123456"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_weak_password(db_session):
    """Test registration with weak password"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "weakpass",
            "email": "weak@example.com",
            "password": "weak"
        }
    )
    
    assert response.status_code == 400


def test_login_success(db_session, test_user):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "Test@123456"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data


def test_login_invalid_credentials(db_session, test_user):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401


def test_get_current_user(db_session, test_user, auth_token):
    """Test getting current user information"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_get_current_user_invalid_token(db_session):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


def test_change_password_success(db_session, test_user, auth_token):
    """Test successful password change"""
    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "old_password": "Test@123456",
            "new_password": "NewTest@123456"
        }
    )
    
    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()


# ============================================================================
# STAGING OVERRIDE TESTS
# ============================================================================

def test_request_staging_override_success(db_session, test_user, test_instrument, auth_token):
    """Test successful staging override request"""
    response = client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": test_instrument.instrument_id,
            "override_stage": "STAGE_2",
            "justification": "Customer experiencing temporary cash flow issues due to delayed receivables"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["instrument_id"] == test_instrument.instrument_id
    assert data["override_stage"] == "STAGE_2"
    assert data["status"] == "PENDING"
    assert data["requested_by"] == test_user.user_id


def test_request_staging_override_invalid_instrument(db_session, test_user, auth_token):
    """Test staging override request with invalid instrument"""
    response = client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": "INVALID_ID",
            "override_stage": "STAGE_2",
            "justification": "Test justification for invalid instrument"
        }
    )
    
    assert response.status_code == 400


def test_list_pending_overrides(db_session, test_user, test_instrument, auth_token):
    """Test listing pending staging overrides"""
    # Create an override first
    client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": test_instrument.instrument_id,
            "override_stage": "STAGE_2",
            "justification": "Test justification for pending override"
        }
    )
    
    # List pending overrides
    response = client.get(
        "/api/v1/staging/overrides/pending",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["status"] == "PENDING"


def test_approve_staging_override_success(db_session, test_user, test_checker, test_instrument, auth_token, checker_token):
    """Test successful staging override approval"""
    # Create override as maker
    create_response = client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": test_instrument.instrument_id,
            "override_stage": "STAGE_2",
            "justification": "Test justification for approval"
        }
    )
    override_id = create_response.json()["override_id"]
    
    # Approve as checker
    response = client.post(
        f"/api/v1/staging/overrides/{override_id}/approve",
        headers={"Authorization": f"Bearer {checker_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["approved_by"] == test_checker.user_id


def test_reject_staging_override_success(db_session, test_user, test_checker, test_instrument, auth_token, checker_token):
    """Test successful staging override rejection"""
    # Create override as maker
    create_response = client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": test_instrument.instrument_id,
            "override_stage": "STAGE_2",
            "justification": "Test justification for rejection"
        }
    )
    override_id = create_response.json()["override_id"]
    
    # Reject as checker
    response = client.post(
        f"/api/v1/staging/overrides/{override_id}/reject",
        headers={"Authorization": f"Bearer {checker_token}"},
        json={
            "rejection_reason": "Insufficient justification provided"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["rejected_by"] == test_checker.user_id


def test_maker_checker_same_user_violation(db_session, test_user, test_instrument, auth_token):
    """Test that maker cannot approve their own override"""
    # Create override as maker
    create_response = client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": test_instrument.instrument_id,
            "override_stage": "STAGE_2",
            "justification": "Test maker-checker violation"
        }
    )
    override_id = create_response.json()["override_id"]
    
    # Try to approve as same user
    response = client.post(
        f"/api/v1/staging/overrides/{override_id}/approve",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 400
    assert "same user" in response.json()["detail"].lower()


# ============================================================================
# EAD CALCULATION TESTS
# ============================================================================

def test_calculate_ead_success(db_session, test_user, test_instrument, auth_token):
    """Test successful EAD calculation"""
    response = client.post(
        "/api/v1/ead/calculate",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": test_instrument.instrument_id,
            "facility_type": "TERM_LOAN",
            "outstanding_balance": "100000.00",
            "undrawn_commitment": "50000.00",
            "reporting_date": date.today().isoformat()
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["instrument_id"] == test_instrument.instrument_id
    assert "total_ead" in data
    assert "ead_on_balance" in data
    assert "ead_off_balance" in data
    assert "ccf" in data


def test_get_ccf_configuration(db_session, test_user, auth_token):
    """Test getting CCF configuration"""
    response = client.get(
        "/api/v1/ead/ccf",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_ccf_specific_facility(db_session, test_user, auth_token):
    """Test getting CCF for specific facility type"""
    response = client.get(
        "/api/v1/ead/ccf?facility_type=TERM_LOAN",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "TERM_LOAN" in data


def test_update_ccf_configuration(db_session, test_user, auth_token):
    """Test updating CCF configuration"""
    response = client.post(
        "/api/v1/ead/ccf",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "facility_type": "TERM_LOAN",
            "ccf_value": "0.75"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["facility_type"] == "TERM_LOAN"
    assert float(data["ccf_value"]) == 0.75


def test_list_off_balance_sheet_exposures(db_session, test_user, test_instrument, auth_token):
    """Test listing off-balance sheet exposures"""
    response = client.get(
        "/api/v1/ead/off-balance-sheet",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# AUTHORIZATION TESTS
# ============================================================================

def test_unauthorized_access_no_token(db_session):
    """Test that endpoints require authentication"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_unauthorized_access_invalid_token(db_session):
    """Test that invalid tokens are rejected"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_invalid_json_payload(db_session, test_user, auth_token):
    """Test handling of invalid JSON payload"""
    response = client.post(
        "/api/v1/staging/overrides",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        },
        content="invalid json"
    )
    
    assert response.status_code == 422


def test_missing_required_fields(db_session, test_user, auth_token):
    """Test handling of missing required fields"""
    response = client.post(
        "/api/v1/staging/overrides",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "instrument_id": "INST001"
            # Missing override_stage and justification
        }
    )
    
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
