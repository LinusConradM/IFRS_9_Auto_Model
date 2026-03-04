"""Pydantic schemas for API validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# Enums (matching database enums)
class InstrumentTypeEnum(str, Enum):
    TERM_LOAN = "TERM_LOAN"
    OVERDRAFT = "OVERDRAFT"
    BOND = "BOND"
    COMMITMENT = "COMMITMENT"


class ClassificationEnum(str, Enum):
    AMORTIZED_COST = "AMORTIZED_COST"
    FVOCI = "FVOCI"
    FVTPL = "FVTPL"


class StageEnum(str, Enum):
    STAGE_1 = "STAGE_1"
    STAGE_2 = "STAGE_2"
    STAGE_3 = "STAGE_3"


class CustomerTypeEnum(str, Enum):
    RETAIL = "RETAIL"
    CORPORATE = "CORPORATE"
    SME = "SME"
    GOVERNMENT = "GOVERNMENT"


# Base schemas
class CustomerBase(BaseModel):
    customer_id: str = Field(..., max_length=50)
    customer_name: str = Field(..., max_length=255)
    customer_type: CustomerTypeEnum
    industry_sector: Optional[str] = Field(None, max_length=100)
    credit_rating: Optional[str] = Field(None, max_length=20)
    internal_rating: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="Uganda", max_length=50)
    region: Optional[str] = Field(None, max_length=100)


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    is_watchlist: bool
    is_defaulted: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FinancialInstrumentBase(BaseModel):
    instrument_id: str = Field(..., max_length=50)
    instrument_type: InstrumentTypeEnum
    customer_id: str = Field(..., max_length=50)
    origination_date: date
    maturity_date: date
    principal_amount: Decimal = Field(..., gt=0, decimal_places=2)
    interest_rate: Decimal = Field(..., ge=0, le=1, decimal_places=4)
    currency: str = Field(default="UGX", max_length=3)
    
    @validator('maturity_date')
    def maturity_after_origination(cls, v, values):
        if 'origination_date' in values and v <= values['origination_date']:
            raise ValueError('maturity_date must be after origination_date')
        return v


class FinancialInstrumentCreate(FinancialInstrumentBase):
    pass


class FinancialInstrumentResponse(FinancialInstrumentBase):
    classification: Optional[ClassificationEnum]
    current_stage: StageEnum
    days_past_due: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ECLCalculationRequest(BaseModel):
    instrument_id: str
    reporting_date: date
    stage: StageEnum
    scenarios: Optional[List[Dict[str, float]]] = None


class ECLCalculationResponse(BaseModel):
    calculation_id: str
    instrument_id: str
    reporting_date: date
    stage: StageEnum
    ecl_amount: Decimal
    pd: Decimal
    lgd: Decimal
    ead: Decimal
    calculation_timestamp: datetime
    
    class Config:
        from_attributes = True


class ClassificationRequest(BaseModel):
    instrument_id: str


class ClassificationResponse(BaseModel):
    instrument_id: str
    classification: ClassificationEnum
    business_model: str
    sppi_test_passed: bool
    rationale: str


class StagingRequest(BaseModel):
    instrument_id: str
    reporting_date: date


class StagingResponse(BaseModel):
    instrument_id: str
    current_stage: StageEnum
    previous_stage: Optional[StageEnum]
    sicr_detected: bool
    credit_impaired: bool
    rationale: str


class ImportRequest(BaseModel):
    source: str
    file_path: Optional[str] = None
    data: Optional[List[Dict]] = None


class ImportResponse(BaseModel):
    import_id: str
    status: str
    records_imported: int
    records_failed: int
    validation_errors: List[Dict]


class ParameterRequest(BaseModel):
    parameter_type: str
    customer_segment: Optional[str] = None
    product_type: Optional[str] = None
    credit_rating: Optional[str] = None
    effective_date: date


class ParameterResponse(BaseModel):
    parameter_id: str
    parameter_type: str
    parameter_value: Decimal
    effective_date: date
    
    class Config:
        from_attributes = True
