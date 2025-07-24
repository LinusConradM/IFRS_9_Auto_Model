import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

# compile JSONB as JSON for SQLite in tests
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, 'sqlite')
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return 'JSON'


@pytest.fixture(autouse=True)
def setup_sqlite_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    # reload modules to pick up in-memory settings
    import sys
    for m in list(sys.modules):
        if m.startswith('db.') or m.startswith('api.') or m.startswith('services.instrument_upload_service'):
            sys.modules.pop(m, None)


@pytest.fixture
def client():
    from db.session import engine, Base
    import db.models  # load models
    from api.main import app

    Base.metadata.create_all(bind=engine)
    return TestClient(app)


def minimal_payload():
    return {
        "loan_id": "L1",
        "borrower_id": "B1",
        "loan_amount_original": "100.00",
        "loan_amount_outstanding": "80.00",
        "currency": "USD",
        "drawdown_date": "2023-01-01",
        "maturity_date": "2023-02-01",
        "business_model_objective": "hold_to_collect",
        "business_model_assessment": "Hold",
        "sppi_test_passed": "Pass",
        "classification_category": "Amortized Cost",
        "measurement_category": "amortised_cost",
    }

def test_validate_ifrs9_success(client):
    payload = minimal_payload()
    res = client.post('/validate_ifrs9', json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data['loan_id'] == payload['loan_id']
    assert data['pd_12m'] is None


def test_validate_ifrs9_fails_on_extra(client):
    payload = minimal_payload()
    payload['unexpected'] = 123
    res = client.post('/validate_ifrs9', json=payload)
    assert res.status_code == 422


def test_validate_ifrs9_fails_on_bounds(client):
    payload = minimal_payload()
    payload['pd_12m'] = -0.2
    res = client.post('/validate_ifrs9', json=payload)
    assert res.status_code == 422