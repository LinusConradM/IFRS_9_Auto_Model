from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    Boolean,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from core.database import Base


class LoanPortfolio(Base):
    __tablename__ = "loan_portfolio"

    id = Column(Integer, primary_key=True, index=True)
    borrower_id = Column(String, nullable=False, index=True)
    loan_id = Column(String, nullable=False, unique=True, index=True)
    stage = Column(Integer, nullable=False, index=True)
    pd = Column(Numeric(5, 4), nullable=False)
    lgd = Column(Numeric(5, 4), nullable=False)
    ead = Column(Numeric(14, 2), nullable=False)
    impairment = Column(Numeric(14, 2), nullable=True)
    drawdown_date = Column(Date, nullable=False, index=True)
    maturity_date = Column(Date, nullable=False, index=True)
    default_flag = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    collaterals = relationship("CollateralInformation", back_populates="loan")
    versions = relationship("LoanBookVersion", back_populates="loan")
    attachments = relationship("Attachment", back_populates="loan")
    approvals = relationship("ApprovalWorkflow", back_populates="loan")