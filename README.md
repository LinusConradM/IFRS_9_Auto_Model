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

### Environment Variables

Copy the example environment file and update the variables:

```bash
cp .env.example .env
# Edit .env and configure your database credentials
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