"""Database models"""
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from src.db.session import Base


# Enums
class InstrumentType(str, Enum):
    TERM_LOAN = "TERM_LOAN"
    OVERDRAFT = "OVERDRAFT"
    BOND = "BOND"
    COMMITMENT = "COMMITMENT"


class Classification(str, Enum):
    AMORTIZED_COST = "AMORTIZED_COST"
    FVOCI = "FVOCI"
    FVTPL = "FVTPL"


class BusinessModel(str, Enum):
    HOLD_TO_COLLECT = "HOLD_TO_COLLECT"
    HOLD_TO_COLLECT_AND_SELL = "HOLD_TO_COLLECT_AND_SELL"
    OTHER = "OTHER"


class Stage(str, Enum):
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"


class InstrumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WRITTEN_OFF = "WRITTEN_OFF"
    DERECOGNIZED = "DERECOGNIZED"


class CustomerType(str, Enum):
    RETAIL = "RETAIL"
    CORPORATE = "CORPORATE"
    SME = "SME"
    GOVERNMENT = "GOVERNMENT"


class ParameterType(str, Enum):
    PD = "PD"
    LGD = "LGD"
    EAD = "EAD"
    SICR_THRESHOLD = "SICR_THRESHOLD"


class CollateralType(str, Enum):
    REAL_ESTATE = "REAL_ESTATE"
    CASH = "CASH"
    SECURITIES = "SECURITIES"
    EQUIPMENT = "EQUIPMENT"


class ImportStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class FacilityType(str, Enum):
    TERM_LOAN = "TERM_LOAN"
    REVOLVING_CREDIT = "REVOLVING_CREDIT"
    OVERDRAFT = "OVERDRAFT"
    CREDIT_CARD = "CREDIT_CARD"
    LETTER_OF_CREDIT = "LETTER_OF_CREDIT"
    GUARANTEE = "GUARANTEE"
    COMMITMENT = "COMMITMENT"
    OTHER = "OTHER"


class OverrideStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class CreditRating(str, Enum):
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    CC = "CC"
    C = "C"
    D = "D"


# Models
class Customer(Base):
    """Customer model"""
    __tablename__ = "customer"
    
    customer_id = Column(String(50), primary_key=True)
    customer_name = Column(String(255), nullable=False)
    customer_type = Column(SQLEnum(CustomerType), nullable=False)
    industry_sector = Column(String(100))
    credit_rating = Column(String(20))
    
    # Credit information
    internal_rating = Column(String(20))
    external_rating = Column(String(20))
    credit_score = Column(Integer)
    
    # Geographic
    country = Column(String(50), default="Uganda")
    region = Column(String(100))
    
    # Status
    is_watchlist = Column(Boolean, default=False)
    is_defaulted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    instruments = relationship("FinancialInstrument", back_populates="customer")


class FinancialInstrument(Base):
    """Financial instrument model"""
    __tablename__ = "financial_instrument"
    
    instrument_id = Column(String(50), primary_key=True)
    instrument_type = Column(SQLEnum(InstrumentType), nullable=False)
    customer_id = Column(String(50), ForeignKey("customer.customer_id"), nullable=False)
    
    # Basic details
    origination_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    interest_rate = Column(Numeric(8, 4), nullable=False)
    currency = Column(String(3), default="UGX")
    
    # Classification
    classification = Column(SQLEnum(Classification))
    classification_date = Column(Date)
    business_model = Column(SQLEnum(BusinessModel))
    sppi_test_result = Column(Boolean)
    
    # Staging
    current_stage = Column(SQLEnum(Stage), default=Stage.STAGE_1)
    stage_date = Column(Date)
    initial_recognition_pd = Column(Numeric(8, 6))
    
    # Status
    status = Column(SQLEnum(InstrumentStatus), default=InstrumentStatus.ACTIVE)
    days_past_due = Column(Integer, default=0)
    is_poci = Column(Boolean, default=False)
    
    # Modification tracking
    is_modified = Column(Boolean, default=False)
    modification_date = Column(Date)
    
    # Balance and exposure fields
    outstanding_balance = Column(Numeric(18, 2))
    undrawn_commitment_amount = Column(Numeric(18, 2), default=Decimal("0"))
    is_off_balance_sheet = Column(Boolean, default=False)
    facility_type = Column(SQLEnum(FacilityType))
    credit_conversion_factor = Column(Numeric(6, 4))
    
    # ECL tracking
    current_ecl = Column(Numeric(18, 2))
    
    # Stage override tracking
    stage_override_active = Column(Boolean, default=False)
    stage_override_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="instruments")
    ecl_calculations = relationship("ECLCalculation", back_populates="instrument")
    stage_transitions = relationship("StageTransition", back_populates="instrument")
    collaterals = relationship("Collateral", back_populates="instrument")


