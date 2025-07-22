from typing import List

from sqlalchemy.orm import Session

from . import models, schemas


def create_instrument(db: Session, instrument: schemas.InstrumentCreate) -> models.Instrument:
    db_instr = models.Instrument(
        raw_pd=instrument.raw_pd,
        raw_lgd=instrument.raw_lgd,
        raw_ead=instrument.raw_ead,
        pd=instrument.pd,
        lgd=instrument.lgd,
        ead=instrument.ead,
    )
    db.add(db_instr)
    db.commit()
    db.refresh(db_instr)
    return db_instr


def get_instruments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Instrument]:
    return db.query(models.Instrument).offset(skip).limit(limit).all()


def create_upload_history(
    db: Session, filename: str, inserted: int
) -> models.UploadHistory:
    db_hist = models.UploadHistory(filename=filename, inserted=inserted)
    db.add(db_hist)
    db.commit()
    db.refresh(db_hist)
    return db_hist


def get_upload_history(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.UploadHistory]:
    return db.query(models.UploadHistory).offset(skip).limit(limit).all()