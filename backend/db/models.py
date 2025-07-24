"""
SQLAlchemy models for IFRS 9 database schema.
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Numeric,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .session import Base


class LoanBookVersion(Base):
    __tablename__ = 'loan_book_versions'
    version_id = Column(Integer, primary_key=True)
    snapshot_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(String, nullable=True)
    description = Column(String, nullable=True)
    loans = relationship('LoanPortfolio', back_populates='version')


class LoanPortfolio(Base):
    __tablename__ = 'loan_portfolio'
    loan_id = Column(String, primary_key=True)
    borrower_id = Column(String, nullable=False, index=True)
    drawdown_date = Column(Date, nullable=False, index=True)
    maturity_date = Column(Date, nullable=False, index=True)
    pd_12m = Column(Float, nullable=True)
    pd_lifetime = Column(Float, nullable=True)
    lgd = Column(Float, nullable=True)
    ead = Column(Float, nullable=True)
    sicr_flag = Column(Boolean, nullable=True, index=True)
    stage = Column(Integer, nullable=True, index=True)
    impairment_allowance = Column(Numeric, nullable=True)
    version_id = Column(Integer, ForeignKey('loan_book_versions.version_id'), nullable=False)
    version = relationship('LoanBookVersion', back_populates='loans')
    collateral = relationship('CollateralInformation', back_populates='loan')


class CollateralInformation(Base):
    __tablename__ = 'collateral_information'
    id = Column(Integer, primary_key=True)
    loan_id = Column(String, ForeignKey('loan_portfolio.loan_id'), nullable=False, index=True)
    collateral_type = Column(String, nullable=False)
    value = Column(Numeric, nullable=False)
    appraisal_date = Column(Date, nullable=False)
    ltv = Column(Float, nullable=True)
    guarantee_amount = Column(Numeric, nullable=True)
    loan = relationship('LoanPortfolio', back_populates='collateral')


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    performed_by = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    details = Column(JSONB, nullable=True)


class Attachment(Base):
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True)
    doc_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    linked_loan_id = Column(String, ForeignKey('loan_portfolio.loan_id'), nullable=False, index=True)
    uploaded_by = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    loan = relationship('LoanPortfolio')


class ApprovalWorkflow(Base):
    __tablename__ = 'approval_workflows'
    id = Column(Integer, primary_key=True)
    loan_id = Column(String, ForeignKey('loan_portfolio.loan_id'), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey('loan_book_versions.version_id'), nullable=False)
    status = Column(Enum('submitted', 'reviewed', 'approved', 'published', name='approval_status'), nullable=False, default='submitted')
    reviewer = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    loan = relationship('LoanPortfolio')
    version = relationship('LoanBookVersion')


class ScenarioAssumption(Base):
    __tablename__ = 'scenario_assumptions'
    id = Column(Integer, primary_key=True)
    scenario = Column(Enum('base', 'adverse', 'optimistic', name='scenario_type'), nullable=False)
    unemployment = Column(Float, nullable=True)
    gdp = Column(Float, nullable=True)
    interest_rate = Column(Float, nullable=True)
    scenario_weights = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ImpairmentCalculation(Base):
    __tablename__ = 'impairment_calculations'
    id = Column(Integer, primary_key=True)
    loan_id = Column(String, ForeignKey('loan_portfolio.loan_id'), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey('loan_book_versions.version_id'), nullable=False)
    calculated_by = Column(String, nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ptp_ecl = Column(Numeric, nullable=False)
    lifetime_ecl = Column(Numeric, nullable=False)
    details = Column(JSONB, nullable=True)
    loan = relationship('LoanPortfolio')
    version = relationship('LoanBookVersion')


class InstrumentStaging(Base):
    __tablename__ = 'instrument_staging'
    instrument_id = Column(String, primary_key=True)
    current_stage = Column(Integer, nullable=False)
    sicr_flag = Column(Boolean, nullable=False)
    default_flag = Column(Boolean, nullable=False)
    days_past_due = Column(Integer, nullable=False)
    last_stage_change = Column(DateTime(timezone=True), nullable=False)
    override_reason = Column(String, nullable=True)
    classified_by = Column(String, nullable=True)
    history = relationship('StagingHistory', back_populates='instrument', order_by='StagingHistory.changed_at')


class StagingHistory(Base):
    __tablename__ = 'staging_history'
    id = Column(Integer, primary_key=True)
    instrument_id = Column(String, ForeignKey('instrument_staging.instrument_id'), nullable=False, index=True)
    from_stage = Column(Integer, nullable=False)
    to_stage = Column(Integer, nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    changed_by = Column(String, nullable=False)
    trigger_type = Column(Enum('auto', 'manual', name='trigger_type'), nullable=False)
    rationale = Column(String, nullable=True)
    instrument = relationship('InstrumentStaging', back_populates='history')


class ECLComputationResult(Base):
    __tablename__ = 'ecl_computation_results'
    id = Column(Integer, primary_key=True)
    instrument_id = Column(String, ForeignKey('instrument_staging.instrument_id'), nullable=False, index=True)
    stage = Column(Integer, nullable=False)
    pd = Column(Float, nullable=False)
    lgd = Column(Float, nullable=False)
    ead = Column(Float, nullable=False)
    eir = Column(Float, nullable=False)
    ecl_amount = Column(Numeric, nullable=False)
    discounted = Column(Numeric, nullable=False)
    scenario_version = Column(Integer, ForeignKey('scenario_assumptions.id'), nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scenario_result = Column(JSONB, nullable=True)
    instrument = relationship('InstrumentStaging')
    scenario = relationship('ScenarioAssumption')


class ProvisionMatrixTemplate(Base):
    __tablename__ = 'provision_matrix_templates'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    segment_keys = Column(JSONB, nullable=False)
    buckets = Column(JSONB, nullable=False)
    base_loss_rates = Column(JSONB, nullable=False)
    macro_adjustment_model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ECLForecast(Base):
    __tablename__ = 'ecl_forecasts'
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('loan_book_versions.version_id'), nullable=False, index=True)
    forecast_horizon = Column(Integer, nullable=False)
    scenario_weights = Column(JSONB, nullable=False)
    macro_inputs = Column(JSONB, nullable=False)
    ecl_curve_json = Column(JSONB, nullable=False)
    generated_by = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    version = relationship('LoanBookVersion')


class UploadHistory(Base):
    __tablename__ = 'upload_history'
    upload_id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    schema_version = Column(String, nullable=False)
    total_rows = Column(Integer, nullable=False)
    valid_rows = Column(Integer, nullable=False)
    invalid_rows = Column(Integer, nullable=False)
    raw_instruments = relationship('RawInstrument', back_populates='upload_history')
    validated_instruments = relationship('ValidatedInstrument', back_populates='upload_history')


class RawInstrument(Base):
    __tablename__ = 'raw_instruments'
    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey('upload_history.upload_id'), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(JSONB, nullable=False)
    errors = Column(JSONB, nullable=True)
    upload_history = relationship('UploadHistory', back_populates='raw_instruments')


class ValidatedInstrument(Base):
    __tablename__ = 'validated_instruments'
    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey('upload_history.upload_id'), nullable=False, index=True)
    instrument_id = Column(String, nullable=False, index=True)
    borrower_id = Column(String, nullable=False)
    asset_class = Column(String, nullable=False)
    classification_category = Column(String, nullable=False)
    measurement_basis = Column(String, nullable=False)
    off_balance_flag = Column(Boolean, nullable=False)
    pd_12m = Column(Float, nullable=False)
    pd_lifetime = Column(Float, nullable=False)
    lgd = Column(Float, nullable=False)
    ead = Column(Float, nullable=False)
    sicr_flag = Column(Boolean, nullable=False)
    eir = Column(Float, nullable=False)
    collateral_flag = Column(Boolean, nullable=False)
    collateral_type = Column(String, nullable=True)
    collateral_value = Column(Numeric, nullable=True)
    appraisal_date = Column(Date, nullable=True)
    drawdown_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    upload_history = relationship('UploadHistory', back_populates='validated_instruments')