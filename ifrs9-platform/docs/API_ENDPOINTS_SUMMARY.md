# API Endpoints Summary

## Completed API Endpoints

### 1. Data Import (`/api/v1/imports`)
- `POST /loan-portfolio` - Import loan portfolio with approval workflow
- `POST /customer-data` - Import customer master data
- `POST /macro-scenarios` - Import macroeconomic scenarios
- `GET /{import_id}` - Get import status
- `POST /{import_id}/approve` - Approve pending import
- `POST /{import_id}/reject` - Reject pending import

### 2. Classification (`/api/v1/classification`)
- `POST /classify` - Classify single instrument
- `POST /reclassify/{instrument_id}` - Reclassify instrument
- `GET /{instrument_id}/rationale` - Get classification rationale

### 3. Staging (`/api/v1/staging`)
- `POST /determine-stage` - Determine stage for instrument
- `POST /evaluate-sicr/{instrument_id}` - Evaluate SICR
- `GET /transitions` - List stage transitions
- `POST /manual-override/{instrument_id}` - Manual stage override

### 4. ECL Calculation (`/api/v1/ecl`)
- `POST /calculate` - Calculate ECL for single instrument
- `POST /calculate-portfolio` - Bulk ECL calculation
- `GET /calculations` - List ECL calculations
- `GET /calculations/{calculation_id}` - Get specific calculation
- `POST /recalculate/{instrument_id}` - Recalculate ECL
- `GET /jobs/{job_id}` - Get async job status

### 5. Instruments (`/api/v1/instruments`)
- `GET /` - List all instruments with filters
- `GET /{instrument_id}` - Get specific instrument
- `POST /` - Create new instrument
- `PUT /{instrument_id}` - Update instrument
- `DELETE /{instrument_id}` - Soft delete instrument
- `GET /{instrument_id}/history` - Get complete history
- `GET /{instrument_id}/ecl-calculations` - Get ECL history
- `GET /{instrument_id}/stage-transitions` - Get stage transition history

### 6. Parameters (`/api/v1/parameters`) ✨ NEW
- `GET /` - List all parameters with filters
  - Filter by: parameter_type, customer_segment
  - Returns: PD, LGD, EAD, SICR_THRESHOLD parameters
- `POST /` - Create new parameter
  - Required: parameter_type, effective_date, parameter_value
  - Optional: expiry_date, customer_segment, product_type

### 7. Scenarios (`/api/v1/scenarios`) ✨ NEW
- `GET /` - List all macroeconomic scenarios
  - Filter by: effective_date
  - Returns: scenario details with probability weights
- `POST /` - Create new scenario
  - Required: scenario_name, effective_date, probability_weight
  - Optional: gdp_growth_rate, inflation_rate

### 8. Reporting (`/api/v1/reports`) ✨ NEW
- `GET /portfolio-summary` - Portfolio summary metrics
  - Returns: total exposure, ECL, coverage ratios, stage distribution
- `GET /ecl-reconciliation` - ECL reconciliation report
  - Parameters: start_date, end_date
  - Returns: opening ECL, closing ECL, movements, stage transitions
- `GET /regulatory/monthly-impairment` - Monthly impairment report for Bank of Uganda
  - Returns: ECL by stage, coverage ratios, exposure breakdown
- `GET /dashboard-metrics` - Real-time dashboard metrics
  - Returns: current portfolio status, high-risk instruments

### 9. Audit Trail (`/api/v1/audit`)
- `GET /entries` - List audit entries with filters
- `GET /entries/{audit_id}` - Get specific audit entry
- `GET /instrument/{instrument_id}` - Audit trail for instrument
- `GET /user/{user_id}` - Audit trail for user
- `POST /search` - Advanced audit search

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **API Info**: http://localhost:8000/api/v1/info

## Authentication

Currently using placeholder authentication (`system_user`). 
Production authentication with JWT will be implemented in Task 3.1.

## Testing the New Endpoints

### Test Parameters Endpoint
```bash
# List all parameters
curl http://localhost:8000/api/v1/parameters

# Create PD parameter
curl -X POST http://localhost:8000/api/v1/parameters \
  -H "Content-Type: application/json" \
  -d '{
    "parameter_type": "PD",
    "effective_date": "2026-01-01",
    "customer_segment": "RETAIL",
    "parameter_value": 0.02
  }'
```

### Test Scenarios Endpoint
```bash
# List all scenarios
curl http://localhost:8000/api/v1/scenarios

# Create scenario
curl -X POST http://localhost:8000/api/v1/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "Base Case",
    "effective_date": "2026-01-01",
    "probability_weight": 0.6,
    "gdp_growth_rate": {"2026": 5.0, "2027": 5.5},
    "inflation_rate": {"2026": 3.0, "2027": 3.2}
  }'
```

### Test Reporting Endpoints
```bash
# Portfolio summary
curl http://localhost:8000/api/v1/reports/portfolio-summary

# ECL reconciliation
curl "http://localhost:8000/api/v1/reports/ecl-reconciliation?start_date=2026-01-01&end_date=2026-03-04"

# Monthly impairment report
curl "http://localhost:8000/api/v1/reports/regulatory/monthly-impairment?reporting_date=2026-03-04"

# Dashboard metrics
curl http://localhost:8000/api/v1/reports/dashboard-metrics
```

## Next Steps

1. ✅ Parameters management - COMPLETE
2. ✅ Scenarios management - COMPLETE
3. ✅ Reporting endpoints - COMPLETE
4. ⏸️ Test all endpoints with real data
5. ⏸️ Implement authentication (Task 3.1)
6. ⏸️ Add frontend UI for parameters and scenarios
7. ⏸️ Add frontend UI for reports

## MVP Status

**API Layer: 90% Complete** 🎉

All critical endpoints for MVP are now implemented:
- ✅ Data import with approval workflow
- ✅ Classification and staging
- ✅ ECL calculation
- ✅ Parameter management
- ✅ Scenario management
- ✅ Regulatory reporting
- ✅ Audit trail
- ⏸️ Authentication (placeholder only)
