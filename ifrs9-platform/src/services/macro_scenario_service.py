"""Macroeconomic scenario service for ECL adjustments"""
from typing import List, Dict, Any
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from src.db.models import MacroScenario
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ScenarioResult:
    """Result of applying a macroeconomic scenario"""
    def __init__(self, scenario_id: int, scenario_name: str, scenario_type: str,
                 weight: Decimal, pd_adjustment: Decimal, lgd_adjustment: Decimal):
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name
        self.scenario_type = scenario_type
        self.weight = weight
        self.pd_adjustment = pd_adjustment
        self.lgd_adjustment = lgd_adjustment


class MacroScenarioService:
    """Service for applying macroeconomic scenarios to risk parameters"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_active_scenarios(self, effective_date: date) -> List[MacroScenario]:
        """
        Get active macroeconomic scenarios for a given date.
        
        Args:
            effective_date: Date for which to retrieve scenarios
            
        Returns:
            List of active scenarios
        """
        scenarios = self.db.query(MacroScenario).filter(
            MacroScenario.is_active == True,
            MacroScenario.effective_date <= effective_date,
            (MacroScenario.expiry_date.is_(None)) | (MacroScenario.expiry_date >= effective_date)
        ).all()
        
        logger.info(f"Found {len(scenarios)} active scenarios for {effective_date}")
        return scenarios
    
    def apply_macro_scenarios(self, base_pd: Decimal, base_lgd: Decimal,
                             scenarios: List[MacroScenario]) -> List[ScenarioResult]:
        """
        Apply macroeconomic scenarios to adjust PD and LGD.
        
        Scenarios adjust risk parameters based on macroeconomic indicators:
        - GDP growth: Higher growth → lower PD
        - Unemployment: Higher unemployment → higher PD
        - Inflation: Higher inflation → higher PD (for some sectors)
        - Interest rates: Higher rates → higher PD
        
        Args:
            base_pd: Base probability of default
            base_lgd: Base loss given default
            scenarios: List of macroeconomic scenarios
            
        Returns:
            List of ScenarioResult with adjusted parameters
        """
        results = []
        
        for scenario in scenarios:
            # Calculate PD adjustment based on macro indicators
            pd_adjustment = self._calculate_pd_adjustment(
                scenario.gdp_growth,
                scenario.unemployment_rate,
                scenario.inflation_rate,
                scenario.interest_rate
            )
            
            # Calculate LGD adjustment
            lgd_adjustment = self._calculate_lgd_adjustment(
                scenario.gdp_growth,
                scenario.unemployment_rate
            )
            
            result = ScenarioResult(
                scenario_id=scenario.id,
                scenario_name=scenario.scenario_name,
                scenario_type=scenario.scenario_type,
                weight=scenario.probability_weight,
                pd_adjustment=pd_adjustment,
                lgd_adjustment=lgd_adjustment
            )
            
            results.append(result)
            
            logger.debug(f"Scenario {scenario.scenario_name}: PD adj={pd_adjustment}, LGD adj={lgd_adjustment}")
        
        return results
    
    def _calculate_pd_adjustment(self, gdp_growth: Decimal, unemployment_rate: Decimal,
                                inflation_rate: Decimal, interest_rate: Decimal) -> Decimal:
        """
        Calculate PD adjustment factor based on macroeconomic indicators.
        
        Simplified model for MVP:
        - GDP growth: -0.1 per 1% GDP growth (negative correlation)
        - Unemployment: +0.05 per 1% unemployment (positive correlation)
        - Inflation: +0.02 per 1% inflation (positive correlation)
        - Interest rate: +0.03 per 1% interest rate (positive correlation)
        
        Args:
            gdp_growth: GDP growth rate (%)
            unemployment_rate: Unemployment rate (%)
            inflation_rate: Inflation rate (%)
            interest_rate: Interest rate (%)
            
        Returns:
            PD adjustment multiplier (1.0 = no change, >1.0 = increase, <1.0 = decrease)
        """
        adjustment = Decimal("1.0")
        
        if gdp_growth is not None:
            # Negative correlation: higher GDP growth → lower PD
            adjustment += (gdp_growth - Decimal("5.0")) * Decimal("-0.02")
        
        if unemployment_rate is not None:
            # Positive correlation: higher unemployment → higher PD
            adjustment += (unemployment_rate - Decimal("5.0")) * Decimal("0.03")
        
        if inflation_rate is not None:
            # Positive correlation: higher inflation → higher PD
            adjustment += (inflation_rate - Decimal("5.0")) * Decimal("0.01")
        
        if interest_rate is not None:
            # Positive correlation: higher interest rates → higher PD
            adjustment += (interest_rate - Decimal("10.0")) * Decimal("0.02")
        
        # Ensure adjustment is within reasonable bounds (0.5x to 2.0x)
        adjustment = max(Decimal("0.5"), min(Decimal("2.0"), adjustment))
        
        return adjustment
    
    def _calculate_lgd_adjustment(self, gdp_growth: Decimal, unemployment_rate: Decimal) -> Decimal:
        """
        Calculate LGD adjustment factor based on macroeconomic indicators.
        
        LGD is less sensitive to macro conditions than PD, but still affected:
        - GDP growth: -0.05 per 1% GDP growth (collateral values)
        - Unemployment: +0.02 per 1% unemployment (recovery rates)
        
        Args:
            gdp_growth: GDP growth rate (%)
            unemployment_rate: Unemployment rate (%)
            
        Returns:
            LGD adjustment multiplier
        """
        adjustment = Decimal("1.0")
        
        if gdp_growth is not None:
            # Negative correlation: higher GDP → lower LGD (better collateral values)
            adjustment += (gdp_growth - Decimal("5.0")) * Decimal("-0.01")
        
        if unemployment_rate is not None:
            # Positive correlation: higher unemployment → higher LGD (worse recovery)
            adjustment += (unemployment_rate - Decimal("5.0")) * Decimal("0.015")
        
        # Ensure adjustment is within reasonable bounds (0.7x to 1.3x)
        adjustment = max(Decimal("0.7"), min(Decimal("1.3"), adjustment))
        
        return adjustment
    
    def calculate_weighted_ecl(self, scenario_ecls: Dict[int, Decimal],
                              scenarios: List[MacroScenario]) -> Decimal:
        """
        Calculate probability-weighted ECL across scenarios.
        
        Property 12: Scenario Weighting
        Weighted ECL = Σ(weight_i × ECL_i) for all scenarios
        Sum of weights must equal 1.0
        
        Args:
            scenario_ecls: Dict mapping scenario_id to ECL amount
            scenarios: List of scenarios with weights
            
        Returns:
            Probability-weighted ECL
        """
        total_weight = Decimal("0")
        weighted_ecl = Decimal("0")
        
        for scenario in scenarios:
            weight = scenario.probability_weight
            ecl = scenario_ecls.get(scenario.id, Decimal("0"))
            
            weighted_ecl += weight * ecl
            total_weight += weight
        
        # Validate weights sum to 1.0 (Property 12)
        if abs(total_weight - Decimal("1.0")) > Decimal("0.001"):
            logger.warning(
                f"Scenario weights sum to {total_weight}, not 1.0. "
                f"This violates Property 12 (Scenario Weighting)"
            )
            # Normalize weights
            if total_weight > Decimal("0"):
                weighted_ecl = weighted_ecl / total_weight
                logger.info(f"Normalized weighted ECL to {weighted_ecl}")
        
        return weighted_ecl.quantize(Decimal("0.01"))
    
    def validate_scenarios(self, scenarios: List[MacroScenario]) -> Dict[str, Any]:
        """
        Validate scenario configuration.
        
        Checks:
        1. Weights sum to 1.0
        2. All scenarios have required fields
        3. Probability weights are between 0 and 1
        
        Args:
            scenarios: List of scenarios to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # Check weights sum to 1.0
        total_weight = sum(s.probability_weight for s in scenarios)
        if abs(total_weight - Decimal("1.0")) > Decimal("0.001"):
            errors.append(f"Scenario weights sum to {total_weight}, must equal 1.0")
        
        # Check individual scenarios
        for scenario in scenarios:
            if scenario.probability_weight < Decimal("0") or scenario.probability_weight > Decimal("1"):
                errors.append(f"Scenario {scenario.scenario_name} has invalid weight {scenario.probability_weight}")
            
            if not scenario.scenario_type:
                warnings.append(f"Scenario {scenario.scenario_name} missing scenario_type")
        
        # Check for typical scenario types
        scenario_types = {s.scenario_type for s in scenarios}
        expected_types = {'BASE', 'UPSIDE', 'DOWNSIDE'}
        if not scenario_types.intersection(expected_types):
            warnings.append(f"No standard scenario types found. Expected: {expected_types}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_weight': float(total_weight)
        }
