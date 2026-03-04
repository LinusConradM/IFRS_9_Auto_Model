# IFRS 9 Automation Platform

A comprehensive IFRS 9 compliance platform for commercial banks in Uganda, featuring automated classification, staging, ECL calculation, and a professional React dashboard.

![Platform Status](https://img.shields.io/badge/status-MVP%20Complete-success)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18.0+-61dafb)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Overview

This platform automates IFRS 9 financial instrument classification, impairment staging, and Expected Credit Loss (ECL) calculations for commercial banks. Built with modern technologies and designed for scalability, it handles real-world portfolios with thousands of instruments.

### Key Features

- ✅ **Automated Classification** - Business model assessment and SPPI testing
- ✅ **Intelligent Staging** - SICR detection with quantitative and qualitative indicators
- ✅ **ECL Calculation** - 12-month and lifetime ECL with scenario weighting
- ✅ **Professional Dashboard** - Real-time portfolio visualization and analytics
- ✅ **Audit Trail** - Comprehensive logging with immutability guarantees
- ✅ **Data Import** - Excel/CSV import with validation
- ✅ **RESTful API** - Complete API with Swagger documentation

## 📊 Dashboard Preview

The platform includes a professional React dashboard with:

- **Portfolio Overview** - Total exposure, ECL, and coverage ratio metrics
- **Stage Distribution** - Visual breakdown by IFRS 9 stages
- **Macroeconomic Forecast** - Scenario analysis with GDP trends
- **Portfolio Treemap** - Interactive composition visualization
- **ECL Calculator** - Individual instrument ECL calculation
- **Searchable Portfolio** - Filter by stage, status, and customer

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/LinusConradM/IFRS_9_Auto_Model.git
cd IFRS_9_Auto_Model/ifrs9-platform
```

2. **Start Docker services**
```bash
docker-compose up -d postgres redis rabbitmq minio
```

3. **Install Python dependencies**
```bash
pip install -e .
```

4. **Run database migrations**
```bash
alembic upgrade head
```

5. **Start the API**
```bash
./start_api.sh
```

6. **Start the Dashboard** (in a new terminal)
```bash
./start_dashboard.sh
```

7. **Access the platform**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/api/docs
- API: http://localhost:8000

## 📁 Project Structure

```
ifrs9-platform/
├── src/
│   ├── api/              # FastAPI routes and dependencies
│   ├── services/         # Business logic (classification, staging, ECL)
│   ├── db/               # Database models and schemas
│   └── utils/            # Utilities (cache, queue, storage, logging)
├── frontend/             # React dashboard
│   └── src/
│       ├── components/   # Dashboard, Portfolio, ECL Calculator
│       └── services/     # API client
├── alembic/              # Database migrations
├── scripts/              # Data import and test scripts
├── docs/                 # Documentation
└── tests/                # Test suites
```

## 💾 Data Import

Import your loan portfolio from Excel:

```bash
python scripts/import_raw_data.py
```

The platform has successfully imported and processed:
- **3,397 instruments** from real bank data
- **977 customers** (744 RETAIL, 233 SME)
- **Stage distribution**: 2,842 Stage 1, 136 Stage 2, 419 Stage 3

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database (port 5433)
- **SQLAlchemy** - ORM and database toolkit
- **Alembic** - Database migrations
- **Redis** - Caching layer
- **RabbitMQ** - Message queue
- **MinIO** - Object storage

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Material-UI** - Component library
- **Recharts** - Data visualization
- **Axios** - HTTP client

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Quick Start Guide](ifrs9-platform/docs/QUICKSTART.md) - Get up and running
- [API Guide](ifrs9-platform/docs/API_GUIDE.md) - API endpoints and examples
- [Dashboard Guide](ifrs9-platform/docs/DASHBOARD_GUIDE.md) - Using the dashboard
- [Database Setup](ifrs9-platform/docs/DATABASE_SETUP.md) - Database configuration
- [MVP Status](ifrs9-platform/docs/MVP_STATUS.md) - Feature completion status

## 🎓 IFRS 9 Implementation

The platform implements key IFRS 9 requirements:

### Classification (IAS 39 → IFRS 9)
- Business model assessment (Hold to Collect, Hold to Collect and Sell, Other)
- SPPI (Solely Payments of Principal and Interest) test
- Classification into Amortized Cost, FVOCI, or FVTPL

### Impairment Staging
- **Stage 1**: Performing (12-month ECL)
- **Stage 2**: Underperforming (Lifetime ECL)
- **Stage 3**: Non-performing (Lifetime ECL)
- SICR (Significant Increase in Credit Risk) detection
- Configurable DPD thresholds (30/90 days)

### ECL Calculation
- Formula: ECL = PD × LGD × EAD
- 12-month ECL for Stage 1
- Lifetime ECL for Stage 2/3
- Scenario weighting (Base, Upside, Downside)
- Macroeconomic adjustments

## 🔐 Security & Compliance

- Comprehensive audit trail with SHA-256 integrity hashing
- Immutable audit entries
- User action tracking
- IP address logging
- Session management

## 📊 API Endpoints

The platform provides RESTful APIs for:

- `/api/v1/imports/*` - Data import (CSV/Excel)
- `/api/v1/classification/*` - Instrument classification
- `/api/v1/staging/*` - Stage determination
- `/api/v1/ecl/*` - ECL calculation
- `/api/v1/instruments/*` - Portfolio queries
- `/api/v1/audit/*` - Audit trail

Interactive API documentation: http://localhost:8000/api/docs

## 🧪 Testing

Run the quick test to verify the platform:

```bash
python scripts/quick_test_run.py
```

This will:
- Set up sample parameters (PD, LGD, EAD)
- Create macro scenarios
- Run classification, staging, and ECL calculations
- Display results

## 🚧 Roadmap

### Completed ✅
- Core IFRS 9 modules (Classification, Staging, ECL)
- React dashboard with visualizations
- Data import from Excel
- RESTful API with documentation
- Audit trail
- Real data processing (3,397 instruments)

### Planned 🔜
- Property-based testing (40 correctness properties)
- JWT authentication
- Role-based access control
- Batch ECL calculations
- Historical trend analysis
- PDF/Excel report generation
- Data export functionality
- POCI (Purchased or Originated Credit Impaired) handling
- Modifications and derecognition
- Write-offs and recoveries

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Linus Conrad Muhirwe** - Initial work

## 🙏 Acknowledgments

- Built for commercial banks in Uganda
- Implements IFRS 9 Financial Instruments standard
- Inspired by industry best practices in credit risk management

## 📞 Support

For questions or issues:
- Check the [documentation](ifrs9-platform/docs/)
- Review the [API guide](ifrs9-platform/docs/API_GUIDE.md)
- Open an issue on GitHub

---

**Platform Status**: ✅ MVP Complete - Ready for Production Testing

Built with ❤️ for the banking industry in Uganda
