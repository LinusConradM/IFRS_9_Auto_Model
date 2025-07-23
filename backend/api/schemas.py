from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class LoanPortfolioBase(BaseModel):
    borrower_id: str
    loan_id: str
    stage: int
    pd: float
    lgd: float
    ead: float
    impairment: Optional[float] = None
    drawdown_date: date
    maturity_date: date
    default_flag: bool = False


class LoanPortfolio(LoanPortfolioBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class CollateralInformationBase(BaseModel):
    loan_id: int
    type: str
    value: float
    appraisal_date: date
    ltv: float


class CollateralInformation(CollateralInformationBase):
    id: int

    class Config:
        orm_mode = True


class LoanBookVersionBase(BaseModel):
    loan_id: int
    version: int
    snapshot: dict


class LoanBookVersion(LoanBookVersionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class AuditLogBase(BaseModel):
    action: str
    actor: str
    context: Optional[dict] = None


class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class AttachmentBase(BaseModel):
    loan_id: Optional[int] = None
    borrower_id: Optional[str] = None
    filename: str
    file_path: str


class Attachment(AttachmentBase):
    id: int
    uploaded_at: datetime

    class Config:
        orm_mode = True


class ApprovalWorkflowBase(BaseModel):
    loan_id: int
    state: str
    assigned_reviewer: Optional[str] = None


class ApprovalWorkflow(ApprovalWorkflowBase):
    id: int
    actioned_at: datetime

    class Config:
        orm_mode = True