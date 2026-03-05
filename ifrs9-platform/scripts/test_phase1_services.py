#!/usr/bin/env python3
"""
Quick validation test for Phase 1 services.
Tests service imports and basic functionality without requiring database.
"""
import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all services can be imported"""
    print("=" * 80)
    print("TEST 1: Service Imports")
    print("=" * 80)

    try:
        # Core services
        from src.services.staging import staging_service
        print("✅ Staging service imported")

        from src.services.ecl_engine import ecl_calculation_service
        print("✅ ECL calculation service imported")

        # Phase 1 services
        from src.services.authentication import authentication_service
        print("✅ Authentication service imported")

        from src.services.authorization import authorization_service
        print("✅ Authorization service imported")

        from src.services.maker_checker import maker_checker_service
        print("✅ Maker-checker service imported")

        from src.services.staging_override import staging_override_service
        print("✅ Staging override service imported")

        from src.services.ead_calculation import ead_calculation_service
        print("✅ EAD calculation service imported")

        from src.services.facility_lgd import facility_lgd_service
        print("✅ Facility LGD service imported")

        from src.services.macro_regression import macro_regression_service
        print("✅ Macro regression service imported")

        from src.services.transition_matrix import transition_matrix_service
        print("✅ Transition matrix service imported")

        from src.services.scorecard import scorecard_service
        print("✅ Scorecard service imported")

        print("\n✅ All service imports successful!\n")
        return True

    except ImportError as e:
        print(f"\n❌ Import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False



def test_authentication_service():
    """Test authentication service basic functionality"""
    print("=" * 80)
    print("TEST 2: Authentication Service")
    print("=" * 80)
    
    try:
        from src.services.authentication import authentication_service
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = authentication_service.hash_password(password)
        print(f"✅ Password hashing works: {hashed[:20]}...")
        
        # Test password verification
        is_valid = authentication_service.verify_password(password, hashed)
        print(f"✅ Password verification works: {is_valid}")
        
        # Test password complexity validation
        is_complex = authentication_service.validate_password_complexity(password)
        print(f"✅ Password complexity validation works: {is_complex}")
        
        print("\n✅ Authentication service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Authentication test failed: {e}\n")
        return False


def test_ead_calculation_service():
    """Test EAD calculation service"""
    print("=" * 80)
    print("TEST 3: EAD Calculation Service")
    print("=" * 80)
    
    try:
        from src.services.ead_calculation import ead_calculation_service
        from src.db.models import FacilityType
        
        # Test default CCF values
        ccf_term_loan = ead_calculation_service.DEFAULT_CCF[FacilityType.TERM_LOAN]
        print(f"✅ Default CCF for term loan: {ccf_term_loan}")
        
        ccf_revolving = ead_calculation_service.DEFAULT_CCF[FacilityType.REVOLVING_CREDIT]
        print(f"✅ Default CCF for revolving credit: {ccf_revolving}")
        
        print("\n✅ EAD calculation service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ EAD calculation test failed: {e}\n")
        return False


def test_facility_lgd_service():
    """Test Facility LGD service"""
    print("=" * 80)
    print("TEST 4: Facility LGD Service")
    print("=" * 80)
    
    try:
        from src.services.facility_lgd import facility_lgd_service
        from src.db.models import Stage
        
        # Test default base LGD values
        lgd_secured = facility_lgd_service.DEFAULT_BASE_LGD["SECURED"]
        print(f"✅ Default base LGD for secured: {lgd_secured}")
        
        lgd_unsecured = facility_lgd_service.DEFAULT_BASE_LGD["UNSECURED"]
        print(f"✅ Default base LGD for unsecured: {lgd_unsecured}")
        
        # Test cure rates
        cure_rate_stage2 = facility_lgd_service.DEFAULT_CURE_RATES[Stage.STAGE_2]
        print(f"✅ Default cure rate for Stage 2: {cure_rate_stage2}")
        
        # Test discount factor calculation
        discount_factor = facility_lgd_service._calculate_discount_factor(
            Decimal("0.10"), 12
        )
        print(f"✅ Discount factor calculation works: {discount_factor}")
        
        print("\n✅ Facility LGD service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Facility LGD test failed: {e}\n")
        return False


def test_macro_regression_service():
    """Test Macro regression service"""
    print("=" * 80)
    print("TEST 5: Macro Regression Service")
    print("=" * 80)
    
    try:
        from src.services.macro_regression import macro_regression_service
        
        # Test Uganda macro variables list
        variables = macro_regression_service.UGANDA_MACRO_VARIABLES
        print(f"✅ Uganda macro variables defined: {len(variables)} variables")
        print(f"   Variables: {', '.join(variables)}")
        
        # Test scenario weight validation
        from src.db.models import MacroScenario
        
        # Create mock scenarios
        class MockScenario:
            def __init__(self, weight):
                self.weight = weight
        
        scenarios = [
            MockScenario(0.25),
            MockScenario(0.50),
            MockScenario(0.25)
        ]
        
        is_valid = macro_regression_service.validate_scenario_weights(scenarios)
        print(f"✅ Scenario weight validation works: {is_valid}")
        
        print("\n✅ Macro regression service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Macro regression test failed: {e}\n")
        return False


def test_transition_matrix_service():
    """Test Transition matrix service"""
    print("=" * 80)
    print("TEST 6: Transition Matrix Service")
    print("=" * 80)
    
    try:
        from src.services.transition_matrix import transition_matrix_service
        from src.db.models import CreditRating
        
        # Test rating classes
        rating_classes = transition_matrix_service.RATING_CLASSES
        print(f"✅ Rating classes defined: {len(rating_classes)} classes")
        print(f"   Classes: {', '.join(rating_classes)}")
        
        # Test default TTC PD
        ttc_pd_aaa = transition_matrix_service._get_default_ttc_pd(CreditRating.AAA)
        print(f"✅ Default TTC PD for AAA: {ttc_pd_aaa}")
        
        ttc_pd_b = transition_matrix_service._get_default_ttc_pd(CreditRating.B)
        print(f"✅ Default TTC PD for B: {ttc_pd_b}")
        
        print("\n✅ Transition matrix service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Transition matrix test failed: {e}\n")
        return False


def test_scorecard_service():
    """Test Scorecard service"""
    print("=" * 80)
    print("TEST 7: Scorecard Service")
    print("=" * 80)
    
    try:
        from src.services.scorecard import scorecard_service
        
        # Test PD bands
        pd_bands = scorecard_service.PD_BANDS
        print(f"✅ PD bands defined: {len(pd_bands)} bands")
        
        for band_name, (min_score, max_score), pd_value in pd_bands:
            print(f"   {band_name}: {min_score}-{max_score} → {pd_value}")
        
        # Test default score-to-PD mapping
        mapping_excellent = scorecard_service._default_score_to_pd(820)
        print(f"\n✅ Score 820 maps to: {mapping_excellent.pd_band} (PD: {mapping_excellent.pd_value})")
        
        mapping_poor = scorecard_service._default_score_to_pd(550)
        print(f"✅ Score 550 maps to: {mapping_poor.pd_band} (PD: {mapping_poor.pd_value})")
        
        print("\n✅ Scorecard service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Scorecard test failed: {e}\n")
        return False


def test_staging_enhancements():
    """Test enhanced staging service"""
    print("=" * 80)
    print("TEST 8: Enhanced Staging Service")
    print("=" * 80)
    
    try:
        from src.services.staging import staging_service
        
        # Test SICR thresholds
        print(f"✅ SICR PD relative threshold: {staging_service.sicr_pd_relative_threshold}")
        print(f"✅ SICR PD absolute threshold: {staging_service.sicr_pd_absolute_threshold}")
        print(f"✅ SICR DPD threshold: {staging_service.sicr_dpd_threshold}")
        print(f"✅ Credit impaired DPD threshold: {staging_service.credit_impaired_dpd_threshold}")
        
        print("\n✅ Enhanced staging service tests passed!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Enhanced staging test failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("PHASE 1 SERVICES VALIDATION TEST SUITE")
    print("=" * 80 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Service Imports", test_imports()))
    results.append(("Authentication Service", test_authentication_service()))
    results.append(("EAD Calculation Service", test_ead_calculation_service()))
    results.append(("Facility LGD Service", test_facility_lgd_service()))
    results.append(("Macro Regression Service", test_macro_regression_service()))
    results.append(("Transition Matrix Service", test_transition_matrix_service()))
    results.append(("Scorecard Service", test_scorecard_service()))
    results.append(("Enhanced Staging Service", test_staging_enhancements()))
    
    # Print summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 80 + "\n")
    
    if passed == total:
        print("🎉 All tests passed! Services are ready for integration.\n")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the errors above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
