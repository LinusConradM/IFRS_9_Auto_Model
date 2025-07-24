from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.instruments import router as instruments_router

app = FastAPI(title="IFRS 9 Automation Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instruments_router)


@app.on_event("startup")
def on_startup():
    from db.session import engine, Base
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def read_root():
    return {"message": "Welcome to IFRS 9 Automation Platform"}