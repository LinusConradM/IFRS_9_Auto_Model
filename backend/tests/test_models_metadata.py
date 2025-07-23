import pytest
import models  # ensure model modules are imported for metadata registration

from core.database import Base


def test_model_tables_defined():
    expected = [
        'loan_portfolio',
        'collateral_information',
        'loan_book_versions',
        'audit_logs',
        'attachments',
        'approval_workflows',
    ]
    defined = list(Base.metadata.tables.keys())
    for tbl in expected:
        assert tbl in defined, f"Model metadata missing table '{tbl}'"


def test_foreign_keys_in_models_metadata():
    table = Base.metadata.tables['collateral_information']
    fks = list(table.foreign_keys)
    assert any(fk.column.table.name == 'loan_portfolio' for fk in fks), \
        "CollateralInformation missing ForeignKey to LoanPortfolio"