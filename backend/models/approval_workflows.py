from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_portfolio.id"), nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    assigned_reviewer = Column(String, nullable=True)
    actioned_at = Column(DateTime(timezone=True), server_default=func.now())

    loan = relationship("LoanPortfolio", back_populates="approvals")