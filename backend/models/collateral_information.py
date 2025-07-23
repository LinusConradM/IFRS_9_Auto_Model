from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class CollateralInformation(Base):
    __tablename__ = "collateral_information"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_portfolio.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    value = Column(Numeric(14, 2), nullable=False)
    appraisal_date = Column(Date, nullable=False)
    ltv = Column(Numeric(5, 4), nullable=False)

    loan = relationship("LoanPortfolio", back_populates="collaterals")