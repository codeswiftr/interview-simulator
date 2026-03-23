#!/bin/bash
# Script to run backend test coverage with database
# Prerequisites: Docker and docker-compose must be installed

set -e

echo "🔧 Setting up test environment..."

# Check if docker-compose services are running
if ! docker-compose ps | grep -q "interview-simulator-postgres.*Up"; then
    echo "📦 Starting PostgreSQL container..."
    docker-compose up -d postgres
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Check if database is accessible
if ! docker-compose exec -T postgres pg_isready -U postgres -d interview_simulator > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not ready. Please check docker-compose status."
    exit 1
fi

echo "✅ Database is ready"
echo "🧪 Running test coverage..."

# Run pytest with coverage
cd "$(dirname "$0")/.."
uv run pytest --cov=app --cov-report=term-missing --cov-report=json --cov-report=html

echo ""
echo "📊 Coverage reports generated:"
echo "  - Terminal output (above)"
echo "  - JSON: backend/coverage.json"
echo "  - HTML: backend/htmlcov/index.html"