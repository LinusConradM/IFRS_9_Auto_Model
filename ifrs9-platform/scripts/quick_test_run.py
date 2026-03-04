"""
Quick Test Run - Demonstrate IFRS 9 Platform with Real Data
This script:
1. Sets up sample parameters (PD, LGD, EAD)
2. Creates macro scenarios
3. Runs classification and ECL calculations on sample loans
4. Displays results
"""
import sys
import os
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
import uuid

# Set database URL to use port 5433
os.environ['DATABASE_URL'] = 'postgresql://ifrs9:ifrs9pass@localhost:5433/ifrs9'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from src.db.session import SessionLocal
from src.db.models import (
    ParameterSet, MacroScenario, FinancialInstrument, Customer,
    ParameterType, CustomerType, Stage
)
from src.services.classification import ClassificationService
from src.services.staging import StagingService
from src.services.ecl_engine import ECLCalculationService
from src.services.parameter_service import ParameterService
from src.services.macro_scenario_service import MacroScenarioService


def setup_sample_parameters(db: Session):
    """Create sample PD, LGD, EAD parameters"""
    print("\n" + "="*60)
    print("STEP 1: Setting up sample parameters")
    print("="*60)
    
    parameters = []
    
    # PD Parameters by customer type and stage
    pd_configs = [
        # RETAIL customers
        ("RETAIL", Stage.STAGE_1, 0.02),   # 2% PD for Stage 1
        ("RETAIL", Stage.STAGE_2, 0.15),   # 15% PD for Stage 2
        ("RETAIL", Stage.STAGE_3, 0.60),   # 60% PD for Stage 3
        # SME customers
        ("SME", Stage.STAGE_1, 0.03),      # 3% PD for Stage 1
        ("SME", Stage.STAGE_2, 0.20),      # 20% PD for Stage 2
        ("SME", Stage.STAGE_3, 0.70),      # 70% PD for Stage 3
        # CORPORATE customers
        ("CORPORATE", Stage.STAGE_1, 0.01), # 1% PD for Stage 1
        ("CORPORATE", Stage.STAGE_2, 0.10), # 10% PD for Stage 2
        ("CORPORATE", Stage.STAGE_3, 0.50), # 50% PD for Stage 3
    ]
    
    for customer_type, stage, pd_value in pd_configs:
        param = ParameterSet(
            parameter_id=str(uuid.uuid4()),
            parameter_type=ParameterType.PD,
            customer_segment=customer_type,
            parameter_value=Decimal(str(pd_value)),
            effective_date=date(2024, 1, 1),
            expiry_date=date(2025, 12, 31),
            notes=f"PD for {customer_type} {stage}"
        )
        parameters.append(param)
    
    # LGD Parameters by customer type
    lgd_configs = [
        ("RETAIL", 0.45),    # 45% LGD
        ("SME", 0.40),       # 40% LGD
        ("CORPORATE", 0.35), # 35% LGD
    ]
    
    for customer_type, lgd_value in lgd_configs:
        param = ParameterSet(
            parameter_id=str(uuid.uuid4()),
            parameter_type=ParameterType.LGD,
            customer_segment=customer_type,
            parameter_value=Decimal(str(lgd_value)),
            effective_date=date(2024, 1, 1),
            expiry_date=date(2025, 12, 31),
            notes=f"LGD for {customer_type}"
        )
        parameters.append(param)
    
    # EAD Parameters (simplified - using 100% of outstanding balance)
    for customer_type in ["RETAIL", "SME", "CORPORATE"]:
        param = ParameterSet(
            parameter_id=str(uuid.uuid4()),
            parameter_type=ParameterType.EAD,
            customer_segment=customer_type,
            parameter_value=Decimal("1.0"),  # 100% of outstanding
            effective_date=date(2024, 1, 1),
            expiry_date=date(2025, 12, 31),
            notes=f"EAD multiplier for {customer_type}"
        )
        parameters.append(param)
    
    # Insert parameters
    for param in parameters:
        db.merge(param)
    
    db.commit()
    print(f"✅ Created {len(parameters)} parameter records")
    print(f"   - PD parameters: {len(pd_configs)}")
    print(f"   - LGD parameters: {len(lgd_configs)}")
    print(f"   - EAD parameters: 3")


