#!/bin/bash
# Run tests with coverage for Medical Triage Assistant

set -e

echo "Running tests with coverage..."

# Run pytest with coverage
pytest tests/ \
    --cov=app \
    --cov=modules \
    --cov=agents \
    --cov=database \
    --cov=config \
    --cov=global_utils \
    --cov=integrations \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=80 \
    -v

echo ""
echo "Coverage report generated in htmlcov/"
echo "Open htmlcov/index.html to view detailed coverage report"

