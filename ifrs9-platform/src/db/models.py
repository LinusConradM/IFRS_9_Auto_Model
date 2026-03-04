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
