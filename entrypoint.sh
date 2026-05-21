#!/bin/bash

# Wait for database to be ready
echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL started"

# Initialize database tables and roles
echo "Initializing database..."
python init_db.py

# Run migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
exec "$@"
