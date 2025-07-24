import os
import sys
import csv

import pytest
from fastapi.testclient import TestClient

# compile JSONB as JSON for SQLite in tests
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB


@compiles(JSONB, 'sqlite')
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return 'JSON'


@pytest.fixture(autouse=True)
def setup_sqlite_env(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///:memory:')
    # ensure modules reloaded
    for m in list(sys.modules):
        if m.startswith('db.') or m.startswith('api.') or m.startswith('services.instrument_upload_service'):
            sys.modules.pop(m, None)


@pytest.fixture
def client_and_db():
    # import after env var set
    from db.session import engine, SessionLocal, Base
    # ensure model definitions are loaded
    import db.models  # noqa: F401
    from api.main import app
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    return client, SessionLocal


def test_upload_valid_csv_and_list(client_and_db, tmp_path):
    client, SessionLocal = client_and_db
    # prepare sample CSV
    csv_file = tmp_path / 'instruments.csv'
    headers = [
        'instrument_id', 'borrower_id', 'asset_class',
        'classification_category', 'measurement_basis', 'off_balance_flag',
        'pd_12m', 'pd_lifetime', 'lgd', 'ead', 'sicr_flag', 'eir',
        'collateral_flag', 'collateral_type', 'collateral_value', 'appraisal_date',
        'drawdown_date', 'maturity_date',
    ]
    row = [
        'ID1', 'B1', 'Loans', 'Amortised cost', 'AC', 'false',
        '0.1', '0.2', '0.5', '1000', 'false', '0.05',
        'false', '', '', '', '2020-01-01', '2021-01-01',
    ]
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row)

    with open(csv_file, 'rb') as f:
        res = client.post('/upload_instruments', files={'file': ('instruments.csv', f, 'text/csv')})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data['total_rows'] == 1
    assert data['valid_rows'] == 1
    assert data['invalid_rows'] == 0
    assert len(data['preview']) == 1

    # GET list
    res2 = client.get('/instruments')
    assert res2.status_code == 200
    lst = res2.json()
    assert isinstance(lst, list)
    assert len(lst) == 1


def test_upload_with_errors_and_duplicates(client_and_db, tmp_path):
    client, SessionLocal = client_and_db
    csv_file = tmp_path / 'instruments.csv'
    headers = [
        'instrument_id', 'borrower_id', 'asset_class',
        'classification_category', 'measurement_basis', 'off_balance_flag',
        'pd_12m', 'pd_lifetime', 'lgd', 'ead', 'sicr_flag', 'eir',
        'collateral_flag', 'collateral_type', 'collateral_value', 'appraisal_date',
        'drawdown_date', 'maturity_date',
    ]
    # two rows: one missing pd_12m, one duplicate ID
    row1 = [
        'ID2', 'B2', 'Loans', 'Amortised cost', 'AC', 'false',
        '', '0.2', '0.5', '1000', 'false', '0.05',
        'false', '', '', '', '2020-01-01', '2021-01-01',
    ]
    row2 = [
        'ID2', 'B2', 'Loans', 'Amortised cost', 'AC', 'false',
        '0.1', '0.2', '0.5', '1000', 'false', '0.05',
        'false', '', '', '', '2020-01-01', '2021-01-01',
    ]
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row1)
        writer.writerow(row2)

    with open(csv_file, 'rb') as f:
        res = client.post('/upload_instruments', files={'file': ('instruments.csv', f, 'text/csv')})
    assert res.status_code == 200, res.text
    data = res.json()
    assert data['total_rows'] == 2
    # first row missing pd_12m, second duplicate instrument_id
    assert data['invalid_rows'] == 2
    assert data['valid_rows'] == 0
    errors = [r['errors'] for r in data['preview']]
    assert any('Missing pd_12m' in e for e in errors)
    assert any('Duplicate instrument_id' in e for e in errors)


def test_unsupported_file_type(client_and_db):
    client, _ = client_and_db
    # upload txt file
    res = client.post('/upload_instruments', files={'file': ('file.txt', b'data', 'text/plain')})
    assert res.status_code == 400


def test_filter_errors(client_and_db, tmp_path):
    client, _ = client_and_db
    # upload two rows, one valid, one invalid
    csv_file = tmp_path / 'instruments.csv'
    headers = [
        'instrument_id', 'borrower_id', 'asset_class',
        'classification_category', 'measurement_basis', 'off_balance_flag',
        'pd_12m', 'pd_lifetime', 'lgd', 'ead', 'sicr_flag', 'eir',
        'collateral_flag', 'collateral_type', 'collateral_value', 'appraisal_date',
        'drawdown_date', 'maturity_date',
    ]
    row_valid = [
        'ID3', 'B3', 'Loans', 'Amortised cost', 'AC', 'false',
        '0.1', '0.2', '0.5', '1000', 'false', '0.05',
        'false', '', '', '', '2020-01-01', '2021-01-01',
    ]
    row_err = [
        'ID4', 'B4', 'Loans', 'Amortised cost', 'AC', 'false',
        '', '0.2', '0.5', '1000', 'false', '0.05',
        'false', '', '', '', '2020-01-01', '2021-01-01',
    ]
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(row_valid)
        writer.writerow(row_err)
    with open(csv_file, 'rb') as f:
        client.post('/upload_instruments', files={'file': ('instruments.csv', f, 'text/csv')})

    res_all = client.get('/instruments')
    assert len(res_all.json()) == 2
    res_err = client.get('/instruments', params={'error': 'true'})
    assert len(res_err.json()) == 1
    res_noerr = client.get('/instruments', params={'error': 'false'})
    assert len(res_noerr.json()) == 1