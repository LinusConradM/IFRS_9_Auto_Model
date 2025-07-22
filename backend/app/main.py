import os
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List


from . import crud, models, schemas, utils
from .database import engine, Base, get_db

Base.metadata.create_all(bind=engine)


app = FastAPI(title="Instrument Upload Service")

# CORS setup
origins = os.getenv("CORS_ORIGINS", "").split(",")
if origins and origins[0] != "":
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.post("/upload")
async def upload_instruments(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """Endpoint to upload a CSV or Excel file of instruments."""
    instruments = utils.parse_instrument_file(file)
    count = 0
    for instr in instruments:
        crud.create_instrument(db, instr)
        count += 1
    # track upload history
    crud.create_upload_history(db, file.filename or "", count)
    return {"inserted": count}


@app.get("/instruments", response_model=List[schemas.Instrument])
def list_instruments(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Retrieve a list of stored instruments."""
    items = crud.get_instruments(db, skip=skip, limit=limit)
    return items


@app.get("/upload-history", response_model=List[schemas.UploadHistory])
def read_upload_history(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Retrieve historical upload records."""
    return crud.get_upload_history(db, skip=skip, limit=limit)