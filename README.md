# IFRS 9 Automation Platform

This repository contains the IFRS 9 Automation Platform, including backend, frontend, and infrastructure code.

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Terraform

## Project Structure

```
IFRS_9-automation/
├── backend/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   └── tests/
├── frontend/
│   ├── src/
│   ├── components/
│   └── tests/
└── infrastructure/
    └── terraform/
```

## Setup Instructions

### Clone the repository

```bash
git clone <repo-url>
cd IFRS_9-automation
```

### Backend Setup

```bash
cd backend
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Database Migrations

Generate and apply database migrations (skip initialization if already set up):
```bash
cd backend
# initialize alembic on first run
alembic init alembic
alembic revision --autogenerate -m "Initial database schema"
alembic upgrade head
```

#### Seeding Dummy Data

Load IFRS 9 dummy loan book data into the database:
```bash
python seed_ifrs9.py --csv full_ifrs9_dummy_loan_book.csv
```

### Environment Variables

# Copy the example environment file from the project root and update variables:

```bash
cp ../.env.example .env
# Edit .env and configure your database credentials
# Optionally configure AI agent and credentials:
# AI_AGENT=codex  # or "claude"
# CLAUDE_API_KEY=your_claude_api_key
# OPENAI_API_KEY=your_openai_api_key
```

### Running Backend Tests

From the `backend` directory, run:

```bash
pytest
```

### Docker Compose (Local Development)

Start the application services:

```bash
docker-compose up -d
```

This will start:
- `db` (PostgreSQL database)
- `backend` (FastAPI application)
- `frontend` (React development server)

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

### Infrastructure

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## License

[Specify license here]