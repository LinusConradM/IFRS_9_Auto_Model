"""Macro regression service for linking macroeconomic variables to PD/LGD"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
import numpy as np
from sklearn.linear_model import LinearRegression

from src.db.models import MacroScenario, MacroRegressionModel, ParameterType
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MacroAdjustmentResult:
    """Macro adjustment result"""
    def __init__(
        self,
        base_value: Decimal,
        adjusted_value: Decimal,
        adjustment_factor: Decimal,
        scenario_name: str,
        macro_variables: Dict[str, float],
        calculation_details: Dict[str, Any]
    ):
        self.base_value = base_value
        self.adjusted_value = adjusted_value
        self.adjustment_factor = adjustment_factor
        self.scenario_name = scenario_name
        self.macro_variables = macro_variables
        self.calculation_details = calculation_details


class MacroRegressionService:
    """Service for macroeconomic regression models and adjustments"""
    
    # Uganda-specific macro variables
    UGANDA_MACRO_VARIABLES = [
        "gdp_growth_rate",
        "inflation_rate",
        "central_bank_rate",
        "ugx_usd_exchange_rate",
        "coffee_price_index",
        "oil_price_usd",
        "lending_rate"
    ]
    
    def calibrate_pd_macro_model(
        self,
        db: Session,
        historical_data: List[Dict[str, Any]],
        segment: str
    ) -> MacroRegressionModel:
        """
        Calibrate regression model linking macro variables to PD.
        
        Model: PD_t = β0 + β1×GDP_t + β2×Inflation_t + β3×CBR_t + ... + ε_t
        
        Args:
            db: Database session
            historical_data: Historical data with PD and macro variables
            segment: Customer segment
            
        Returns:
            MacroRegressionModel record
        """
        logger.info(f"Calibrating PD macro model for segment {segment}")
        
        # Prepare data for regression
        X = []  # Macro variables
        y = []  # PD values
        
        for record in historical_data:
            macro_vars = [
                record.get("gdp_growth_rate", 0),
                record.get("inflation_rate", 0),
                record.get("central_bank_rate", 0),
                record.get("ugx_usd_exchange_rate", 0),
                record.get("coffee_price_index", 0),
                record.get("oil_price_usd", 0),
                record.get("lending_rate", 0)
            ]
            X.append(macro_vars)
            y.append(float(record.get("pd", 0)))
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Extract coefficients
        coefficients = {
            "intercept": float(model.intercept_),
            "gdp_growth_rate": float(model.coef_[0]),
            "inflation_rate": float(model.coef_[1]),
            "central_bank_rate": float(model.coef_[2]),
            "ugx_usd_exchange_rate": float(model.coef_[3]),
            "coffee_price_index": float(model.coef_[4]),
            "oil_price_usd": float(model.coef_[5]),
            "lending_rate": float(model.coef_[6])
        }
        
        # Calculate R-squared
        r_squared = float(model.score(X, y))
        
        # Save model to database
        regression_model = MacroRegressionModel(
            parameter_type=ParameterType.PD,
            segment=segment,
            coefficients=coefficients,
            r_squared=r_squared,
            calibration_date=date.today(),
            is_active=True
        )
        
        db.add(regression_model)
        db.commit()
        
        logger.info(f"PD macro model calibrated: R² = {r_squared}")
        
        return regression_model
    
    def calibrate_lgd_macro_model(
        self,
        db: Session,
        historical_data: List[Dict[str, Any]],
        segment: str
    ) -> MacroRegressionModel:
        """
        Calibrate regression model linking macro variables to LGD.
        
        Model: LGD_t = β0 + β1×GDP_t + β2×Inflation_t + β3×CBR_t + ... + ε_t
        
        Args:
            db: Database session
            historical_data: Historical data with LGD and macro variables
            segment: Customer segment
            
        Returns:
            MacroRegressionModel record
        """
        logger.info(f"Calibrating LGD macro model for segment {segment}")
        
        # Prepare data for regression
        X = []  # Macro variables
        y = []  # LGD values
        
        for record in historical_data:
            macro_vars = [
                record.get("gdp_growth_rate", 0),
                record.get("inflation_rate", 0),
                record.get("central_bank_rate", 0),
                record.get("ugx_usd_exchange_rate", 0),
                record.get("coffee_price_index", 0),
                record.get("oil_price_usd", 0),
                record.get("lending_rate", 0)
            ]
            X.append(macro_vars)
            y.append(float(record.get("lgd", 0)))
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Extract coefficients
        coefficients = {
            "intercept": float(model.intercept_),
            "gdp_growth_rate": float(model.coef_[0]),
            "inflation_rate": float(model.coef_[1]),
            "central_bank_rate": float(model.coef_[2]),
            "ugx_usd_exchange_rate": float(model.coef_[3]),
            "coffee_price_index": float(model.coef_[4]),
            "oil_price_usd": float(model.coef_[5]),
            "lending_rate": float(model.coef_[6])
        }
        
        # Calculate R-squared
        r_squared = float(model.score(X, y))
        
        # Save model to database
        regression_model = MacroRegressionModel(
            parameter_type=ParameterType.LGD,
            segment=segment,
            coefficients=coefficients,
            r_squared=r_squared,
            calibration_date=date.today(),
            is_active=True
        )
        
        db.add(regression_model)
        db.commit()
        
        logger.info(f"LGD macro model calibrated: R² = {r_squared}")
        
        return regression_model
    
    def apply_macro_adjustment_pd(
        self,
        db: Session,
        base_pd: Decimal,
        scenario: MacroScenario,
        segment: str
    ) -> MacroAdjustmentResult:
        """
        Apply macroeconomic adjustment to PD.
        
        Args:
            db: Database session
            base_pd: Base PD (TTC or long-run average)
            scenario: Macro scenario
            segment: Customer segment
            
        Returns:
            MacroAdjustmentResult with adjusted PD
        """
        logger.info(f"Applying macro adjustment to PD for segment {segment}")
        
        # Fetch regression model
        model = db.query(MacroRegressionModel).filter(
            MacroRegressionModel.parameter_type == ParameterType.PD,
            MacroRegressionModel.segment == segment,
            MacroRegressionModel.is_active == True
        ).first()
        
        if not model:
            logger.warning(f"No macro model found for segment {segment}, using base PD")
            return MacroAdjustmentResult(
                base_value=base_pd,
                adjusted_value=base_pd,
                adjustment_factor=Decimal("1.0"),
                scenario_name=scenario.scenario_name,
                macro_variables={},
                calculation_details={"note": "No macro model available"}
            )
        
        # Extract macro variables from scenario
        macro_vars = {
            "gdp_growth_rate": float(scenario.gdp_growth_rate or 0),
            "inflation_rate": float(scenario.inflation_rate or 0),
            "central_bank_rate": float(scenario.central_bank_rate or 0),
            "ugx_usd_exchange_rate": float(scenario.ugx_usd_exchange_rate or 0),
            "coffee_price_index": float(scenario.coffee_price_index or 0),
            "oil_price_usd": float(scenario.oil_price_usd or 0),
            "lending_rate": float(scenario.lending_rate or 0)
        }
        
        # Calculate adjustment factor using regression coefficients
        coef = model.coefficients
        adjustment = (
            coef["intercept"] +
            coef["gdp_growth_rate"] * macro_vars["gdp_growth_rate"] +
            coef["inflation_rate"] * macro_vars["inflation_rate"] +
            coef["central_bank_rate"] * macro_vars["central_bank_rate"] +
            coef["ugx_usd_exchange_rate"] * macro_vars["ugx_usd_exchange_rate"] +
            coef["coffee_price_index"] * macro_vars["coffee_price_index"] +
            coef["oil_price_usd"] * macro_vars["oil_price_usd"] +
            coef["lending_rate"] * macro_vars["lending_rate"]
        )
        
        # Convert to adjustment factor (multiplicative)
        adjustment_factor = Decimal(str(max(0.5, min(2.0, 1.0 + adjustment))))  # Cap between 0.5x and 2.0x
        
        # Apply adjustment
        adjusted_pd = base_pd * adjustment_factor
        
        # Cap PD at 100%
        adjusted_pd = min(adjusted_pd, Decimal("1.0"))
        
        calculation_details = {
            "model_r_squared": model.r_squared,
            "base_pd": float(base_pd),
            "adjustment_factor": float(adjustment_factor),
            "adjusted_pd": float(adjusted_pd),
            "coefficients": coef
        }
        
        logger.info(f"PD adjusted: {base_pd} → {adjusted_pd} (factor: {adjustment_factor})")
        
        return MacroAdjustmentResult(
            base_value=base_pd,
            adjusted_value=adjusted_pd,
            adjustment_factor=adjustment_factor,
            scenario_name=scenario.scenario_name,
            macro_variables=macro_vars,
            calculation_details=calculation_details
        )
    
    def apply_macro_adjustment_lgd(
        self,
        db: Session,
        base_lgd: Decimal,
        scenario: MacroScenario,
        segment: str
    ) -> MacroAdjustmentResult:
        """
        Apply macroeconomic adjustment to LGD.
        
        Args:
            db: Database session
            base_lgd: Base LGD
            scenario: Macro scenario
            segment: Customer segment
            
        Returns:
            MacroAdjustmentResult with adjusted LGD
        """
        logger.info(f"Applying macro adjustment to LGD for segment {segment}")
        
        # Fetch regression model
        model = db.query(MacroRegressionModel).filter(
            MacroRegressionModel.parameter_type == ParameterType.LGD,
            MacroRegressionModel.segment == segment,
            MacroRegressionModel.is_active == True
        ).first()
        
        if not model:
            logger.warning(f"No macro model found for segment {segment}, using base LGD")
            return MacroAdjustmentResult(
                base_value=base_lgd,
                adjusted_value=base_lgd,
                adjustment_factor=Decimal("1.0"),
                scenario_name=scenario.scenario_name,
                macro_variables={},
                calculation_details={"note": "No macro model available"}
            )
        
        # Extract macro variables from scenario
        macro_vars = {
            "gdp_growth_rate": float(scenario.gdp_growth_rate or 0),
            "inflation_rate": float(scenario.inflation_rate or 0),
            "central_bank_rate": float(scenario.central_bank_rate or 0),
            "ugx_usd_exchange_rate": float(scenario.ugx_usd_exchange_rate or 0),
            "coffee_price_index": float(scenario.coffee_price_index or 0),
            "oil_price_usd": float(scenario.oil_price_usd or 0),
            "lending_rate": float(scenario.lending_rate or 0)
        }
        
        # Calculate adjustment factor using regression coefficients
        coef = model.coefficients
        adjustment = (
            coef["intercept"] +
            coef["gdp_growth_rate"] * macro_vars["gdp_growth_rate"] +
            coef["inflation_rate"] * macro_vars["inflation_rate"] +
            coef["central_bank_rate"] * macro_vars["central_bank_rate"] +
            coef["ugx_usd_exchange_rate"] * macro_vars["ugx_usd_exchange_rate"] +
            coef["coffee_price_index"] * macro_vars["coffee_price_index"] +
            coef["oil_price_usd"] * macro_vars["oil_price_usd"] +
            coef["lending_rate"] * macro_vars["lending_rate"]
        )
        
        # Convert to adjustment factor (multiplicative)
        adjustment_factor = Decimal(str(max(0.5, min(1.5, 1.0 + adjustment))))  # Cap between 0.5x and 1.5x
        
        # Apply adjustment
        adjusted_lgd = base_lgd * adjustment_factor
        
        # Cap LGD at 100%
        adjusted_lgd = min(adjusted_lgd, Decimal("1.0"))
        
        calculation_details = {
            "model_r_squared": model.r_squared,
            "base_lgd": float(base_lgd),
            "adjustment_factor": float(adjustment_factor),
            "adjusted_lgd": float(adjusted_lgd),
            "coefficients": coef
        }
        
        logger.info(f"LGD adjusted: {base_lgd} → {adjusted_lgd} (factor: {adjustment_factor})")
        
        return MacroAdjustmentResult(
            base_value=base_lgd,
            adjusted_value=adjusted_lgd,
            adjustment_factor=adjustment_factor,
            scenario_name=scenario.scenario_name,
            macro_variables=macro_vars,
            calculation_details=calculation_details
        )
    
    def validate_scenario_weights(self, scenarios: List[MacroScenario]) -> bool:
        """
        Validate that scenario weights sum to 1.0.
        
        Args:
            scenarios: List of macro scenarios
            
        Returns:
            True if weights sum to 1.0, False otherwise
        """
        total_weight = sum(Decimal(str(s.weight)) for s in scenarios)
        
        # Allow small tolerance for floating point errors
        tolerance = Decimal("0.001")
        is_valid = abs(total_weight - Decimal("1.0")) < tolerance
        
        if not is_valid:
            logger.error(f"Scenario weights sum to {total_weight}, expected 1.0")
        
        return is_valid


# Global service instance
macro_regression_service = MacroRegressionService()
