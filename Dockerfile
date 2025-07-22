FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend code
COPY backend/app ./app
COPY backend/frontend ./frontend

# Default environment variables (override with .env or Docker Compose)
COPY .env.example .env

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]