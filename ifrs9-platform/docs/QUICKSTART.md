# IFRS 9 Platform - Quick Start Guide

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

## Step 1: Start Infrastructure Services

```bash
# Start infrastructure services
cd ifrs9-platform
docker-compose up -d db redis rabbitmq minio

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME                    STATUS
ifrs9-platform-db-1     Up
ifrs9-platform-redis-1  Up
ifrs9-platform-rabbitmq-1 Up
ifrs9-platform-minio-1  Up
```

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Step 3: Run Database Migrations

```bash
# Run migrations to create all tables
alembic upgrade head

# Verify migration
alembic current
# Should show: 001 (head)
```

## Step 4: Start API Server

```bash
# Start FastAPI server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 5: Access API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health

## Step 6: Load Sample Data

### Option A: Using Swagger UI

1. Go to http://localhost:8000/api/docs
2. Navigate to **POST /api/v1/imports/customer-data**
3. Click "Try it out"
4. Upload `docs/sample_data/customers.csv`
5. Click "Execute"

Repeat for:
- **POST /api/v1/imports/loan-portfolio** with `loans.csv`
- **POST /api/v1/imports/macro-scenarios** with `scenarios.csv`

### Option B: Using cURL

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

## Step 7: Test Core Functionality

### Classify an Instrument

```bash
curl -X POST "http://localhost:8000/api/v1/classification/classify" \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": "LOAN001"}'
```

Expected response:
```json
{
  "instrument_id": "LOAN001",
  "classification": "AMORTIZED_COST",
  "business_model": "HOLD_TO_COLLECT",
  "sppi_passed": true,
  "rationale": "..."
}
```

### Determine Stage

```bash
curl -X POST "http://localhost:8000/api/v1/staging/determine-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN002",
    "reporting_date": "2024-03-31"
  }'
```

Expected response (LOAN002 has 35 DPD, should be Stage 2):
```json
{
  "instrument_id": "LOAN002",
  "stage": "STAGE_2",
  "previous_stage": "STAGE_1",
  "reason": "SICR detected: DPD > 30 days",
  "sicr_detected": true,
  "sicr_indicators": ["DPD_THRESHOLD"],
  "credit_impaired": false
}
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

Expected response:
```json
{
  "calculation_id": "...",
  "instrument_id": "LOAN001",
  "stage": "STAGE_1",
  "ecl_amount": 95000.00,
  "time_horizon": "12_MONTH",
  "pd": 0.02,
  "lgd": 0.45,
  "ead": 10000000.00,
  "scenario_results": {}
}
```

### Calculate Portfolio ECL

```bash
curl -X POST "http://localhost:8000/api/v1/ecl/calculate-portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "reporting_date": "2024-03-31"
  }'
```

Expected response:
```json
{
  "reporting_date": "2024-03-31",
  "instruments_calculated": 10,
  "total_ecl": 2500000.00,
  "stage_totals": {
    "STAGE_1": 1000000.00,
    "STAGE_2": 800000.00,
    "STAGE_3": 700000.00
  }
}
```

### View Audit Trail

```bash
curl "http://localhost:8000/api/v1/audit/instrument/LOAN001"
```

## Step 8: Explore the Platform

### Sample Data Overview

The sample data includes:
- **5 customers**: Mix of RETAIL, SME, and CORPORATE
- **10 loans**: Various stages (0-120 days past due)
- **3 macro scenarios**: Base, Upside, Downside

### Loan Characteristics

| Loan ID | Customer | Amount | DPD | Expected Stage |
|---------|----------|--------|-----|----------------|
| LOAN001 | CUST001  | 10M    | 0   | Stage 1        |
| LOAN002 | CUST002  | 5M     | 35  | Stage 2 (SICR) |
| LOAN005 | CUST005  | 1M     | 95  | Stage 3 (Impaired) |
| LOAN010 | CUST005  | 800K   | 120 | Stage 3 (Impaired) |

### Test Scenarios

1. **Stage 1 → Stage 2 Transition**: LOAN002 (35 DPD triggers SICR)
2. **Stage 3 Credit Impairment**: LOAN005, LOAN010 (>90 DPD)
3. **Portfolio ECL**: Calculate total ECL across all instruments
4. **Scenario Weighting**: Test with multiple macro scenarios

## Troubleshooting

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose ps db

# View logs
docker-compose logs db

# Restart if needed
docker-compose restart db
```

### Migration Error

```bash
# Check current migration status
alembic current

# If stuck, reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

### API Server Error

```bash
# Check logs
docker-compose logs api

# Verify Python dependencies
pip install -e .

# Check database connection
python -c "from src.db.session import SessionLocal; db = SessionLocal(); print('Connected!')"
```

### Import Fails

Common issues:
- **CSV format**: Ensure headers match exactly
- **Date format**: Use YYYY-MM-DD format
- **Enum values**: Use exact enum names (e.g., "LOAN", "CORPORATE")
- **Required fields**: All required fields must be present

## Next Steps

1. **Explore API Documentation**: http://localhost:8000/api/docs
2. **Review Architecture**: See `docs/MVP_STATUS.md`
3. **Read API Guide**: See `docs/API_GUIDE.md`
4. **Check Database**: Use pgAdmin or psql to inspect tables
5. **Monitor Logs**: Watch application logs for errors

## Production Deployment

For production deployment:
1. Set environment variables in `.env` file
2. Configure proper database credentials
3. Enable authentication (JWT tokens)
4. Set up SSL/TLS certificates
5. Configure rate limiting
6. Set up monitoring and alerting
7. Review security settings

See `docs/DATABASE_SETUP.md` for more details.

## Support

- **API Documentation**: http://localhost:8000/api/docs
- **Spec Files**: `.kiro/specs/ifrs9-platform-uganda/`
- **Database Schema**: `alembic/versions/001_initial_schema.py`
- **Service Code**: `src/services/`

## Summary

You now have a fully functional IFRS 9 platform with:
- ✅ Data import (CSV/JSON)
- ✅ Classification engine
- ✅ Staging engine (SICR detection)
- ✅ ECL calculation (12-month & lifetime)
- ✅ Audit trail
- ✅ REST API with Swagger documentation
- ✅ Sample data for testing

The platform is ready for testing and further development!
