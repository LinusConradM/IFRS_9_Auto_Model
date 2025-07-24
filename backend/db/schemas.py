"""
Pydantic schemas for IFRS 9 database models.
"""
from datetime import date, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


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