class ECLCalculation(Base):
    """ECL calculation model"""
    __tablename__ = "ecl_calculation"
    
    calculation_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("financial_instrument.instrument_id"), nullable=False)
    reporting_date = Column(Date, nullable=False)
    stage = Column(SQLEnum(Stage), nullable=False)
    
    # ECL Components
    pd = Column(Numeric(8, 6), nullable=False)
    lgd = Column(Numeric(8, 6), nullable=False)
    ead = Column(Numeric(18, 2), nullable=False)
    ecl_amount = Column(Numeric(18, 2), nullable=False)
    
    # Calculation details
    calculation_method = Column(String(20))  # INDIVIDUAL, COLLECTIVE
    time_horizon = Column(String(20))  # 12_MONTH, LIFETIME
    discount_rate = Column(Numeric(8, 6))
    
    # Scenario weighting
    base_scenario_ecl = Column(Numeric(18, 2))
    upside_scenario_ecl = Column(Numeric(18, 2))
    downside_scenario_ecl = Column(Numeric(18, 2))
    scenario_weights = Column(JSON)
    
    # Metadata
    calculation_timestamp = Column(DateTime, server_default=func.now())
    calculation_duration_ms = Column(Integer)
    parameters_version = Column(String(50))
    
    # Relationships
    instrument = relationship("FinancialInstrument", back_populates="ecl_calculations")


class StageTransition(Base):
    """Stage transition model"""
    __tablename__ = "stage_transition"
    
    transition_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("financial_instrument.instrument_id"), nullable=False)
    transition_date = Column(Date, nullable=False)
    from_stage = Column(SQLEnum(Stage), nullable=False)
    to_stage = Column(SQLEnum(Stage), nullable=False)
    
    # SICR details
    sicr_indicators = Column(JSON)
    pd_at_transition = Column(Numeric(8, 6))
    pd_at_origination = Column(Numeric(8, 6))
    pd_change_percentage = Column(Numeric(8, 4))
    days_past_due = Column(Integer)
    
    # Rationale
    transition_reason = Column(Text)
    is_automatic = Column(Boolean, default=True)
    approved_by = Column(String(50))
    
    # Relationships
    instrument = relationship("FinancialInstrument", back_populates="stage_transitions")


class ParameterSet(Base):
    """Parameter set model"""
    __tablename__ = "parameter_set"
    
    parameter_id = Column(String(50), primary_key=True)
    parameter_type = Column(SQLEnum(ParameterType), nullable=False)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    
    # Segmentation
    customer_segment = Column(String(50))
    product_type = Column(String(50))
    credit_rating = Column(String(20))
    collateral_type = Column(String(50))
    
    # Parameter values
    parameter_value = Column(Numeric(8, 6), nullable=False)
    parameter_curve = Column(JSON)
    
    # Metadata
    version = Column(String(20))
    created_by = Column(String(50))
    approved_by = Column(String(50))
    approval_date = Column(Date)
    notes = Column(Text)


class MacroScenario(Base):
    """Macroeconomic scenario model"""
    __tablename__ = "macro_scenario"
    
    scenario_id = Column(String(50), primary_key=True)
    scenario_name = Column(String(100), nullable=False)
    effective_date = Column(Date, nullable=False)
    probability_weight = Column(Numeric(4, 3), nullable=False)
    
    # Economic indicators (stored as JSON)
    gdp_growth_rate = Column(JSON)
    inflation_rate = Column(JSON)
    ugx_usd_exchange_rate = Column(JSON)
    unemployment_rate = Column(JSON)
    interest_rate = Column(JSON)
    
    # Sector-specific adjustments
    agriculture_index = Column(JSON)
    manufacturing_index = Column(JSON)
    services_index = Column(JSON)
    
    # Metadata
    created_by = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    notes = Column(Text)


