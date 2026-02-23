#!/bin/bash
# syntax-analyzer/scripts/entrypoint.sh

set -e

echo "🚀 Starting Syntax Analyzer..."

# Create necessary directories
mkdir -p /app/data/repos /app/data/reports /app/logs

# Wait for dependencies
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "✅ Redis is ready"

echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Run database migrations (if any)
# python manage.py migrate

# Start the application
echo "✅ All systems ready. Starting application..."
exec "$@"