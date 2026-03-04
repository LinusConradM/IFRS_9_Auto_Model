#!/bin/bash
# Start the IFRS 9 Platform API

export DATABASE_URL="postgresql://ifrs9:ifrs9pass@localhost:5433/ifrs9"
export REDIS_URL="redis://localhost:6379"
export RABBITMQ_URL="amqp://guest:guest@localhost:5672"

echo "Starting IFRS 9 Platform API..."
echo "Database: $DATABASE_URL"
echo "API Documentation: http://localhost:8000/api/docs"
echo ""

uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
