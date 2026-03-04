# Data Import Summary

## Import Completed Successfully ✅

Your borrower data from `test_data/raw_data.xlsx` has been successfully imported into the IFRS 9 Platform database.

## Import Statistics

- **Total Customers**: 977
- **Total Loan Instruments**: 3,397
- **Rows Processed**: 3,397
- **Rows Skipped**: 0

## Data Distribution

### By Customer Type
- **RETAIL**: 744 customers (76%)
- **SME**: 233 customers (24%)

### By IFRS 9 Stage
- **Stage 1** (Performing): 2,842 loans (84%)
- **Stage 2** (Underperforming): 136 loans (4%)
- **Stage 3** (Non-performing): 419 loans (12%)

### By Status
- **ACTIVE**: 1,236 loans (36%)
- **DERECOGNIZED** (Closed/Paid Off): 2,161 loans (64%)

## Column Mapping

The import script automatically mapped your Excel columns to the database schema:

### Customer Data
- `CUST_ID` → `customer_id`
- `ACCT_NM` → `customer_name`
- `PRODUCT_TYPE` → `customer_type` (mapped to RETAIL/SME)
- `RISK_CLASSFICATION` → `credit_rating`

### Loan Instrument Data
- `ACCT_NO` → `instrument_id`
- `PROD_DESC` → `instrument_type` (mapped to TERM_LOAN/OVERDRAFT/BOND/COMMITMENT)
- `START_DT` → `origination_date`
- `MATURITY_DT` → `maturity_date`
- `PRINCIPALCLOSING` → `principal_amount`
- `INTEREST_RATE` → `interest_rate`
- `CRNCY_CD` → `currency`
- `DAYS_IN_ARREAS` → `days_past_due`
- `STATUS` → `status` (mapped to ACTIVE/DERECOGNIZED)
- `IS_LOAN_RESTRUCTURED` → `is_modified`

### Stage Assignment Logic
The import script automatically assigned IFRS 9 stages based on Days Past Due (DPD):
- **Stage 1**: DPD ≤ 30 days
- **Stage 2**: 30 < DPD ≤ 90 days
- **Stage 3**: DPD > 90 days

## Next Steps

Now that your data is imported, you can:

1. **View the data via API**:
   ```bash
   # Get all customers
   curl http://localhost:8000/api/v1/customers
   
   # Get all instruments
   curl http://localhost:8000/api/v1/instruments
   ```

2. **Run Classification**:
   Use the classification endpoint to classify instruments according to IFRS 9 rules

3. **Calculate ECL**:
   Use the ECL calculation endpoints to compute Expected Credit Loss

4. **Generate Reports**:
   Query the database or use the API to generate IFRS 9 compliance reports

## Import Script Location

The import script is located at: `scripts/import_raw_data.py`

To re-import data (this will update existing records):
```bash
cd ifrs9-platform
python scripts/import_raw_data.py
```

## Database Connection

- **Host**: localhost
- **Port**: 5433
- **Database**: ifrs9
- **User**: ifrs9
- **Password**: ifrs9pass

## Sample Queries

```sql
-- View active loans by stage
SELECT current_stage, COUNT(*) as count, 
       SUM(principal_amount) as total_exposure
FROM financial_instrument 
WHERE status = 'ACTIVE'
GROUP BY current_stage;

-- View customers with highest exposure
SELECT c.customer_name, c.customer_type,
       COUNT(f.instrument_id) as loan_count,
       SUM(f.principal_amount) as total_exposure
FROM customer c
JOIN financial_instrument f ON c.customer_id = f.customer_id
WHERE f.status = 'ACTIVE'
GROUP BY c.customer_id, c.customer_name, c.customer_type
ORDER BY total_exposure DESC
LIMIT 10;

-- View loans in Stage 3 (Non-performing)
SELECT instrument_id, customer_id, principal_amount, 
       days_past_due, origination_date
FROM financial_instrument
WHERE current_stage = 'STAGE_3' AND status = 'ACTIVE'
ORDER BY principal_amount DESC
LIMIT 10;
```
