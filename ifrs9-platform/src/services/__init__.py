"""Services module"""

# Phase 1 services (no DB required for import)
from src.services.authentication import authentication_service
from src.services.authorization import authorization_service
from src.services.maker_checker import maker_checker_service
from src.services.staging_override import staging_override_service
from src.services.ead_calculation import ead_calculation_service
from src.services.facility_lgd import facility_lgd_service, collateral_revaluation_service
from src.services.macro_regression import macro_regression_service
from src.services.transition_matrix import transition_matrix_service
from src.services.scorecard import scorecard_service

# Core services (no DB required for import)
from src.services.staging import staging_service

# Services requiring DB session are imported as classes
from src.services.ecl_engine import ECLCalculationService, ecl_calculation_service
from src.services.parameter_service import ParameterService
from src.services.macro_scenario_service import MacroScenarioService
from src.services.data_import import DataImportService
from src.services.classification import ClassificationService
from src.services.audit_trail import AuditTrailService, AuditQueryService

__all__ = [
    # Phase 1 services
    "authentication_service",
    "authorization_service",
    "maker_checker_service",
    "staging_override_service",
    "ead_calculation_service",
    "facility_lgd_service",
    "collateral_revaluation_service",
    "macro_regression_service",
    "transition_matrix_service",
    "scorecard_service",
    # Core services
    "staging_service",
    # Service classes
    "ECLCalculationService",
    "ecl_calculation_service",
    "ParameterService",
    "MacroScenarioService",
    "DataImportService",
    "ClassificationService",
    "AuditTrailService",
    "AuditQueryService",
]
