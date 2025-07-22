from fastapi import FastAPI

app = FastAPI(title="IFRS 9 Automation Platform")

@app.get("/")
async def read_root():
    return {"message": "Welcome to IFRS 9 Automation Platform"}