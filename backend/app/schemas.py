from datetime import datetime

from pydantic import BaseModel


class InstrumentBase(BaseModel):
    raw_pd: str
    raw_lgd: str
    raw_ead: str
    pd: float
    lgd: float
    ead: float


class InstrumentCreate(InstrumentBase):
    pass


class Instrument(InstrumentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class UploadHistory(BaseModel):
    id: int
    filename: str
    inserted: int
    uploaded_at: datetime

    class Config:
        orm_mode = True