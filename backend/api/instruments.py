from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
import sqlalchemy as sa
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import RawInstrument
from services.instrument_upload_service import process_instrument_upload
from db.schemas import RawInstrumentSchema

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload_instruments")
async def upload_instruments(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        result = process_instrument_upload(db, file)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instruments", response_model=List[RawInstrumentSchema])
def list_instruments(
    asset_class: Optional[str] = Query(None),
    classification_category: Optional[str] = Query(None),
    off_balance_flag: Optional[bool] = Query(None),
    error: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(RawInstrument)
    if asset_class:
        query = query.filter(RawInstrument.raw_data['asset_class'].astext == asset_class)
    if classification_category:
        query = query.filter(RawInstrument.raw_data['classification_category'].astext == classification_category)
    if off_balance_flag is not None:
        query = query.filter(RawInstrument.raw_data['off_balance_flag'].astext.cast(sa.Boolean) == off_balance_flag)
    rows = query.order_by(RawInstrument.id).all()
    if error is not None:
        if error:
            rows = [r for r in rows if r.errors]
        else:
            rows = [r for r in rows if not r.errors]
    return rows