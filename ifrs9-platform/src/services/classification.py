"""Classification service for IFRS 9 financial instruments"""
from typing import Dict, Any
from decimal import Decimal
from datetime import date
import uuid

from src.db.models import FinancialInstrument, Classification, BusinessModel
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ClassificationResult:
    """Classification result"""
    def __init__(self, classification: Classification, business_model: BusinessModel, 
                 sppi_test_passed: bool, rationale: str):
        self.classification = classification
        self.business_model = business_model
        self.sppi_test_passed = sppi_test_passed
        self.rationale = rationale


class ClassificationService:
    """Service for classifying financial instruments according to IFRS 9"""
    
    def classify_instrument(self, instrument: FinancialInstrument) -> ClassificationResult:
        """
        Classify financial instrument according to IFRS 9 criteria.
        
        Property 1: Classification Completeness
        For any financial instrument imported into the system, both the business model test 
        and the SPPI test must be evaluated, and the instrument must be classified into 
        exactly one of: Amortized Cost, FVOCI, or FVTPL.
        
        Args:
            instrument: Financial instrument to classify
            
        Returns:
            ClassificationResult with classification, business model, SPPI result, and rationale
        """
        logger.info(f"Classifying instrument {instrument.instrument_id}")
        
        # Step 1: Evaluate business model
        business_model_result = self.evaluate_business_model(instrument)
        business_model = business_model_result["business_model"]
        
        # Step 2: Evaluate SPPI test
        sppi_result = self.evaluate_sppi_test(instrument)
        sppi_passed = sppi_result["passed"]
        
        # Step 3: Determine classification based on business model and SPPI
        classification, rationale = self._determine_classification(
            business_model, sppi_passed, business_model_result, sppi_result
        )
        
        logger.info(f"Instrument {instrument.instrument_id} classified as {classification}")
        
        return ClassificationResult(
            classification=classification,
            business_model=business_model,
            sppi_test_passed=sppi_passed,
            rationale=rationale
        )
    
    def evaluate_business_model(self, instrument: FinancialInstrument) -> Dict[str, Any]:
        """
        Evaluate business model test.
        
        Determines whether the business model is:
        - HOLD_TO_COLLECT: Hold to collect contractual cash flows
        - HOLD_TO_COLLECT_AND_SELL: Hold to collect and sell
        - OTHER: Other business models (trading, etc.)
        
        Args:
            instrument: Financial instrument
            
        Returns:
            Dict with business_model and rationale
        """
        # For MVP, we use simple heuristics based on instrument type
        # In production, this would consider actual business model documentation
        
        if instrument.instrument_type.value in ["TERM_LOAN", "OVERDRAFT"]:
            # Loans are typically held to collect
            return {
                "business_model": BusinessModel.HOLD_TO_COLLECT,
                "rationale": f"{instrument.instrument_type.value} typically held to collect contractual cash flows"
            }
        elif instrument.instrument_type.value == "BOND":
            # Bonds might be held to collect and sell
            return {
                "business_model": BusinessModel.HOLD_TO_COLLECT_AND_SELL,
                "rationale": "Bonds may be held to collect cash flows and sold before maturity"
            }
        else:
            return {
                "business_model": BusinessModel.OTHER,
                "rationale": f"{instrument.instrument_type.value} does not fit hold to collect model"
            }
    
    def evaluate_sppi_test(self, instrument: FinancialInstrument) -> Dict[str, Any]:
        """
        Evaluate SPPI (Solely Payments of Principal and Interest) test.
        
        Determines whether contractual cash flows are solely payments of principal and interest.
        Fails if instrument has:
        - Equity conversion features
        - Commodity-linked returns
        - Leverage features
        - Non-recourse features
        
        Args:
            instrument: Financial instrument
            
        Returns:
            Dict with passed (bool) and rationale
        """
        # For MVP, we use simple heuristics
        # In production, this would analyze actual contractual terms
        
        if instrument.instrument_type.value in ["TERM_LOAN", "OVERDRAFT"]:
            # Standard loans pass SPPI test
            return {
                "passed": True,
                "rationale": f"{instrument.instrument_type.value} has standard principal and interest payments"
            }
        elif instrument.instrument_type.value == "BOND":
            # Standard bonds pass SPPI test
            # Convertible bonds would fail
            return {
                "passed": True,
                "rationale": "Bond has standard coupon and principal payments"
            }
        elif instrument.instrument_type.value == "COMMITMENT":
            # Commitments typically pass
            return {
                "passed": True,
                "rationale": "Commitment has standard terms"
            }
        else:
            return {
                "passed": False,
                "rationale": f"{instrument.instrument_type.value} may have non-SPPI features"
            }
    
    def _determine_classification(self, business_model: BusinessModel, sppi_passed: bool,
                                  bm_result: Dict, sppi_result: Dict) -> tuple:
        """
        Determine final classification based on business model and SPPI test.
        
        Property 2: SPPI Test Failure Classification
        For any financial instrument that fails the SPPI test, the classification must be FVTPL.
        
        Classification rules:
        - HOLD_TO_COLLECT + SPPI pass → Amortized Cost
        - HOLD_TO_COLLECT_AND_SELL + SPPI pass → FVOCI
        - SPPI fail → FVTPL (regardless of business model)
        - OTHER business model → FVTPL
        
        Args:
            business_model: Business model result
            sppi_passed: SPPI test result
            bm_result: Business model evaluation details
            sppi_result: SPPI test evaluation details
            
        Returns:
            Tuple of (Classification, rationale)
        """
        # Property 2: SPPI failure always results in FVTPL
        if not sppi_passed:
            return (
                Classification.FVTPL,
                f"SPPI test failed: {sppi_result['rationale']}. Classified as FVTPL per IFRS 9."
            )
        
        # SPPI passed, check business model
        if business_model == BusinessModel.HOLD_TO_COLLECT:
            return (
                Classification.AMORTIZED_COST,
                f"Business model: {bm_result['rationale']}. SPPI test passed. Classified as Amortized Cost."
            )
        elif business_model == BusinessModel.HOLD_TO_COLLECT_AND_SELL:
            return (
                Classification.FVOCI,
                f"Business model: {bm_result['rationale']}. SPPI test passed. Classified as FVOCI."
            )
        else:  # OTHER
            return (
                Classification.FVTPL,
                f"Business model: {bm_result['rationale']}. Classified as FVTPL."
            )
    
    def reclassify_instrument(self, instrument_id: str, reason: str) -> ClassificationResult:
        """
        Reclassify an instrument (rare, only when business model changes).
        
        Args:
            instrument_id: Instrument ID
            reason: Reason for reclassification
            
        Returns:
            New classification result
        """
        # TODO: Implement reclassification logic
        # This would fetch the instrument, reclassify it, and update the database
        logger.info(f"Reclassifying instrument {instrument_id}: {reason}")
        raise NotImplementedError("Reclassification not yet implemented")


# Global service instance
classification_service = ClassificationService()