class Collateral(Base):
    """Collateral model"""
    __tablename__ = "collateral"
    
    collateral_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("financial_instrument.instrument_id"), nullable=False)
    collateral_type = Column(SQLEnum(CollateralType), nullable=False)
    
    # Valuation
    original_value = Column(Numeric(18, 2), nullable=False)
    current_value = Column(Numeric(18, 2), nullable=False)
    valuation_date = Column(Date, nullable=False)
    currency = Column(String(3), default="UGX")
    
    # Haircut
    haircut_percentage = Column(Numeric(5, 2), nullable=False)
    net_realizable_value = Column(Numeric(18, 2), nullable=False)
    
    # Legal
    is_perfected = Column(Boolean, default=False)
    priority_rank = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    instrument = relationship("FinancialInstrument", back_populates="collaterals")


class AuditEntry(Base):
    """Audit entry model"""
    __tablename__ = "audit_entry"
    
    audit_id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    event_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    
    # User context
    user_id = Column(String(50), nullable=False)
    user_role = Column(String(50))
    ip_address = Column(String(50))
    session_id = Column(String(100))
    
    # Change tracking
    action = Column(String(255), nullable=False)
    before_state = Column(JSON)
    after_state = Column(JSON)
    
    # Details
    rationale = Column(Text)
    calculation_details = Column(JSON)
    
    # Immutability
    is_deleted = Column(Boolean, default=False)
    hash = Column(String(64))  # SHA-256 hash


class ImportBatch(Base):
    """Import batch tracking model"""
    __tablename__ = "import_batch"
    
    import_id = Column(String(50), primary_key=True)
    import_type = Column(String(50), nullable=False)  # LOAN_PORTFOLIO, CUSTOMER_DATA, MACRO_SCENARIO
    status = Column(SQLEnum(ImportStatus), default=ImportStatus.PENDING, nullable=False)
    
    # Import details
    filename = Column(String(255))
    file_format = Column(String(10))  # csv, json
    records_processed = Column(Integer, default=0)
    records_valid = Column(Integer, default=0)
    records_invalid = Column(Integer, default=0)
    
    # Validation
    validation_errors = Column(JSON)
    
    # Approval workflow
    submitted_by = Column(String(50), nullable=False)
    submitted_at = Column(DateTime, server_default=func.now(), nullable=False)
    reviewed_by = Column(String(50))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Relationships
    staged_instruments = relationship("StagedInstrument", back_populates="import_batch", cascade="all, delete-orphan")


class StagedInstrument(Base):
    """Staged financial instrument awaiting approval"""
    __tablename__ = "staged_instrument"
    
    staged_id = Column(Integer, primary_key=True, autoincrement=True)
    import_id = Column(String(50), ForeignKey("import_batch.import_id"), nullable=False)
    
    # All instrument fields stored as staging data
    instrument_id = Column(String(50), nullable=False)
    instrument_type = Column(String(50), nullable=False)
    customer_id = Column(String(50), nullable=False)
    
    # Basic details
    origination_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    outstanding_balance = Column(Numeric(18, 2))
    interest_rate = Column(Numeric(8, 4), nullable=False)
    currency = Column(String(3), default="UGX")
    
    # Status fields
    days_past_due = Column(Integer, default=0)
    is_poci = Column(Boolean, default=False)
    is_forbearance = Column(Boolean, default=False)
    is_watchlist = Column(Boolean, default=False)

    # Customer data (for new customers)
    customer_name = Column(String(255))
    customer_type = Column(String(50))
    customer_sector = Column(String(100))
    customer_credit_rating = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    import_batch = relationship("ImportBatch", back_populates="staged_instruments")



# ========================================
# PHASE 1 ENHANCEMENTS - NEW MODELS
# ========================================

# Additional Enums for Phase 1
class WatchlistStatus(str, Enum):
    NORMAL = "NORMAL"
    WATCHLIST = "WATCHLIST"
    SPECIAL_MENTION = "SPECIAL_MENTION"


