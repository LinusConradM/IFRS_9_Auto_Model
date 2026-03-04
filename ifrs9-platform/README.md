# IFRS 9 Automation Platform

Complete IFRS 9 compliance platform for commercial banks in Uganda with professional React dashboard.

## ✅ MVP Complete!

Your platform is ready to use with:
- ✅ Backend API with FastAPI (8 endpoints)
- ✅ React Dashboard with Material-UI
- ✅ Real data imported (3,397 instruments)
- ✅ Database migrated (9 tables)
- ✅ Docker services running (PostgreSQL on port 5433, Redis, RabbitMQ, MinIO)

## Quick Start

### 1. Start the API

```bash
cd ifrs9-platform
./start_api.sh
```

API available at: http://localhost:8000/api/docs

**If you see "Address already in use":**
```bash
lsof -ti:8000 | xargs kill -9
./start_api.sh
```

### 2. Start the Dashboard

```bash
./start_dashboard.sh
```

Dashboard opens at: http://localhost:3000

### 3. Explore Your Data

Open http://localhost:3000 and explore:
- **Dashboard Tab**: Portfolio overview with charts (3,397 instruments)
- **Portfolio Tab**: Search and filter instruments by stage/status
- **ECL Calculator**: Calculate ECL for individual loans

## Dashboard Features

### Dashboard Tab
- Total instruments, exposure, ECL, and coverage ratio
- Stage distribution pie chart
- Exposure by stage bar chart
- Detailed stage breakdown table

### Portfolio Tab
- Search by instrument ID or customer ID
- Filter by stage (1, 2, 3) and status
- Sortable columns
- Pagination for large datasets

### ECL Calculator Tab
- Calculate ECL for individual instruments
- View PD, LGD, EAD components
- See calculation formula breakdown

## API Testing

### Test with Sample Data

```bash
# Import customers
curl -X POST "http://localhost:8000/api/v1/imports/customer-data" \
  -F "file=@docs/sample_data/customers.csv"

# Import loans
curl -X POST "http://localhost:8000/api/v1/imports/loan-portfolio" \
  -F "file=@docs/sample_data/loans.csv" \
  -F "auto_approve=true"

# Import scenarios
curl -X POST "http://localhost:8000/api/v1/imports/macro-scenarios" \
  -F "file=@docs/sample_data/scenarios.csv"
```

### Test Classification

```bash
curl -X POST "http://localhost:8000/api/v1/classification/classify" \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": "LOAN001"}'
```

### Test Staging

```bash
curl -X POST "http://localhost:8000/api/v1/staging/determine-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN002",
    "reporting_date": "2024-03-31"
  }'
```

### Calculate ECL

```bash
curl -X POST "http://localhost:8000/api/v1/ecl/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "reporting_date": "2024-03-31"
  }'
```

### Calculate Portfolio ECL

```bash
curl -X POST "http://localhost:8000/api/v1/ecl/calculate-portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "reporting_date": "2024-03-31"
  }'
```

## Important Note: Port Configuration

**PostgreSQL is running on port 5433** (not 5432) because you have a local PostgreSQL instance on port 5432.

If you need to change this:
1. Edit `docker-compose.yml` - change the db ports
2. Edit `alembic.ini` - update the sqlalchemy.url
3. Edit `start_api.sh` - update the DATABASE_URL

## Documentation

- **Dashboard Guide**: `docs/DASHBOARD_GUIDE.md` - How to use the dashboard
- **Quick Start Guide**: `docs/QUICKSTART.md` - Getting started
- **API Guide**: `docs/API_GUIDE.md` - API endpoints and examples
- **Database Setup**: `docs/DATABASE_SETUP.md` - Database configuration
- **MVP Status**: `docs/MVP_STATUS.md` - Complete feature list
- **Data Import Summary**: `docs/DATA_IMPORT_SUMMARY.md` - Import results

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   React Dashboard                            │
│                   http://localhost:3000                      │
│  - Portfolio overview with charts                            │
│  - Instrument search and filtering                           │
│  - Individual ECL calculator                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│                   http://localhost:8000                      │
├─────────────────────────────────────────────────────────────┤
│  API Routes                                                  │
│  ✅ /api/v1/imports/*      - Data import                    │
│  ✅ /api/v1/classification/* - Classification               │
│  ✅ /api/v1/staging/*      - Staging & SICR                 │
│  ✅ /api/v1/ecl/*          - ECL calculation                │
│  ✅ /api/v1/audit/*        - Audit trail                    │
│  ✅ /api/v1/instruments/*  - Portfolio queries              │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Services                                     │
│  ✅ Classification Service                                   │
│  ✅ Staging Service                                          │
│  ✅ ECL Calculation Service                                  │
│  ✅ Parameter Service                                        │
│  ✅ Macro Scenario Service                                   │
│  ✅ Data Import Service                                      │
│  ✅ Audit Trail Service                                      │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure (Docker)                                     │
│  ✅ PostgreSQL:5433 (database)                               │
│  ✅ Redis:6379 (caching)                                     │
│  ✅ RabbitMQ:5672 (messaging)                                │
│  ✅ MinIO:9000 (storage)                                     │
└─────────────────────────────────────────────────────────────┘
```

## Features Implemented

### Frontend Dashboard
- ✅ React + TypeScript + Material-UI
- ✅ Portfolio overview with charts
- ✅ Instrument search and filtering
- ✅ Individual ECL calculator
- ✅ Real-time data from API

### Core Modules
- ✅ Data Import (CSV/JSON with validation)
- ✅ Classification (Business model + SPPI tests)
- ✅ Staging Engine (SICR detection + transitions)
- ✅ ECL Calculation (12-month & lifetime)
- ✅ Parameter Management (PD/LGD/EAD)
- ✅ Macro Scenarios (Economic adjustments)
- ✅ Audit Trail (Immutable logging)

### IFRS 9 Properties
Implements 18 correctness properties including:
- Property 1-2: Classification
- Property 3-9: Staging & SICR
- Property 10-12: ECL Calculation
- Property 14-16: Data Import
- Property 29-31: Audit Trail

## Troubleshooting

### Database Connection Error

Check if services are running:
```bash
docker-compose ps
```

Restart if needed:
```bash
docker-compose restart db
```

### API Won't Start

Make sure DATABASE_URL is set:
```bash
export DATABASE_URL="postgresql://ifrs9:ifrs9pass@localhost:5433/ifrs9"
```

### Import Fails

Check CSV format matches expected columns. See `docs/API_GUIDE.md` for examples.

## Next Steps

1. ✅ Platform is running with dashboard - explore your data!
2. Customize dashboard (colors, charts, filters)
3. Add authentication (JWT tokens)
4. Implement batch ECL calculations
5. Add data export (Excel/CSV)
6. Deploy to production

## Support

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **Dashboard Guide**: `docs/DASHBOARD_GUIDE.md`
- **Spec Files**: `.kiro/specs/ifrs9-platform-uganda/`
- **Issues**: Check logs with `docker-compose logs`

---

**Platform Status**: ✅ MVP Complete with Dashboard - Ready to Use!
