from typing import List

import pandas as pd
from fastapi import HTTPException, UploadFile

from .schemas import InstrumentCreate


def parse_instrument_file(upload_file: UploadFile) -> List[InstrumentCreate]:
    """Parse CSV or Excel upload and return a list of InstrumentCreate schemas."""
    filename = upload_file.filename or ""
    data = upload_file.file

    if filename.lower().endswith(".csv"):
        df = pd.read_csv(data)
    elif filename.lower().endswith(('.xls', '.xlsx')):
        df = pd.read_excel(data)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type; must be CSV or Excel")

    required = ["PD", "LGD", "EAD"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    if df[required].isnull().any().any():
        raise HTTPException(status_code=400, detail="Null values found in required columns")

    instruments: List[InstrumentCreate] = []
    for row in df.itertuples(index=False):
        raw_pd = str(getattr(row, "PD"))
        raw_lgd = str(getattr(row, "LGD"))
        raw_ead = str(getattr(row, "EAD"))
        try:
            pd_val = float(raw_pd)
            lgd_val = float(raw_lgd)
            ead_val = float(raw_ead)
        except ValueError:
            raise HTTPException(status_code=400, detail="PD, LGD, and EAD values must be numeric")
        if not (0.0 <= pd_val <= 1.0):
            raise HTTPException(status_code=400, detail=f"PD must be between 0 and 1, got {pd_val}")
        if not (0.0 <= lgd_val <= 1.0):
            raise HTTPException(status_code=400, detail=f"LGD must be between 0 and 1, got {lgd_val}")
        if ead_val < 0.0:
            raise HTTPException(status_code=400, detail=f"EAD must be non-negative, got {ead_val}")
        instruments.append(
            InstrumentCreate(
                raw_pd=raw_pd,
                raw_lgd=raw_lgd,
                raw_ead=raw_ead,
                pd=pd_val,
                lgd=lgd_val,
                ead=ead_val,
            )
        )
    return instruments