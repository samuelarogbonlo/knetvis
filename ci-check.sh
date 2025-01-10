#!/bin/bash
set -e  # Exit on any error

echo "🔍 Running format checks..."
black --check src tests
isort --check-only src tests

echo "🔍 Running linting..."
flake8 src tests

echo "🔍 Running type checks..."
mypy src

echo "🔍 Running tests..."
pytest --cov=src tests/

echo "✅ All checks passed!"