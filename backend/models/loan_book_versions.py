from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from core.database import Base


class LoanBookVersion(Base):
    __tablename__ = "loan_book_versions"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_portfolio.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    loan = relationship("LoanPortfolio", back_populates="versions")