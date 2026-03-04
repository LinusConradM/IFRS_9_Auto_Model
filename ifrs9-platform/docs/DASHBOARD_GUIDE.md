# IFRS 9 Dashboard Guide

## Quick Start

### 1. Start the API (if not already running)

```bash
cd ifrs9-platform
./start_api.sh
```

The API will be available at: http://localhost:8000

**If you see "Address already in use" error:**
```bash
# Kill the existing process on port 8000
lsof -ti:8000 | xargs kill -9

# Then restart
./start_api.sh
```

**After updating API code, restart the server:**
- Press `Ctrl+C` in the terminal running the API
- Run `./start_api.sh` again

### 2. Start the Dashboard

```bash
# From the ifrs9-platform directory
./start_dashboard.sh
```

The dashboard will automatically open at: http://localhost:3000

## Dashboard Overview

### Dashboard Tab

The main dashboard provides a high-level overview of your loan portfolio:

**Summary Cards:**
- **Total Instruments**: Number of loans in your portfolio (3,397)
- **Total Exposure**: Sum of all principal amounts
- **Total ECL**: Total Expected Credit Loss across portfolio
- **Coverage Ratio**: ECL as a percentage of total exposure

**Visualizations:**
- **Stage Distribution (Pie Chart)**: Shows the count of instruments in each stage
- **Stage Distribution (Bar Chart)**: Shows the exposure amount by stage
- **Stage Details Table**: Detailed breakdown with percentages and averages

**What the Stages Mean:**
- **Stage 1** (Green): Performing loans - 12-month ECL
- **Stage 2** (Orange): Underperforming loans - Lifetime ECL
- **Stage 3** (Red): Non-performing loans - Lifetime ECL

### Portfolio Tab

View and filter all instruments in your portfolio:

**Features:**
- **Search**: Find instruments by ID or customer ID
- **Stage Filter**: Show only Stage 1, 2, or 3 loans
- **Status Filter**: Filter by Active, Derecognized, or Written Off
- **Pagination**: Navigate through large datasets
- **Sortable Columns**: Click column headers to sort

**Columns Displayed:**
- Instrument ID
- Customer ID
- Instrument Type (TERM_LOAN, OVERDRAFT, etc.)
- Principal Amount
- Interest Rate
- Days Past Due (DPD)
- Current Stage
- Status
- Origination Date
- Maturity Date

### ECL Calculator Tab

Calculate Expected Credit Loss for individual instruments:

**How to Use:**
1. Enter an Instrument ID (e.g., `1003020638002`)
2. Click "Calculate ECL" or press Enter
3. View the results:
   - ECL Amount in UGX
   - Stage classification
   - PD (Probability of Default)
   - LGD (Loss Given Default)
   - EAD (Exposure at Default)
   - Calculation formula breakdown

**Understanding the Results:**
- **ECL Amount**: The expected loss amount for this instrument
- **PD**: Likelihood the borrower will default
- **LGD**: Expected loss if default occurs (after collateral recovery)
- **EAD**: Amount exposed at the time of default
- **Formula**: ECL = PD × LGD × EAD

## Common Tasks

### View Stage 3 (Non-Performing) Loans

1. Go to the **Portfolio** tab
2. Set **Stage Filter** to "Stage 3"
3. Review the list of non-performing loans
4. Note the Days Past Due (DPD) - typically > 90 days

### Calculate ECL for High-Risk Loans

1. From the Portfolio tab, identify instruments in Stage 3
2. Copy an Instrument ID
3. Go to the **ECL Calculator** tab
4. Paste the Instrument ID and calculate
5. Review the ECL amount and components

### Monitor Portfolio Health

1. Go to the **Dashboard** tab
2. Check the **Coverage Ratio** - higher means more provisions
3. Review **Stage Distribution**:
   - High Stage 1 percentage = healthy portfolio
   - High Stage 3 percentage = portfolio stress
4. Compare exposure across stages

### Export Data (Coming Soon)

Currently, you can:
- Copy data from tables
- Take screenshots
- Use browser print function

Future versions will include:
- Excel export
- CSV download
- PDF reports

## Troubleshooting

### Dashboard Won't Load

**Problem**: White screen or loading forever

**Solutions:**
1. Check if API is running: http://localhost:8000/api/docs
2. Check browser console for errors (F12)
3. Restart the dashboard: `Ctrl+C` then `./start_dashboard.sh`

### "Failed to load portfolio statistics"

**Problem**: Error message on dashboard

**Solutions:**
1. Verify API is running on port 8000
2. Check if data was imported: `python scripts/quick_test_run.py`
3. Check API logs for errors

### No Data Showing

**Problem**: Dashboard loads but shows 0 instruments

**Solutions:**
1. Verify data import: Run `python scripts/import_raw_data.py`
2. Check database: 
   ```bash
   PGPASSWORD=ifrs9pass psql -h localhost -p 5433 -U ifrs9 -d ifrs9 -c "SELECT COUNT(*) FROM financial_instrument;"
   ```
3. Restart both API and dashboard

### Port Already in Use

**Problem**: "Address already in use" error

**Solutions:**
```bash
# For API (port 8000)
lsof -ti:8000 | xargs kill -9

# For Dashboard (port 3000)
lsof -ti:3000 | xargs kill -9
```

## Performance Tips

### Large Portfolios

If you have many instruments (>10,000):
- Use filters to narrow down results
- Increase pagination size for faster browsing
- Consider adding database indexes (already done)

### Slow ECL Calculations

If ECL calculations are slow:
- Check if parameters are cached
- Verify database connection
- Consider batch calculations for multiple instruments

## Next Steps

### Customize the Dashboard

1. **Change Colors**: Edit `src/components/Dashboard.tsx`
2. **Add Charts**: Use Recharts library
3. **Modify Layout**: Update Material-UI Grid components

### Add Features

Potential enhancements:
- Historical ECL trends
- Scenario analysis
- Customer drill-down
- Batch ECL calculations
- Report generation
- Data export

### Deploy to Production

For production deployment:
1. Build the dashboard: `cd frontend && npm run build`
2. Serve with nginx or similar
3. Update API URL in `src/services/api.ts`
4. Add authentication
5. Enable HTTPS

## Support

For issues or questions:
1. Check the logs in browser console (F12)
2. Check API logs
3. Review the API documentation: http://localhost:8000/api/docs
4. Check database connectivity

## Keyboard Shortcuts

- **Enter** in ECL Calculator: Calculate ECL
- **F12**: Open browser developer tools
- **Ctrl+R**: Refresh page
- **Ctrl+Shift+R**: Hard refresh (clear cache)
