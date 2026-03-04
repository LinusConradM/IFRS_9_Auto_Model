# IFRS 9 Platform API Guide

## Quick Start

### 1. Start the Platform

```bash
# Start infrastructure services
cd ifrs9-platform
docker-compose up -d postgres redis rabbitmq minio

# Run database migrations
alembic upgrade head

# Start API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **API Info**: http://localhost:8000/api/v1/info

## API Endpoints

### Data Import

#### Import Loan Portfolio
```http
POST /api/v1/imports/loan-portfolio
Content-Type: multipart/form-data

file: loan_portfolio.csv
auto_approve: false
```

**CSV Format:**
```csv
instrument_id,customer_id,instrument_type,principal_amount,outstanding_balance,interest_rate,origination_date,maturity_date,days_past_due
LOAN001,CUST001,LOAN,1000000,950000,12.5,2023-01-15,2028-01-15,0
```

**Response:**
```json
{
  "import_id": "uuid",
  "status": "completed",
  "records_processed": 100,
  "records_imported": 98,
  "records_failed": 2,
  "errors": []
}
```

#### Import Customer Data
```http
POST /api/v1/imports/customer-data
Content-Type: multipart/form-data

file: customers.csv
```

**CSV Format:**
```csv
customer_id,name,customer_type,sector,credit_rating,country
CUST001,ABC Company Ltd,CORPORATE,Manufacturing,BBB,Uganda
```

#### Import Macro Scenarios
```http
POST /api/v1/imports/macro-scenarios
Content-Type: multipart/form-data

file: scenarios.csv
```

**CSV Format:**
```csv
scenario_name,scenario_type,probability_weight,gdp_growth,inflation_rate,unemployment_rate,interest_rate,effective_date
Base Case,BASE,0.6,5.0,5.0,5.0,10.0,2024-01-01
```

### Classification

#### Classify Instrument
```http
POST /api/v1/classification/classify
Content-Type: application/json

{
  "instrument_id": "LOAN001"
}
```

**Response:**
```json
{
  "instrument_id": "LOAN001",
  "classification": "AMORTIZED_COST",
  "business_model": "HOLD_TO_COLLECT",
  "sppi_passed": true,
  "rationale": "Standard loan with SPPI cash flows, held to collect"
}
```

#### Get Classification Rationale
```http
GET /api/v1/classification/{instrument_id}/rationale
```

### Staging

#### Determine Stage
```http
POST /api/v1/staging/determine-stage
Content-Type: application/json

{
  "instrument_id": "LOAN001",
  "reporting_date": "2024-03-31"
}
```

**Response:**
```json
{
  "instrument_id": "LOAN001",
  "stage": "STAGE_2",
  "previous_stage": "STAGE_1",
  "reason": "SICR detected: DPD > 30 days",
  "sicr_detected": true,
  "sicr_indicators": ["DPD_THRESHOLD"],
  "credit_impaired": false
}
```

#### Evaluate SICR
```http
POST /api/v1/staging/evaluate-sicr/{instrument_id}?reporting_date=2024-03-31
```

#### Get Stage Transitions
```http
GET /api/v1/staging/transitions?instrument_id=LOAN001&limit=50
```

### ECL Calculation

#### Calculate ECL for Single Instrument
```http
POST /api/v1/ecl/calculate
Content-Type: application/json

{
  "instrument_id": "LOAN001",
  "reporting_date": "2024-03-31",
  "scenarios": [
    {
      "scenario_id": "base",
      "weight": 0.6,
      "adjustment": 1.0
    },
    {
      "scenario_id": "downside",
      "weight": 0.4,
      "adjustment": 1.5
    }
  ]
}
```

**Response:**
```json
{
  "calculation_id": "uuid",
  "instrument_id": "LOAN001",
  "stage": "STAGE_2",
  "ecl_amount": 45000.00,
  "time_horizon": "LIFETIME",
  "pd": 0.05,
  "lgd": 0.45,
  "ead": 950000.00,
  "scenario_results": {
    "base": 40000.00,
    "downside": 60000.00
  }
}
```

#### Calculate Portfolio ECL
```http
POST /api/v1/ecl/calculate-portfolio
Content-Type: application/json

