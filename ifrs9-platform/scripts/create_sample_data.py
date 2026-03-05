"""
Create sample data for testing Phase 1 services.

This script creates:
- Admin user and test users with different roles
- Sample customers
- Sample financial instruments
- Sample macro scenarios
- Sample parameters
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.db.models import (
    User, Customer, FinancialInstrument, MacroScenario, Role, UserRole,
    Stage, FacilityType, CreditRating, InstrumentType, Classification, BusinessModel, InstrumentStatus
)
from src.services.authentication import authentication_service
from src.services.authorization import authorization_service


def create_users(db: Session):
    """Create admin and test users"""
    print("Creating users...")
    
    # Initialize roles and permissions first
    print("  Initializing roles and permissions...")
    authorization_service.initialize_default_roles_and_permissions(db)
    
    users_data = [
        {
            "username": "admin",
            "email": "admin@ifrs9.ug",
            "password": "Admin@123456",
            "role_name": "Administrator"
        },
        {
            "username": "maker1",
            "email": "maker1@ifrs9.ug",
            "password": "Maker@123456",
            "role_name": "Risk Manager"
        },
        {
            "username": "checker1",
            "email": "checker1@ifrs9.ug",
            "password": "Checker@123456",
            "role_name": "Risk Manager"
        },
        {
            "username": "analyst1",
            "email": "analyst1@ifrs9.ug",
            "password": "Analyst@123456",
            "role_name": "Accountant"
        },
        {
            "username": "viewer1",
            "email": "viewer1@ifrs9.ug",
            "password": "Viewer@123456",
            "role_name": "Viewer"
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user already exists
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            print(f"  User {user_data['username']} already exists, skipping...")
            created_users.append(existing)
            continue
        
        # Create user
        user, error = authentication_service.register_user(
            db=db,
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"]
        )
        
        if error:
            print(f"  Error creating user {user_data['username']}: {error}")
            continue
        
        # Assign role
        role = db.query(Role).filter(Role.role_name == user_data["role_name"]).first()
        if role:
            authorization_service.assign_role_to_user(db, user.user_id, role.role_id)
            print(f"  Created user: {user.username} (role: {user_data['role_name']})")
        else:
            print(f"  Created user: {user.username} (no role assigned)")
        
        created_users.append(user)
    
    return created_users


def create_customers(db: Session):
    """Create sample customers"""
    print("\nCreating customers...")
    
    customers_data = [
        {
            "customer_id": "CUST001",
            "customer_name": "ABC Manufacturing Ltd",
            "customer_type": "CORPORATE",
            "industry_sector": "Manufacturing",
            "credit_rating": CreditRating.BBB
        },
        {
            "customer_id": "CUST002",
            "customer_name": "XYZ Trading Company",
            "customer_type": "SME",
            "industry_sector": "Trade",
            "credit_rating": CreditRating.BB
        },
        {
            "customer_id": "CUST003",
            "customer_name": "John Doe",
            "customer_type": "RETAIL",
            "industry_sector": "Individual",
            "credit_rating": CreditRating.A
        },
        {
            "customer_id": "CUST004",
            "customer_name": "Tech Innovations Ltd",
            "customer_type": "CORPORATE",
            "industry_sector": "Technology",
            "credit_rating": CreditRating.AA
        },
        {
            "customer_id": "CUST005",
            "customer_name": "Green Agriculture Co",
            "customer_type": "SME",
            "industry_sector": "Agriculture",
            "credit_rating": CreditRating.BBB
        }
    ]
    
    created_customers = []
    for cust_data in customers_data:
        # Check if customer already exists
        existing = db.query(Customer).filter(Customer.customer_id == cust_data["customer_id"]).first()
        if existing:
            print(f"  Customer {cust_data['customer_id']} already exists, skipping...")
            created_customers.append(existing)
            continue
        
        customer = Customer(**cust_data)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        print(f"  Created customer: {customer.customer_id} - {customer.customer_name}")
        created_customers.append(customer)
    
    return created_customers


def create_financial_instruments(db: Session, customers):
    """Create sample financial instruments"""
    print("\nCreating financial instruments...")
    
    instruments_data = [
        {
            "instrument_id": "LOAN001",
            "customer_id": "CUST001",
            "instrument_type": InstrumentType.TERM_LOAN,
            "principal_amount": Decimal("500000.00"),
            "outstanding_balance": Decimal("450000.00"),
            "undrawn_commitment_amount": Decimal("0.00"),
            "origination_date": date(2024, 1, 15),
            "maturity_date": date(2027, 1, 15),
            "interest_rate": Decimal("12.5"),
            "current_stage": Stage.STAGE_1,
            "days_past_due": 0,
            "classification": Classification.AMORTIZED_COST,
            "business_model": BusinessModel.HOLD_TO_COLLECT,
            "sppi_test_result": True,
            "status": InstrumentStatus.ACTIVE,
            "facility_type": FacilityType.TERM_LOAN,
            "is_off_balance_sheet": False,
            "current_ecl": Decimal("5000.00")
        },
        {
            "instrument_id": "LOAN002",
            "customer_id": "CUST002",
            "instrument_type": InstrumentType.OVERDRAFT,
            "principal_amount": Decimal("75000.00"),
            "outstanding_balance": Decimal("60000.00"),
            "undrawn_commitment_amount": Decimal("15000.00"),
            "origination_date": date(2023, 6, 1),
            "maturity_date": date(2026, 6, 1),
            "interest_rate": Decimal("15.0"),
            "current_stage": Stage.STAGE_1,
            "days_past_due": 0,
            "classification": Classification.AMORTIZED_COST,
            "business_model": BusinessModel.HOLD_TO_COLLECT,
            "sppi_test_result": True,
            "status": InstrumentStatus.ACTIVE,
            "facility_type": FacilityType.OVERDRAFT,
            "is_off_balance_sheet": False,
            "current_ecl": Decimal("1200.00")
        },
        {
            "instrument_id": "LOAN003",
            "customer_id": "CUST003",
            "instrument_type": InstrumentType.TERM_LOAN,
            "principal_amount": Decimal("250000.00"),
            "outstanding_balance": Decimal("200000.00"),
            "undrawn_commitment_amount": Decimal("0.00"),
            "origination_date": date(2022, 3, 10),
            "maturity_date": date(2042, 3, 10),
            "interest_rate": Decimal("10.0"),
            "current_stage": Stage.STAGE_1,
            "days_past_due": 0,
            "classification": Classification.AMORTIZED_COST,
            "business_model": BusinessModel.HOLD_TO_COLLECT,
            "sppi_test_result": True,
            "status": InstrumentStatus.ACTIVE,
            "facility_type": FacilityType.TERM_LOAN,
            "is_off_balance_sheet": False,
            "current_ecl": Decimal("2500.00")
        },
        {
            "instrument_id": "LOAN004",
            "customer_id": "CUST004",
            "instrument_type": InstrumentType.TERM_LOAN,
            "principal_amount": Decimal("1000000.00"),
            "outstanding_balance": Decimal("950000.00"),
            "undrawn_commitment_amount": Decimal("0.00"),
            "origination_date": date(2023, 9, 1),
            "maturity_date": date(2028, 9, 1),
            "interest_rate": Decimal("11.0"),
            "current_stage": Stage.STAGE_2,
            "days_past_due": 35,
            "classification": Classification.AMORTIZED_COST,
            "business_model": BusinessModel.HOLD_TO_COLLECT,
            "sppi_test_result": True,
            "status": InstrumentStatus.ACTIVE,
            "facility_type": FacilityType.TERM_LOAN,
            "is_off_balance_sheet": False,
            "current_ecl": Decimal("45000.00")
        },
        {
            "instrument_id": "LOAN005",
            "customer_id": "CUST005",
            "instrument_type": InstrumentType.COMMITMENT,
            "principal_amount": Decimal("150000.00"),
            "outstanding_balance": Decimal("0.00"),
            "undrawn_commitment_amount": Decimal("150000.00"),
            "origination_date": date(2024, 2, 1),
            "maturity_date": date(2025, 2, 1),
            "interest_rate": Decimal("13.5"),
            "current_stage": Stage.STAGE_1,
            "days_past_due": 0,
            "classification": Classification.AMORTIZED_COST,
            "business_model": BusinessModel.HOLD_TO_COLLECT,
            "sppi_test_result": True,
            "status": InstrumentStatus.ACTIVE,
            "facility_type": FacilityType.COMMITMENT,
            "is_off_balance_sheet": True,
            "current_ecl": Decimal("1500.00")
        }
    ]
    
    created_instruments = []
    for inst_data in instruments_data:
        # Check if instrument already exists
        existing = db.query(FinancialInstrument).filter(
            FinancialInstrument.instrument_id == inst_data["instrument_id"]
        ).first()
        if existing:
            print(f"  Instrument {inst_data['instrument_id']} already exists, skipping...")
            created_instruments.append(existing)
            continue
        
        instrument = FinancialInstrument(**inst_data)
        db.add(instrument)
        db.commit()
        db.refresh(instrument)
        
        print(f"  Created instrument: {instrument.instrument_id} - {instrument.instrument_type.value} ({instrument.current_stage.value})")
        created_instruments.append(instrument)
    
    return created_instruments


def create_macro_scenarios(db: Session):
    """Create sample macro scenarios"""
    print("\nCreating macro scenarios...")
    
    scenarios_data = [
        {
            "scenario_id": "BASE_2026",
            "scenario_name": "Base Case 2026",
            "probability_weight": Decimal("0.60"),
            "gdp_growth_rate": {"2026": 5.5, "2027": 5.8, "2028": 6.0},
            "inflation_rate": {"2026": 4.0, "2027": 3.8, "2028": 3.5},
            "ugx_usd_exchange_rate": {"2026": 3700, "2027": 3750, "2028": 3800},
            "unemployment_rate": {"2026": 3.5, "2027": 3.3, "2028": 3.0},
            "interest_rate": {"2026": 10.0, "2027": 9.5, "2028": 9.0},
            "effective_date": date(2026, 1, 1)
        },
        {
            "scenario_id": "OPTIMISTIC_2026",
            "scenario_name": "Optimistic Case 2026",
            "probability_weight": Decimal("0.25"),
            "gdp_growth_rate": {"2026": 7.0, "2027": 7.5, "2028": 8.0},
            "inflation_rate": {"2026": 3.0, "2027": 2.8, "2028": 2.5},
            "ugx_usd_exchange_rate": {"2026": 3600, "2027": 3550, "2028": 3500},
            "unemployment_rate": {"2026": 2.5, "2027": 2.3, "2028": 2.0},
            "interest_rate": {"2026": 9.0, "2027": 8.5, "2028": 8.0},
            "effective_date": date(2026, 1, 1)
        },
        {
            "scenario_id": "PESSIMISTIC_2026",
            "scenario_name": "Pessimistic Case 2026",
            "probability_weight": Decimal("0.15"),
            "gdp_growth_rate": {"2026": 3.0, "2027": 2.5, "2028": 2.0},
            "inflation_rate": {"2026": 6.0, "2027": 6.5, "2028": 7.0},
            "ugx_usd_exchange_rate": {"2026": 3900, "2027": 4000, "2028": 4100},
            "unemployment_rate": {"2026": 5.0, "2027": 5.5, "2028": 6.0},
            "interest_rate": {"2026": 12.0, "2027": 12.5, "2028": 13.0},
            "effective_date": date(2026, 1, 1)
        }
    ]
    
    created_scenarios = []
    for scenario_data in scenarios_data:
        # Check if scenario already exists
        existing = db.query(MacroScenario).filter(
            MacroScenario.scenario_id == scenario_data["scenario_id"]
        ).first()
        if existing:
            print(f"  Scenario {scenario_data['scenario_id']} already exists, skipping...")
            created_scenarios.append(existing)
            continue
        
        scenario = MacroScenario(**scenario_data)
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
        
        print(f"  Created scenario: {scenario.scenario_id} - {scenario.scenario_name}")
        created_scenarios.append(scenario)
    
    return created_scenarios


def main():
    """Main function to create all sample data"""
    print("=" * 60)
    print("Creating Sample Data for IFRS 9 Platform")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create users
        users = create_users(db)
        
        # Create customers
        customers = create_customers(db)
        
        # Create financial instruments
        instruments = create_financial_instruments(db, customers)
        
        # Create macro scenarios
        scenarios = create_macro_scenarios(db)
        
        print("\n" + "=" * 60)
        print("Sample Data Creation Complete!")
        print("=" * 60)
        print(f"\nCreated:")
        print(f"  - {len(users)} users")
        print(f"  - {len(customers)} customers")
        print(f"  - {len(instruments)} financial instruments")
        print(f"  - {len(scenarios)} macro scenarios")
        
        print("\n" + "=" * 60)
        print("Test User Credentials:")
        print("=" * 60)
        print("Admin:    username=admin,    password=Admin@123456")
        print("Maker:    username=maker1,   password=Maker@123456")
        print("Checker:  username=checker1, password=Checker@123456")
        print("Analyst:  username=analyst1, password=Analyst@123456")
        print("Viewer:   username=viewer1,  password=Viewer@123456")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
