# IFRS 9 Platform - React Dashboard

Professional web dashboard for the IFRS 9 Platform.

## Features

- **Dashboard**: Portfolio overview with charts and statistics
- **Portfolio View**: Searchable and filterable table of all instruments
- **ECL Calculator**: Calculate Expected Credit Loss for individual instruments
- Real-time data from the API
- Responsive design
- Material-UI components

## Getting Started

### Prerequisites

- Node.js 16+ installed
- IFRS 9 API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install
```

### Running the Dashboard

```bash
# Start the development server
npm start
```

The dashboard will open automatically at http://localhost:3000

### Building for Production

```bash
# Create production build
npm run build
```

The build files will be in the `build/` directory.

## Dashboard Sections

### 1. Dashboard Tab
- Total instruments count
- Total exposure
- Total ECL
- Coverage ratio
- Stage distribution (pie chart and bar chart)
- Detailed stage breakdown table

### 2. Portfolio Tab
- Searchable table of all instruments
- Filter by stage (Stage 1, 2, 3)
- Filter by status (Active, Derecognized, Written Off)
- Pagination
- Sortable columns

### 3. ECL Calculator Tab
- Calculate ECL for any instrument
- View ECL components (PD, LGD, EAD)
- See calculation formula
- View stage and reporting date

## API Integration

The dashboard connects to the IFRS 9 API at `http://localhost:8000/api/v1`

Endpoints used:
- `GET /instruments` - Fetch all instruments
- `POST /ecl/calculate` - Calculate ECL for an instrument

## Technology Stack

- React 18 with TypeScript
- Material-UI (MUI) for components
- Recharts for data visualization
- Axios for API calls

## Customization

### Colors

Stage colors are defined in `Dashboard.tsx`:
- Stage 1: Green (#4caf50)
- Stage 2: Orange (#ff9800)
- Stage 3: Red (#f44336)

### Theme

The Material-UI theme is configured in `App.tsx` and can be customized.

## Troubleshooting

### API Connection Issues

If you see "Failed to load portfolio statistics":
1. Make sure the API is running: `./start_api.sh`
2. Check the API is accessible at http://localhost:8000/api/docs
3. Check browser console for CORS errors

### Port Already in Use

If port 3000 is already in use:
```bash
# Kill the process on port 3000
lsof -ti:3000 | xargs kill -9

# Or set a different port
PORT=3001 npm start
```

## Future Enhancements

- Real-time updates with WebSockets
- Export data to Excel/CSV
- Advanced filtering and search
- Drill-down views for individual instruments
- ECL calculation history
- Batch ECL calculations
- User authentication
- Role-based access control
