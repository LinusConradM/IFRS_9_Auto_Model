# Option A - Quick Start Guide

**Status:** ✅ Ready to Use  
**Date:** March 4, 2026

## What's Ready

All Phase 1 critical path APIs are implemented and ready for testing:
- ✅ Authentication API (JWT tokens, login/logout)
- ✅ Staging Override API (request/approve/reject with maker-checker)
- ✅ EAD Calculation API (calculate EAD with CCF)
- ✅ Sample data script (users, customers, instruments, scenarios)
- ✅ Unit tests (20+ tests covering all critical paths)

## Quick Start (3 Steps)

### Step 1: Start the API Server

```bash
cd ifrs9-platform
uvicorn src.api.main:app --reload --port 8000
```

The API will be available at: http://localhost:8000

### Step 2: Create Sample Data

```bash
cd ifrs9-platform
python scripts/create_sample_data.py
```

This creates:
- 5 test users (admin, maker, checker, analyst, viewer)
- 5 sample customers
- 5 financial instruments
- 3 macro scenarios

### Step 3: Test the APIs

#### Option A: Use Swagger UI
Open http://localhost:8000/api/docs in your browser

#### Option B: Use curl

**1. Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=maker1&password=Maker@123456"
```

Save the `access_token` from the response.

**2. Request Staging Override:**
```bash
curl -X POST http://localhost:8000/api/v1/staging/overrides \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "override_stage": "STAGE_2",
    "justification": "Customer experiencing temporary cash flow issues due to delayed receivables"
  }'
```

**3. Calculate EAD:**
```bash
curl -X POST http://localhost:8000/api/v1/ead/calculate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": "LOAN001",
    "facility_type": "TERM_LOAN",
    "outstanding_balance": "100000.00",
    "undrawn_commitment": "50000.00",
    "reporting_date": "2026-03-04"
  }'
```

## Test Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | Admin@123456 |
| Maker | maker1 | Maker@123456 |
| Checker | checker1 | Checker@123456 |
| Analyst | analyst1 | Analyst@123456 |
| Viewer | viewer1 | Viewer@123456 |

## Sample Data

### Customers
- CUST001: ABC Manufacturing Ltd (Corporate, BBB)
- CUST002: XYZ Trading Company (SME, BB)
- CUST003: John Doe (Retail, A)
- CUST004: Tech Innovations Ltd (Corporate, AA)
- CUST005: Green Agriculture Co (SME, BBB)

### Financial Instruments
- LOAN001: Term Loan, UGX 500,000, Stage 1
- LOAN002: Overdraft, UGX 75,000, Stage 1
- LOAN003: Mortgage, UGX 250,000, Stage 1
- LOAN004: Term Loan, UGX 1,000,000, Stage 2 (35 DPD)
- LOAN005: Working Capital, UGX 150,000, Stage 1

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /login` - Login (returns JWT tokens)
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout
- `GET /me` - Get current user info
- `POST /change-password` - Change password

### Staging Overrides (`/api/v1/staging/overrides`)
- `POST /` - Request staging override
- `GET /` - List overrides (with filters)
- `GET /pending` - Get pending overrides
- `GET /{override_id}` - Get override details
- `POST /{override_id}/approve` - Approve override
- `POST /{override_id}/reject` - Reject override

### EAD Calculation (`/api/v1/ead`)
- `POST /calculate` - Calculate EAD
- `GET /ccf` - Get CCF configuration
- `POST /ccf` - Update CCF configuration
- `GET /off-balance-sheet` - List off-balance sheet exposures

## Run Unit Tests

```bash
cd ifrs9-platform
pytest tests/test_phase1_critical.py -v
```

Expected: 20+ tests passing

## Troubleshooting

### Database Connection Error
Make sure PostgreSQL is running on port 5433:
```bash
docker-compose up -d postgres
```

### Import Errors
Make sure you're in the ifrs9-platform directory and dependencies are installed:
```bash
cd ifrs9-platform
pip install -e .
```

### Authentication Errors
Make sure you've created sample data first:
```bash
python scripts/create_sample_data.py
```

## Next Steps

1. **Frontend Integration**: Connect React components to these APIs
2. **Additional APIs**: Implement remaining Phase 1 service APIs
3. **Integration Tests**: Test with real database and workflows
4. **Performance Testing**: Load test the APIs
5. **Monitoring**: Add logging and metrics

## Documentation

- Full API docs: http://localhost:8000/api/docs
- Implementation details: `docs/OPTION_A_IMPLEMENTATION_SUMMARY.md`
- Phase 1 services: `docs/PHASE1_SERVICES_COMPLETED.md`

## Support

For issues or questions:
1. Check the API documentation at `/api/docs`
2. Review the implementation summary
3. Check the test suite for examples
4. Review service implementations in `src/services/`
