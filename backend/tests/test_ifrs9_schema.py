import pytest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from db.schemas import IFRS9InstrumentSchema


def test_ifrs9_schema_minimal_required_fields():
    data = {
        "loan_id": "L1",
        "borrower_id": "B1",
        "loan_amount_original": Decimal("100.00"),
        "loan_amount_outstanding": Decimal("80.00"),
        "currency": "USD",
        "drawdown_date": date(2023, 1, 1),
        "maturity_date": date(2024, 1, 1),
        "business_model_objective": "hold_to_collect",
        "business_model_assessment": "Hold",
        "sppi_test_passed": "Pass",
        "classification_category": "Amortized Cost",
        "measurement_category": "amortised_cost",
    }
    schema = IFRS9InstrumentSchema(**data)
    assert schema.loan_id == "L1"
    assert schema.loan_amount_original == Decimal("100.00")
    assert schema.sppi_test_passed == "Pass"


def test_ifrs9_schema_disallows_extra_fields():
    data = {
        "loan_id": "L1",
        "borrower_id": "B1",
        "loan_amount_original": Decimal("100.00"),
        "loan_amount_outstanding": Decimal("80.00"),
        "currency": "USD",
        "drawdown_date": date(2023, 1, 1),
        "maturity_date": date(2024, 1, 1),
        "business_model_objective": "hold_to_collect",
        "business_model_assessment": "Hold",
        "sppi_test_passed": "Pass",
        "classification_category": "Amortized Cost",
        "measurement_category": "amortised_cost",
        "extra_field": "not_allowed",
    }
    with pytest.raises(ValidationError):
        IFRS9InstrumentSchema(**data)

@pytest.fixture
def minimal_payload():
    return {
        "loan_id": "L1",
        "borrower_id": "B1",
        "loan_amount_original": Decimal("100.00"),
        "loan_amount_outstanding": Decimal("80.00"),
        "currency": "USD",
        "drawdown_date": date(2023, 1, 1),
        "maturity_date": date(2023, 2, 1),
        "business_model_objective": "hold_to_collect",
        "business_model_assessment": "Hold",
        "sppi_test_passed": "Pass",
        "classification_category": "Amortized Cost",
        "measurement_category": "amortised_cost",
    }

def test_pd_lgd_boundary_checks(minimal_payload):
    # PD and LGD must be between 0 and 1
    for field in ("pd_12m", "pd_lifetime", "lgd"):  # all between 0 and 1
        for invalid in (-0.1, Decimal("1.1")):
            data = minimal_payload.copy()
            data[field] = invalid
            with pytest.raises(ValidationError):
                IFRS9InstrumentSchema(**data)

def test_date_logic_invalid(minimal_payload):
    # maturity_date must be after drawdown_date
    data = minimal_payload.copy()
    data["drawdown_date"] = date(2023, 5, 1)
    data["maturity_date"] = date(2023, 4, 1)
    with pytest.raises(ValidationError):
        IFRS9InstrumentSchema(**data)

def test_json_fields_accept_and_reject(minimal_payload):
    # JSONB-style fields: dicts and lists
    data = minimal_payload.copy()
    data["probability_weighted_scenarios"] = {"base": 0.5, "adverse": 0.3}
    data["historical_stage_transitions"] = [{"from_stage": 1, "to_stage": 2}]
    schema = IFRS9InstrumentSchema(**data)
    assert isinstance(schema.probability_weighted_scenarios, dict)
    assert isinstance(schema.historical_stage_transitions, list)

    # Wrong types
    data2 = minimal_payload.copy()
    data2["probability_weighted_scenarios"] = "invalid"
    with pytest.raises(ValidationError):
        IFRS9InstrumentSchema(**data2)
    data3 = minimal_payload.copy()
    data3["historical_stage_transitions"] = "not a list"
    with pytest.raises(ValidationError):
        IFRS9InstrumentSchema(**data3)