import os
import sys
import csv
import tempfile

# skip database tests if SQLAlchemy or Alembic are not installed
import pytest
try:
    import sqlalchemy  # noqa: F401
    import alembic  # noqa: F401
except ImportError:
    pytest.skip("SQLAlchemy or Alembic not available, skipping DB tests", allow_module_level=True)
# ensure backend directory is on the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# compile JSONB types as JSON in SQLite for tests
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from dateutil import parser as date_parser


def try_parse_date(value):
    try:
        return date_parser.parse(value).date() if value else None
    except Exception:
        return None



@compiles(JSONB, 'sqlite')
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return 'JSON'

from sqlalchemy import inspect


def test_alembic_config_exists():
    # Ensure Alembic configuration and versions directory are present under backend
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    assert os.path.isfile(os.path.join(project_root, 'alembic.ini'))
    assert os.path.isdir(os.path.join(project_root, 'alembic', 'versions'))


def test_foreign_keys_defined():
    # Verify referential integrity constraints are declared in metadata
    from db.models import CollateralInformation, LoanPortfolio, LoanBookVersion

    fks_collateral = {fk.target_fullname for fk in CollateralInformation.__table__.foreign_keys}
    assert 'loan_portfolio.loan_id' in fks_collateral

    fks_portfolio = {fk.target_fullname for fk in LoanPortfolio.__table__.foreign_keys}
    assert 'loan_book_versions.version_id' in fks_portfolio


def test_dummy_seed_loads_data(tmp_path, monkeypatch):
    # Use in-memory SQLite for testing seed script
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    # Reload modules to apply DATABASE_URL override
    sys.modules.pop('db.session', None)
    sys.modules.pop('db.models', None)
    sys.modules.pop('seed_ifrs9', None)

    from db.session import engine, SessionLocal, Base
    from seed_ifrs9 import load_dummy_loan_book

    # Create dummy CSV file
    csv_file = tmp_path / 'dummy.csv'
    headers = ['loan_id', 'borrower_id', 'drawdown_date', 'maturity_date',
               'pd_12m', 'pd_lifetime', 'lgd', 'ead', 'sicr_flag', 'stage',
               'impairment_allowance', 'collateral_type', 'collateral_value',
               'appraisal_date', 'ltv', 'guarantee_amount']
    data_row = ['L1', 'B1', '2020-01-01', '2021-01-01', '0.01', '0.02',
                '0.5', '1000', 'true', '1', '50', 'Mortgage', '500',
                '2020-06-01', '0.5', '100']
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(data_row)

    # Create tables and load data
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    load_dummy_loan_book(session, str(csv_file))
    # Verify data inserted
    inspector = inspect(engine)
    assert 'loan_portfolio' in inspector.get_table_names()
    # Basic record check
    from sqlalchemy import text
    loan_records = session.execute(
        text('SELECT loan_id, borrower_id FROM loan_portfolio')
    ).fetchall()
    assert loan_records and loan_records[0][0] == 'L1'
    collateral_records = session.execute(
        text('SELECT collateral_type, value FROM collateral_information')
    ).fetchall()
    assert collateral_records and collateral_records[0][0] == 'Mortgage'


def test_seed_script_missing_csv(capsys):
    # Test that missing CSV path is handled gracefully
    import seed_ifrs9
    # Simulate command line args
    sys_argv = sys.argv
    sys.argv = ['seed_ifrs9.py', '--csv', 'nonexistent.csv']
    try:
        seed_ifrs9.main()
        captured = capsys.readouterr()
        assert 'CSV file not found' in captured.out
    finally:
        sys.argv = sys_argv