class SectorRiskRating(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MatrixType(str, Enum):
    PIT = "PIT"  # Point-in-Time
    TTC = "TTC"  # Through-the-Cycle


class ScenarioType(str, Enum):
    BASELINE = "BASELINE"
    OPTIMISTIC = "OPTIMISTIC"
    DOWNTURN = "DOWNTURN"


class ProductType(str, Enum):
    TERM_LOAN = "TERM_LOAN"
    MORTGAGE = "MORTGAGE"
    CREDIT_CARD = "CREDIT_CARD"
    OVERDRAFT = "OVERDRAFT"
    REVOLVING_CREDIT = "REVOLVING_CREDIT"
    TRADE_FINANCE = "TRADE_FINANCE"
    OTHER = "OTHER"


class WorkflowType(str, Enum):
    PARAMETER_CHANGE = "PARAMETER_CHANGE"
    STAGING_OVERRIDE = "STAGING_OVERRIDE"
    MACRO_SCENARIO_UPDATE = "MACRO_SCENARIO_UPDATE"
    CCF_CALIBRATION = "CCF_CALIBRATION"


# Task 30: Enhanced Staging Engine
class StagingOverride(Base):
    """Staging override model for manual stage adjustments"""
    __tablename__ = "staging_override"
    
    override_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("financial_instrument.instrument_id"), nullable=False)
    original_stage = Column(String(20), nullable=False)  # Store as string to avoid enum conflicts
    override_stage = Column(String(20), nullable=False)  # Store as string to avoid enum conflicts
    justification = Column(Text, nullable=False)
    
    # Workflow
    requested_by = Column(String(50), nullable=False)
    requested_at = Column(DateTime, server_default=func.now(), nullable=False)
    approved_by = Column(String(50), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(String(50), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)  # Store as string to avoid enum conflicts
    workflow_id = Column(String(50), nullable=True)
    
    # Expiry
    expiry_date = Column(Date, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)
    
    # ECL Impact
    ecl_before_override = Column(Numeric(18, 2), nullable=True)
    ecl_after_override = Column(Numeric(18, 2), nullable=True)
    ecl_impact_amount = Column(Numeric(18, 2), nullable=True)


# Task 31: Transition Matrix PD
class TransitionMatrix(Base):
    """Transition matrix for PD estimation"""
    __tablename__ = "transition_matrix"
    
    matrix_id = Column(String(50), primary_key=True)
    portfolio_segment = Column(String(50), nullable=False)
    rating_from = Column(String(20), nullable=False)
    rating_to = Column(String(20), nullable=False)
    transition_probability = Column(Numeric(10, 8), nullable=False)
    
    # Observation period
    observation_period_start = Column(Date, nullable=False)
    observation_period_end = Column(Date, nullable=False)
    calibration_date = Column(Date, nullable=False)
    
    # Matrix type
    matrix_type = Column(String(10), nullable=False)  # PIT, TTC
    
    # Validation
    psi_value = Column(Numeric(8, 6), nullable=True)  # Population Stability Index
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class RatingHistory(Base):
    """Rating history for transition matrix calibration"""
    __tablename__ = "rating_history"
    
    history_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customer.customer_id"), nullable=False)
    rating = Column(String(20), nullable=False)
    rating_date = Column(Date, nullable=False)
    rating_agency = Column(String(50), nullable=True)  # INTERNAL, EXTERNAL
    rating_notch_change = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


# Task 32: Behavioral Scorecard PD
class BehavioralScorecard(Base):
    """Behavioral scorecard for retail PD estimation"""
    __tablename__ = "behavioral_scorecard"
    
    scorecard_id = Column(String(50), primary_key=True)
    product_type = Column(String(50), nullable=False)
    score_min = Column(Integer, nullable=False)
    score_max = Column(Integer, nullable=False)
    pd_estimate = Column(Numeric(8, 6), nullable=False)
    calibration_date = Column(Date, nullable=False)
    
    # Performance metrics
    gini_coefficient = Column(Numeric(6, 4), nullable=True)
    ks_statistic = Column(Numeric(6, 4), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class CustomerScore(Base):
    """Customer behavioral scores"""
    __tablename__ = "customer_score"
    
    score_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customer.customer_id"), nullable=False)
    scorecard_id = Column(String(50), ForeignKey("behavioral_scorecard.scorecard_id"), nullable=False)
    score_value = Column(Integer, nullable=False)
    score_date = Column(Date, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


# Task 33: Macro Regression Model
class MacroRegressionModel(Base):
    """Macro regression model for forward-looking adjustments"""
    __tablename__ = "macro_regression_model"
    
    model_id = Column(String(50), primary_key=True)
    dependent_variable = Column(String(20), nullable=False)  # PD, LGD
    coefficients = Column(JSON, nullable=False)
    r_squared = Column(Numeric(6, 4), nullable=True)
    calibration_date = Column(Date, nullable=False)
    portfolio_segment = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


# Task 34: Facility-Level LGD
class CollateralHaircutConfig(Base):
    """Collateral haircut configuration"""
    __tablename__ = "collateral_haircut_config"
    
    config_id = Column(String(50), primary_key=True)
    collateral_type = Column(String(50), nullable=False)
    standard_haircut_pct = Column(Numeric(5, 2), nullable=False)
    stressed_haircut_pct = Column(Numeric(5, 2), nullable=False)
    revaluation_frequency_months = Column(Integer, nullable=False)
    effective_date = Column(Date, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class WorkoutRecovery(Base):
    """Historical workout and recovery data for LGD calibration"""
    __tablename__ = "workout_recovery"
    
    recovery_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("financial_instrument.instrument_id"), nullable=False)
    default_date = Column(Date, nullable=False)
    recovery_date = Column(Date, nullable=True)
    
    # Recovery details
    exposure_at_default = Column(Numeric(18, 2), nullable=False)
    recovery_amount = Column(Numeric(18, 2), nullable=True)
    direct_costs = Column(Numeric(18, 2), nullable=True)
    time_to_recovery_months = Column(Integer, nullable=True)
    realized_lgd = Column(Numeric(8, 6), nullable=True)
    
    # Segmentation
    product_type = Column(String(50), nullable=True)
    collateral_type = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


# Task 35: Off-Balance Sheet EAD
class CCFConfig(Base):
    """Credit Conversion Factor configuration"""
    __tablename__ = "ccf_config"
    
    config_id = Column(String(50), primary_key=True)
    facility_type = Column(String(50), nullable=False)  # Store as string to avoid enum conflicts
    ccf_value = Column(Numeric(6, 4), nullable=False)
    effective_date = Column(Date, nullable=False)
    updated_by = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


# Task 36: Authentication & RBAC
class User(Base):
    """User model for authentication"""
    __tablename__ = "user"
    
    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    roles = relationship("UserRole", back_populates="user")
    activity_logs = relationship("UserActivityLog", back_populates="user")


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "role"
    
    role_id = Column(String(50), primary_key=True)
    role_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    users = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role")


class Permission(Base):
    """Permission model for RBAC"""
    __tablename__ = "permission"
    
    permission_id = Column(String(50), primary_key=True)
    permission_name = Column(String(100), nullable=False, unique=True)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    roles = relationship("RolePermission", back_populates="permission")


class UserRole(Base):
    """User-Role association"""
    __tablename__ = "user_role"
    
    user_id = Column(String(50), ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(String(50), ForeignKey("role.role_id"), primary_key=True)
    assigned_at = Column(DateTime, server_default=func.now())
    assigned_by = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class RolePermission(Base):
    """Role-Permission association"""
    __tablename__ = "role_permission"
    
    role_id = Column(String(50), ForeignKey("role.role_id"), primary_key=True)
    permission_id = Column(String(50), ForeignKey("permission.permission_id"), primary_key=True)
    granted_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")


class ApprovalWorkflow(Base):
    """Approval workflow for maker-checker"""
    __tablename__ = "approval_workflow"
    
    workflow_id = Column(String(50), primary_key=True)
    workflow_type = Column(String(50), nullable=False)
    request_data = Column(JSON, nullable=False)
    
    # Workflow
    requester_id = Column(String(50), ForeignKey("user.user_id"), nullable=False)
    request_date = Column(DateTime, server_default=func.now())
    approver_id = Column(String(50), ForeignKey("user.user_id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # PENDING, APPROVED, REJECTED
    rejection_reason = Column(Text, nullable=True)


class UserActivityLog(Base):
    """User activity log"""
    __tablename__ = "user_activity_log"
    
    log_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("user.user_id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    activity_description = Column(Text, nullable=False)
    
    # Context
    ip_address = Column(String(50), nullable=True)
    session_id = Column(String(100), nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    
    # Request/Response
    request_data = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
