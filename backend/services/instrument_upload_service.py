import io
import csv
import hashlib
from datetime import datetime

try:
    import openpyxl
except ImportError:
    openpyxl = None
from fastapi import UploadFile
from sqlalchemy.orm import Session

from db.models import (
    UploadHistory,
    RawInstrument,
    ValidatedInstrument,
)


def _parse_bool(val, field, errors):
    if isinstance(val, bool):
        return val
    txt = str(val).strip().lower()
    if txt in ('true', '1', 'yes'):
        return True
    if txt in ('false', '0', 'no'):
        return False
    errors.append(f'Invalid boolean for {field}')
    return None


def _parse_float(val, field, errors, minv=None, maxv=None):
    try:
        f = float(val)
    except Exception:
        errors.append(f'Invalid float for {field}')
        return None
    if minv is not None and f < minv or maxv is not None and f > maxv:
        errors.append(f'{field} out of bounds [{minv},{maxv}]')
    return f


def _parse_date(val, field, errors):
    try:
        # expect ISO format date
        return datetime.fromisoformat(str(val)).date()
    except Exception:
        errors.append(f'Invalid date for {field}')
        return None


def process_instrument_upload(
    db: Session,
    file: UploadFile,
    uploaded_by: str = None,
    schema_version: str = 'v1',
):
    """
    Parse, validate and persist instrument upload.
    Returns upload summary and preview of rows with errors.
    """
    bind = db.get_bind()
    from sqlalchemy import inspect
    from db.session import Base
    if not inspect(bind).has_table(UploadHistory.__tablename__):
        Base.metadata.create_all(bind=bind)
    file.file.seek(0)
    content = file.file.read()
    checksum = hashlib.md5(content).hexdigest()
    filename = file.filename or 'unknown'

    rows = []
    file.file.seek(0)
    if filename.lower().endswith('.xlsx'):
        if openpyxl is None:
            raise ValueError('XLSX support requires openpyxl')
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        try:
            headers = [str(h) for h in next(it)]
        except StopIteration:
            raise ValueError('Empty XLSX file')
        for row in it:
            rows.append({headers[i]: row[i] for i in range(len(headers))})
    elif filename.lower().endswith('.csv'):
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            rows.append(row)
    else:
        raise ValueError('Unsupported file type')

    required = [
        'instrument_id', 'borrower_id', 'asset_class',
        'classification_category', 'measurement_basis', 'off_balance_flag',
        'pd_12m', 'pd_lifetime', 'lgd', 'ead', 'sicr_flag', 'eir',
        'collateral_flag', 'drawdown_date', 'maturity_date',
    ]
    preview = []
    seen_ids = set()
    for idx, row in enumerate(rows, start=1):
        errors = []
        raw = {k: row.get(k) for k in row}
        # required fields
        for field in required:
            if row.get(field) in (None, ''):
                errors.append(f'Missing {field}')
        inst_id = row.get('instrument_id')
        if inst_id:
            if inst_id in seen_ids:
                errors.append('Duplicate instrument_id')
            seen_ids.add(inst_id)
            inst_bind = db.get_bind()
            from sqlalchemy import inspect

            if inspect(inst_bind).has_table(ValidatedInstrument.__tablename__):
                exists = db.query(ValidatedInstrument).filter_by(instrument_id=inst_id).first()
                if exists:
                    errors.append('instrument_id already exists')
        collateral_flag = _parse_bool(row.get('collateral_flag'), 'collateral_flag', errors)
        if collateral_flag:
            # cross-validate collateral details
            for f in ('collateral_type', 'collateral_value', 'appraisal_date'):
                if row.get(f) in (None, ''):
                    errors.append(f'Missing {f} for collateral_flag')
        draw = _parse_date(row.get('drawdown_date'), 'drawdown_date', errors)
        mat = _parse_date(row.get('maturity_date'), 'maturity_date', errors)
        if draw and mat and mat <= draw:
            errors.append('maturity_date must be after drawdown_date')
        _parse_float(row.get('pd_12m'), 'pd_12m', errors, 0, 1)
        _parse_float(row.get('pd_lifetime'), 'pd_lifetime', errors, 0, 1)
        _parse_float(row.get('lgd'), 'lgd', errors)
        _parse_float(row.get('ead'), 'ead', errors)
        _parse_float(row.get('eir'), 'eir', errors)
        _parse_bool(row.get('sicr_flag'), 'sicr_flag', errors)
        _parse_bool(row.get('off_balance_flag'), 'off_balance_flag', errors)

        preview.append({'row_number': idx, 'raw_data': raw, 'errors': errors})

    total = len(preview)
    valid = sum(1 for r in preview if not r['errors'])
    invalid = total - valid

    upload = UploadHistory(
        filename=filename,
        checksum=checksum,
        uploaded_by=uploaded_by,
        schema_version=schema_version,
        total_rows=total,
        valid_rows=valid,
        invalid_rows=invalid,
    )
    db.add(upload)
    db.flush()  # get upload_id
    for r in preview:
        db.add(RawInstrument(
            upload_id=upload.upload_id,
            row_number=r['row_number'],
            raw_data=r['raw_data'],
            errors=r['errors'] or None,
        ))
        if not r['errors']:
            data = r['raw_data']
            db.add(ValidatedInstrument(
                upload_id=upload.upload_id,
                instrument_id=data.get('instrument_id'),
                borrower_id=data.get('borrower_id'),
                asset_class=data.get('asset_class'),
                classification_category=data.get('classification_category'),
                measurement_basis=data.get('measurement_basis'),
                off_balance_flag=_parse_bool(data.get('off_balance_flag'), 'off_balance_flag', []),
                pd_12m=float(data.get('pd_12m')),
                pd_lifetime=float(data.get('pd_lifetime')),
                lgd=float(data.get('lgd')),
                ead=float(data.get('ead')),
                sicr_flag=_parse_bool(data.get('sicr_flag'), 'sicr_flag', []),
                eir=float(data.get('eir')),
                collateral_flag=_parse_bool(data.get('collateral_flag'), 'collateral_flag', []),
                collateral_type=data.get('collateral_type'),
                collateral_value=(None if data.get('collateral_value') in (None, '')
                                   else float(data.get('collateral_value'))),
                appraisal_date=_parse_date(data.get('appraisal_date'), 'appraisal_date', []),
                drawdown_date=_parse_date(data.get('drawdown_date'), 'drawdown_date', []),
                maturity_date=_parse_date(data.get('maturity_date'), 'maturity_date', []),
            ))
    db.commit()
    return {
        'upload_id': upload.upload_id,
        'filename': upload.filename,
        'checksum': upload.checksum,
        'total_rows': upload.total_rows,
        'valid_rows': upload.valid_rows,
        'invalid_rows': upload.invalid_rows,
        'preview': preview,
    }