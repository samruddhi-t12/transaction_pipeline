# Use a lightweight official Python image
FROM python:3.12-slim

# Stop Python from generating .pyc files and force logs to show immediately
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (needed for psycopg2 to talk to PostgreSQL)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# We don't put a CMD here because docker-compose will specify whether 
# this container should run the FastAPI server or the Celery worker.