def setup_macro_scenarios(db: Session):
    """Create sample macro scenarios"""
    print("\n" + "="*60)
    print("STEP 2: Setting up macro scenarios")
    print("="*60)
    
    scenarios = [
        {
            "name": "Base Case",
            "probability": 0.60,
            "gdp_growth": [5.5, 5.3, 5.0],  # 3-year forecast
            "unemployment": [3.5, 3.4, 3.3],
            "inflation": [5.0, 4.8, 4.5],
            "interest_rate": [10.0, 9.8, 9.5],
            "description": "Most likely economic scenario"
        },
        {
            "name": "Upside",
            "probability": 0.20,
            "gdp_growth": [7.0, 6.8, 6.5],
            "unemployment": [2.5, 2.4, 2.3],
            "inflation": [4.0, 3.8, 3.5],
            "interest_rate": [9.0, 8.8, 8.5],
            "description": "Optimistic economic scenario"
        },
        {
            "name": "Downside",
            "probability": 0.20,
            "gdp_growth": [3.0, 2.8, 2.5],
            "unemployment": [5.0, 5.2, 5.5],
            "inflation": [7.0, 7.2, 7.5],
            "interest_rate": [12.0, 12.2, 12.5],
            "description": "Pessimistic economic scenario"
        }
    ]
    
    for scenario_data in scenarios:
        scenario = MacroScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_name=scenario_data["name"],
            probability_weight=Decimal(str(scenario_data["probability"])),
            gdp_growth_rate=scenario_data["gdp_growth"],
            unemployment_rate=scenario_data["unemployment"],
            inflation_rate=scenario_data["inflation"],
            interest_rate=scenario_data["interest_rate"],
            effective_date=date(2024, 1, 1),
            notes=scenario_data["description"]
        )
        db.merge(scenario)
    
    db.commit()
    print(f"✅ Created {len(scenarios)} macro scenarios")
    for s in scenarios:
        print(f"   - {s['name']}: {s['probability']*100}% probability")


def run_classification_test(db: Session, sample_size: int = 10):
    """Run classification on sample loans"""
    print("\n" + "="*60)
    print(f"STEP 3: Running classification on {sample_size} sample loans")
    print("="*60)
    
    # Get sample active loans
    instruments = db.query(FinancialInstrument).filter(
        FinancialInstrument.status == "ACTIVE"
    ).limit(sample_size).all()
    
    if not instruments:
        print("❌ No active instruments found")
        return []
    
    classification_service = ClassificationService()
    results = []
    
    print(f"\nClassifying {len(instruments)} instruments...")
    for instrument in instruments:
        try:
            result = classification_service.classify_instrument(instrument)
            results.append({
                "instrument_id": instrument.instrument_id,
                "classification": result.classification.value,
                "business_model": result.business_model.value,
                "sppi_passed": result.sppi_test_passed,
                "rationale": result.rationale
            })
            print(f"✅ {instrument.instrument_id}: {result.classification.value}")
        except Exception as e:
            print(f"❌ {instrument.instrument_id}: Error - {str(e)}")
    
    return results


def run_staging_test(db: Session, sample_size: int = 10):
    """Run staging assessment on sample loans"""
    print("\n" + "="*60)
    print(f"STEP 4: Running staging assessment on {sample_size} sample loans")
    print("="*60)
    
    # Get sample active loans with different DPD levels
    instruments = db.query(FinancialInstrument).filter(
        FinancialInstrument.status == "ACTIVE"
    ).order_by(FinancialInstrument.days_past_due.desc()).limit(sample_size).all()
    
    if not instruments:
        print("❌ No active instruments found")
        return []
    
    staging_service = StagingService()
    results = []
    
    print(f"\nAssessing staging for {len(instruments)} instruments...")
    for instrument in instruments:
        try:
            result = staging_service.determine_stage(instrument, date.today())
            results.append({
                "instrument_id": instrument.instrument_id,
                "stage": result.stage.value,
                "dpd": instrument.days_past_due,
                "credit_impaired": result.credit_impaired,
                "rationale": result.rationale
            })
            print(f"✅ {instrument.instrument_id}: {result.stage.value} (DPD: {instrument.days_past_due})")
        except Exception as e:
            print(f"❌ {instrument.instrument_id}: Error - {str(e)}")
    
    return results


