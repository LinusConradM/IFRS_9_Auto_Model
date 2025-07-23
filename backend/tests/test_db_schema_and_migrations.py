import os

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError

from alembic.config import Config
from alembic import command


@pytest.fixture(scope='module')
def engine():
    from core.database import DATABASE_URL

    try:
        eng = create_engine(DATABASE_URL)
        conn = eng.connect()
        conn.close()
    except (OperationalError, ValueError):
        pytest.skip("Database not available - skipping migration tests")
    return eng


def test_upgrade_to_head(engine):
    cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    command.upgrade(cfg, 'head')
    inspector = inspect(engine)
    expected_tables = [
        'loan_portfolio',
        'collateral_information',
        'loan_book_versions',
        'audit_logs',
        'attachments',
        'approval_workflows',
    ]
    existing = inspector.get_table_names()
    for tbl in expected_tables:
        assert tbl in existing, f"Expected table '{tbl}' to exist"


def test_foreign_key_constraints(engine):
    inspector = inspect(engine)
    fk_coll = inspector.get_foreign_keys('collateral_information')
    assert any(fk['referred_table'] == 'loan_portfolio' for fk in fk_coll)
    fk_version = inspector.get_foreign_keys('loan_book_versions')
    assert any(fk['referred_table'] == 'loan_portfolio' for fk in fk_version)
    fk_attach = inspector.get_foreign_keys('attachments')
    assert any(fk['referred_table'] == 'loan_portfolio' for fk in fk_attach)
    fk_app = inspector.get_foreign_keys('approval_workflows')
    assert any(fk['referred_table'] == 'loan_portfolio' for fk in fk_app)


def test_seed_script_and_data_insertion(tmp_path, engine):
    csv_file = tmp_path / 'sample.csv'
    csv_file.write_text(
        'borrower_id,loan_id,stage,pd,lgd,ead,impairment,drawdown_date,maturity_date,default_flag\n'
        'B1,L1,1,0.01,0.2,1000,0.0,2020-01-01,2021-01-01,false\n'
        'B2,L2,2,0.02,0.3,2000,,2020-06-01,2021-06-01,true\n'
    )
    from services.seed_ifrs9 import seed_from_csv

    # Seed the sample data
    seed_from_csv(str(csv_file))

    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM loan_portfolio'))
        count = result.scalar()
    assert count == 2