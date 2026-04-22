#!/bin/bash
# Development setup script for Medical Triage Assistant

set -e

echo "Setting up development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your configuration"
fi

# Start PostgreSQL if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "Starting PostgreSQL with pgvector..."
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Setup frontend
echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "Development environment setup complete!"
echo ""
echo "To start the backend:"
echo "  source venv/bin/activate"
echo "  python -m app.main"
echo ""
echo "To start the frontend:"
echo "  cd frontend && npm run dev"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up --build"