{
  "reporting_date": "2024-03-31",
  "instrument_ids": null
}
```

**Response:**
```json
{
  "reporting_date": "2024-03-31",
  "instruments_calculated": 1000,
  "total_ecl": 5000000.00,
  "stage_totals": {
    "STAGE_1": 1000000.00,
    "STAGE_2": 2500000.00,
    "STAGE_3": 1500000.00
  }
}
```

#### Get ECL Calculations
```http
GET /api/v1/ecl/calculations?instrument_id=LOAN001&limit=10
```

#### Get Specific Calculation
```http
GET /api/v1/ecl/calculations/{calculation_id}
```

### Audit Trail

#### Get Audit Entries
```http
GET /api/v1/audit/entries?entity_type=FinancialInstrument&entity_id=LOAN001&limit=100
```

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2024-03-31T10:30:00",
    "user_id": "system_user",
    "action": "CLASSIFICATION",
    "entity_type": "FinancialInstrument",
    "entity_id": "LOAN001",
    "before_state": null,
    "after_state": {
      "classification": "AMORTIZED_COST",
      "business_model": "HOLD_TO_COLLECT"
    },
    "changes": null,
    "ip_address": "127.0.0.1"
  }
]
```

#### Get Instrument Audit Trail
```http
GET /api/v1/audit/instrument/{instrument_id}
```

**Response:**
```json
{
  "entity_type": "FinancialInstrument",
  "entity_id": "LOAN001",
  "total_actions": 15,
  "actions_by_type": {
    "CLASSIFICATION": 1,
    "STAGE_TRANSITION": 3,
    "ECL_CALCULATION": 11
  },
  "users": ["system_user", "admin"],
  "timeline": [...]
}
```

#### Get User Audit Trail
```http
GET /api/v1/audit/user/{user_id}?limit=50
```

## Complete Workflow Example

### 1. Import Data
```bash
# Import customers
curl -X POST "http://localhost:8000/api/v1/imports/customer-data" \
  -F "file=@customers.csv"

# Import loan portfolio
curl -X POST "http://localhost:8000/api/v1/imports/loan-portfolio" \
  -F "file=@loans.csv" \
  -F "auto_approve=true"

# Import macro scenarios
curl -X POST "http://localhost:8000/api/v1/imports/macro-scenarios" \
  -F "file=@scenarios.csv"
```

### 2. Classify Instruments
```bash
curl -X POST "http://localhost:8000/api/v1/classification/classify" \
  -H "Content-Type: application/json" \
  -d '{"instrument_id": "LOAN001"}'
```

### 3. Determine Stages
```bash
curl -X POST "http://localhost:8000/api/v1/staging/determine-stage" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "reporting_date": "2024-03-31"
  }'
```

### 4. Calculate ECL
```bash
curl -X POST "http://localhost:8000/api/v1/ecl/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "reporting_date": "2024-03-31"
  }'
```

### 5. Calculate Portfolio ECL
```bash
curl -X POST "http://localhost:8000/api/v1/ecl/calculate-portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "reporting_date": "2024-03-31"
  }'
```

### 6. Review Audit Trail
```bash
curl "http://localhost:8000/api/v1/audit/instrument/LOAN001"
```

## Error Handling

All endpoints return standard HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid input data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Testing with Sample Data

Create sample CSV files:

**customers.csv:**
```csv
customer_id,name,customer_type,sector,credit_rating,country
CUST001,ABC Company Ltd,CORPORATE,Manufacturing,BBB,Uganda
CUST002,XYZ Traders,SME,Retail,BB,Uganda
```

**loans.csv:**
```csv
instrument_id,customer_id,instrument_type,principal_amount,outstanding_balance,interest_rate,origination_date,maturity_date,days_past_due
LOAN001,CUST001,LOAN,1000000,950000,12.5,2023-01-15,2028-01-15,0
LOAN002,CUST002,LOAN,500000,480000,15.0,2023-06-01,2026-06-01,35
```

**scenarios.csv:**
```csv
scenario_name,scenario_type,probability_weight,gdp_growth,inflation_rate,unemployment_rate,interest_rate,effective_date
Base Case,BASE,0.6,5.0,5.0,5.0,10.0,2024-01-01
Upside,UPSIDE,0.2,7.0,4.0,4.0,9.0,2024-01-01
Downside,DOWNSIDE,0.2,2.0,8.0,8.0,12.0,2024-01-01
```

## Next Steps

1. Test all endpoints with sample data
2. Implement authentication (JWT tokens)
3. Add rate limiting
4. Set up monitoring and logging
5. Deploy to production environment

## Support

For issues or questions:
- Check API documentation: http://localhost:8000/api/docs
- Review logs in Docker containers
- Refer to spec files in `.kiro/specs/ifrs9-platform-uganda/`