def run_ecl_calculation_test(db: Session, sample_size: int = 5):
    """Run ECL calculation on sample loans"""
    print("\n" + "="*60)
    print(f"STEP 5: Running ECL calculation on {sample_size} sample loans")
    print("="*60)
    
    # Get sample active loans from different stages
    instruments = []
    for stage in [Stage.STAGE_1, Stage.STAGE_2, Stage.STAGE_3]:
        stage_instruments = db.query(FinancialInstrument).filter(
            FinancialInstrument.status == "ACTIVE",
            FinancialInstrument.current_stage == stage
        ).limit(2).all()
        instruments.extend(stage_instruments)
    
    if not instruments:
        print("❌ No active instruments found")
        return []
    
    ecl_service = ECLCalculationService()
    results = []
    
    print(f"\nCalculating ECL for {len(instruments)} instruments...")
    for instrument in instruments:
        try:
            result = ecl_service.calculate_ecl(
                instrument=instrument,
                stage=instrument.current_stage,
                reporting_date=date.today(),
                scenarios=None  # No scenarios for quick test
            )
            
            coverage_ratio = float(result.ecl_amount) / float(instrument.principal_amount) if instrument.principal_amount > 0 else 0
            
            results.append({
                "instrument_id": instrument.instrument_id,
                "stage": instrument.current_stage.value,
                "principal": float(instrument.principal_amount),
                "ecl_amount": float(result.ecl_amount),
                "coverage_ratio": coverage_ratio
            })
            
            print(f"✅ {instrument.instrument_id} ({instrument.current_stage.value}):")
            print(f"   Principal: UGX {instrument.principal_amount:,.2f}")
            print(f"   ECL: UGX {result.ecl_amount:,.2f}")
            print(f"   Coverage: {coverage_ratio:.2%}")
            
        except Exception as e:
            print(f"❌ {instrument.instrument_id}: Error - {str(e)}")
            import traceback
            traceback.print_exc()
    
    return results


def print_summary(classification_results, staging_results, ecl_results):
    """Print summary of test results"""
    print("\n" + "="*60)
    print("TEST RUN SUMMARY")
    print("="*60)
    
    print(f"\n📊 Classification Results: {len(classification_results)} instruments")
    if classification_results:
        classifications = {}
        for r in classification_results:
            classifications[r['classification']] = classifications.get(r['classification'], 0) + 1
        for classification, count in classifications.items():
            print(f"   - {classification}: {count}")
    
    print(f"\n📊 Staging Results: {len(staging_results)} instruments")
    if staging_results:
        stages = {}
        for r in staging_results:
            stages[r['stage']] = stages.get(r['stage'], 0) + 1
        for stage, count in stages.items():
            print(f"   - {stage}: {count}")
    
    print(f"\n📊 ECL Calculation Results: {len(ecl_results)} instruments")
    if ecl_results:
        total_principal = sum(r['principal'] for r in ecl_results)
        total_ecl = sum(r['ecl_amount'] for r in ecl_results)
        avg_coverage = total_ecl / total_principal if total_principal > 0 else 0
        
        print(f"   - Total Principal: UGX {total_principal:,.2f}")
        print(f"   - Total ECL: UGX {total_ecl:,.2f}")
        print(f"   - Average Coverage: {avg_coverage:.2%}")
        
        print("\n   By Stage:")
        for stage in ["STAGE_1", "STAGE_2", "STAGE_3"]:
            stage_results = [r for r in ecl_results if r['stage'] == stage]
            if stage_results:
                stage_principal = sum(r['principal'] for r in stage_results)
                stage_ecl = sum(r['ecl_amount'] for r in stage_results)
                stage_coverage = stage_ecl / stage_principal if stage_principal > 0 else 0
                print(f"   - {stage}: UGX {stage_ecl:,.2f} ({stage_coverage:.2%} coverage)")


def main():
    """Main entry point"""
    print("="*60)
    print("IFRS 9 PLATFORM - QUICK TEST RUN")
    print("="*60)
    print("\nThis script will demonstrate the platform with your real data")
    print("by running classification, staging, and ECL calculations")
    print("on a sample of your loans.\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Step 1: Setup parameters
        setup_sample_parameters(db)
        
        # Step 2: Setup macro scenarios
        setup_macro_scenarios(db)
        
        # Step 3: Run classification
        classification_results = run_classification_test(db, sample_size=10)
        
        # Step 4: Run staging
        staging_results = run_staging_test(db, sample_size=10)
        
        # Step 5: Run ECL calculation
        ecl_results = run_ecl_calculation_test(db, sample_size=6)
        
        # Print summary
        print_summary(classification_results, staging_results, ecl_results)
        
        print("\n" + "="*60)
        print("✅ TEST RUN COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review the results above")
        print("2. Adjust parameters to match your bank's risk models")
        print("3. Run calculations on your full portfolio")
        print("4. Generate IFRS 9 compliance reports")
        
    except Exception as e:
        print(f"\n❌ Test run failed: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
