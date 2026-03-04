# Database Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with virtual environment

## Quick Start

### 1. Start Database Services

```bash
cd ifrs9-platform
docker-compose up -d db redis rabbitmq minio
```

### 2. Run Database Migrations

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Run migrations
alembic upgrade head
```

### 3. Verify Migration

```bash
# Check current migration version
alembic current

# Should show: 001 (head)
```

## Database Connection

Default connection string:
```
postgresql://ifrs9:ifrs9pass@localhost:5432/ifrs9
```

Set via environment variable:
```bash
export DATABASE_URL="postgresql://ifrs9:ifrs9pass@localhost:5432/ifrs9"
```

## Migration Commands

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show migration history
alembic history

# Show current version
alembic current
```

## Tables Created

The initial migration creates:

1. **customer** - Customer master data
2. **financial_instrument** - Loan portfolio and instruments
3. **ecl_calculation** - ECL calculation results
4. **stage_transition** - Stage transition history
5. **parameter_set** - PD, LGD, EAD parameters
6. **macro_scenario** - Macroeconomic scenarios
7. **collateral** - Collateral valuations
8. **audit_entry** - Audit trail

## Indexes

Performance indexes are created on:
- financial_instrument: customer_id, current_stage, status, days_past_due
- ecl_calculation: instrument_id, reporting_date, stage
- stage_transition: instrument_id, transition_date
- audit_entry: timestamp, entity_type, entity_id, user_id
- parameter_set: parameter_type, effective_date, is_active

## Troubleshooting

### Connection refused
```bash
# Check if PostgreSQL is running
docker-compose ps db

# View logs
docker-compose logs db
```

### Migration fails
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db
alembic upgrade head
```
