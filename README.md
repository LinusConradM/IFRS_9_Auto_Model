# IFRS_9_Auto_Model

Instrument Upload & Summary Service

This project provides a FastAPI backend and a React frontend to upload financial instrument data and view a clean summary. Data is persisted in PostgreSQL.

## Features

- **API**
-   `POST /upload` — Upload instrument data (CSV or Excel)
-   `GET /instruments` — List uploaded instruments
- **Frontend**
-   React-based UI for file upload and table preview
- **Database**
-   PostgreSQL table storing raw and normalized fields
- **Tests**
-   pytest-based tests for upload & persistence
- **Upload History**
-   Track each upload (filename, record count, timestamp)
- **Advanced Validation**
-   Ensure PD & LGD ∈ [0,1], EAD ≥ 0
- **CORS**
-   Configurable cross-origin support

## Tech Stack

- Python, FastAPI
- React (no build step, uses CDN)
- PostgreSQL
- pytest for testing
- Docker & Docker Compose for containerized deployment

## Setup

### Prerequisites

- Python 3.8+
- NumPy <2 (required for pandas compatibility)
- PostgreSQL
- PostgreSQL
- (Optional) Node.js if you plan to integrate/build the frontend differently

### Back-end

1. Copy `.env.example` → `.env` and update `DATABASE_URL`
2. Create virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Front-end

The frontend is served by the backend. With the server running on http://localhost:8000, navigate to that URL in your browser to access the UI.

### Tests

```bash
cd backend
pytest
```

## Environment Example

Create a `.env` file based on this example:
```
DATABASE_URL=postgresql://username:password@db:5432/yourdb
CORS_ORIGINS=*
```

## Docker & Deployment

A Dockerfile and `docker-compose.yml` are provided for easy setup:

```bash
# Build and start services
docker-compose up --build
```

This will launch:
- **db**: PostgreSQL on port 5432
- **web**: FastAPI service with React UI on port 8000