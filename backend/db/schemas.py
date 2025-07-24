"""
Pydantic schemas for IFRS 9 database models.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from pydantic import BaseModel, condecimal, model_validator


class LoanBookVersionSchema(BaseModel):
    version_id: int
    snapshot_data: Dict
    created_at: datetime
    created_by: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True


class CollateralInformationSchema(BaseModel):
    id: int
    loan_id: str
    collateral_type: str
    value: float
    appraisal_date: date
    ltv: Optional[float]
    guarantee_amount: Optional[float]

    class Config:
        orm_mode = True


class LoanPortfolioSchema(BaseModel):
    loan_id: str
    borrower_id: str
    drawdown_date: date
    maturity_date: date
    pd_12m: Optional[float]
    pd_lifetime: Optional[float]
    lgd: Optional[float]
    ead: Optional[float]
    sicr_flag: Optional[bool]
    stage: Optional[int]
    impairment_allowance: Optional[float]
    version_id: int
    collateral: Optional[List[CollateralInformationSchema]]

    class Config:
        orm_mode = True


class AuditLogSchema(BaseModel):
    id: int
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    performed_by: Optional[str]
    timestamp: datetime
    details: Optional[Dict]

    class Config:
        orm_mode = True


class AttachmentSchema(BaseModel):
    id: int
    doc_type: str
    file_path: str
    linked_loan_id: str
    uploaded_by: str
    checksum: str
    created_at: datetime

    class Config:
        orm_mode = True


class ApprovalWorkflowSchema(BaseModel):
    id: int
    loan_id: str
    version_id: int
    status: str
    reviewer: Optional[str]
    submitted_at: datetime
    reviewed_at: Optional[datetime]
    published_at: Optional[datetime]

    class Config:
        orm_mode = True


class ScenarioAssumptionSchema(BaseModel):
    id: int
    scenario: str
    unemployment: Optional[float]
    gdp: Optional[float]
    interest_rate: Optional[float]
    scenario_weights: Optional[Dict]
    created_at: datetime

    class Config:
        orm_mode = True


class ImpairmentCalculationSchema(BaseModel):
    id: int
    loan_id: str
    version_id: int
    calculated_by: str
    calculated_at: datetime
    ptp_ecl: float
    lifetime_ecl: float
    details: Optional[Dict]

    class Config:
        orm_mode = True


class InstrumentStagingSchema(BaseModel):
    instrument_id: str
    current_stage: int
    sicr_flag: bool
    default_flag: bool
    days_past_due: int
    last_stage_change: datetime
    override_reason: Optional[str]
    classified_by: Optional[str]

    class Config:
        orm_mode = True


class StagingHistorySchema(BaseModel):
    id: int
    instrument_id: str
    from_stage: int
    to_stage: int
    changed_at: datetime
    changed_by: str
    trigger_type: str
    rationale: Optional[str]

    class Config:
        orm_mode = True


class ECLComputationResultSchema(BaseModel):
    id: int
    instrument_id: str
    stage: int
    pd: float
    lgd: float
    ead: float
    eir: float
    ecl_amount: float
    discounted: float
    scenario_version: int
    calculated_at: datetime
    scenario_result: Optional[Dict]

    class Config:
        orm_mode = True


class ProvisionMatrixTemplateSchema(BaseModel):
    id: int
    name: str
    segment_keys: Dict
    buckets: Dict
    base_loss_rates: Dict
    macro_adjustment_model: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ECLForecastSchema(BaseModel):
    id: int
    portfolio_id: int
    forecast_horizon: int
    scenario_weights: Dict
    macro_inputs: Dict
    ecl_curve_json: Dict
    generated_by: str
    generated_at: datetime

    class Config:
        orm_mode = True


class UploadHistorySchema(BaseModel):
    upload_id: int
    filename: str
    checksum: str
    uploaded_by: Optional[str]
    upload_timestamp: datetime
    schema_version: str
    total_rows: int
    valid_rows: int
    invalid_rows: int

    class Config:
        orm_mode = True


class RawInstrumentSchema(BaseModel):
    id: int
    upload_id: int
    row_number: int
    raw_data: Dict[str, Any]
    errors: Optional[List[str]]

    class Config:
        orm_mode = True


class ValidatedInstrumentSchema(BaseModel):
    id: int
    upload_id: int
    instrument_id: str
    borrower_id: str
    asset_class: str
    classification_category: str
    measurement_basis: str
    off_balance_flag: bool
    pd_12m: float
    pd_lifetime: float
    lgd: float
    ead: float
    sicr_flag: bool
    eir: float
    collateral_flag: bool
    collateral_type: Optional[str]
    collateral_value: Optional[float]
    appraisal_date: Optional[date]
    drawdown_date: date
    maturity_date: date

    class Config:
        orm_mode = True

class IFRS9InstrumentSchema(BaseModel):
    # 1. Unique Identifiers
    loan_id: str
    borrower_id: str
    group_id: Optional[str] = None
    facility_id: Optional[str] = None
    portfolio_id: Optional[str] = None

    # 2. Borrower Information
    borrower_name: Optional[str] = None
    sector: Optional[str] = None
    geography: Optional[str] = None
    customer_type: Optional[Literal['Retail', 'SME', 'Corporate', 'Sovereign']] = None
    credit_rating_internal: Optional[str] = None
    credit_rating_external: Optional[str] = None
    low_credit_risk_flag: Optional[bool] = None

    # 3. Loan Terms
    loan_amount_original: Decimal
    loan_amount_outstanding: Decimal
    currency: str
    product_type: Optional[str] = None
    drawdown_date: date
    maturity_date: date
    remaining_term: Optional[int] = None
    interest_rate_type: Optional[Literal['Fixed', 'Variable']] = None
    interest_rate: Optional[condecimal(max_digits=5, decimal_places=3)] = None
    effective_interest_rate: Optional[condecimal(max_digits=5, decimal_places=3)] = None
    repayment_type: Optional[Literal['Bullet', 'Amortizing', 'Revolving']] = None
    repayment_schedule: Optional[Literal['Monthly', 'Quarterly', 'Custom']] = None

    # 4. Credit Risk Metrics
    pd_12m: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    pd_lifetime: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    lgd: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    ead: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    sicr_flag: Optional[bool] = None
    stage: Optional[Literal[1, 2, 3]] = None
    default_flag: Optional[bool] = None
    days_past_due: Optional[int] = None
    forbearance_flag: Optional[bool] = None
    collateral_value: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    collateral_type: Optional[str] = None
    guarantee_amount: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    recovery_strategy: Optional[str] = None

    # 5. Impairment Tracking
    impairment_allowance: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    impairment_model_version: Optional[str] = None
    date_stage_changed: Optional[date] = None
    ecl_amount_12m: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    ecl_amount_lifetime: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    ecl_scenario_weights: Optional[Dict[str, float]] = None

    # 6. Historical / Time-Series Fields
    past_pd: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    past_lgd: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    past_stage: Optional[Literal[1, 2, 3]] = None
    date_entered_default: Optional[date] = None
    date_exited_default: Optional[date] = None

    # 7. Off-Balance Sheet Exposures
    loan_commitment_amount: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    guarantee_exposure: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    facility_type: Optional[Literal['Committed', 'Uncommitted']] = None
    cancel_notice_period: Optional[int] = None

    # 8. Other Qualitative / Judgmental Fields
    risk_analyst_comments: Optional[str] = None
    override_justification: Optional[str] = None
    rebuttable_presumption_notes: Optional[str] = None
    macro_adjustment_applied: Optional[bool] = None

    # 9. AI/ML-enhanced models
    borrower_financials: Optional[Dict[str, Any]] = None
    behavioral_data: Optional[Dict[str, Any]] = None
    cluster_id: Optional[str] = None
    probability_weighted_scenarios: Optional[Dict[str, Any]] = None

    # 10. Classification & Measurement (IFRS 9.4.1.1 – 4.1.4)
    business_model_objective: Literal['hold_to_collect', 'hold_to_collect_and_sell', 'other']
    business_model_assessment: Literal['Hold', 'Hold and Sell', 'Trade']
    sppi_test_passed: Literal['Pass', 'Fail', 'Unassessed']
    classification_category: Literal['Amortized Cost', 'FVOCI', 'FVTPL']
    measurement_category: Literal['amortised_cost', 'FVOCI', 'FVPL']
    initial_classification: Optional[str] = None
    classification_date: Optional[date] = None
    reclassification_reason: Optional[str] = None
    initial_recognition_date: Optional[date] = None

    # 11. Regulatory Trace & Model Lock-In
    reporting_standard_version: Optional[str] = None
    ifrs9_model_config_id: Optional[str] = None
    lock_in_date: Optional[date] = None

    # 12. Audit Metadata & Source Mapping
    source_upload_id: Optional[int] = None
    source_file_name: Optional[str] = None
    source_row_number: Optional[int] = None
    data_entry_user_id: Optional[str] = None
    upload_timestamp: Optional[datetime] = None

    # 13. Lifetime Estimation & Model Control
    expected_lifetime_months: Optional[int] = None
    impairment_scenario_assumptions: Optional[Dict[str, Any]] = None
    model_override_flag: Optional[bool] = None
    override_documentation_link: Optional[str] = None

    # 14. Staging and SICR
    sicr_assessment_method: Optional[Literal['qualitative', 'quantitative', 'backstop']] = None
    sicr_trigger_description: Optional[Dict[str, Any]] = None
    backstop_days: Optional[int] = None
    origination_pd: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    current_pd: Optional[condecimal(max_digits=5, decimal_places=4)] = None
    pd_trend: Optional[str] = None

    # 15. Impairment Model & Scenario Support
    scenario_adjustments: Optional[Dict[str, Any]] = None
    model_type: Optional[Literal['simplified', 'general']] = None
    discount_rate_used: Optional[condecimal(max_digits=5, decimal_places=3)] = None

    # 16. Disclosure & Audit Trail (IFRS 7 Reference)
    input_source: Optional[str] = None
    uploader_user_id: Optional[str] = None
    upload_schema_version: Optional[str] = None
    last_validated_by_ai: Optional[str] = None
    validation_confidence_score: Optional[condecimal(max_digits=5, decimal_places=4)] = None

    # 17. Enhanced Historical Tracking
    historical_stage_transitions: Optional[List[Dict[str, Any]]] = None
    cumulative_ecl: Optional[condecimal(max_digits=15, decimal_places=2)] = None
    prior_impairment_assessments: Optional[List[Dict[str, Any]]] = None

    # 18. AI-Support Fields
    ai_validation_flags: Optional[Dict[str, Any]] = None
    suggested_corrections_by_ai: Optional[List[Dict[str, Any]]] = None
    ai_agent_version: Optional[str] = None

    @model_validator(mode='after')
    def _validate_ranges_and_dates(self):
        if self.drawdown_date and self.maturity_date and self.maturity_date <= self.drawdown_date:
            raise ValueError('maturity_date must be after drawdown_date')
        if self.pd_12m is not None and (self.pd_12m < 0 or self.pd_12m > 1):
            raise ValueError('pd_12m must be between 0 and 1')
        if self.pd_lifetime is not None and (self.pd_lifetime < 0 or self.pd_lifetime > 1):
            raise ValueError('pd_lifetime must be between 0 and 1')
        if self.lgd is not None and (self.lgd < 0 or self.lgd > 1):
            raise ValueError('lgd must be between 0 and 1')
        return self

    class Config:
        extra = 'forbid'
        orm_mode = True