#!/bin/bash
# Setup test environment by running simulator to seed database

echo "Setting up test environment..."

# Start databases
echo "1. Starting databases..."
docker-compose up -d timescaledb statedb

# Wait for databases to be healthy
echo "2. Waiting for databases to be ready..."
sleep 10

# Run simulator to seed data
echo "3. Running simulator to seed test data..."
docker-compose up simulator

echo "✓ Test environment ready!"
echo "Run tests with: cd api && pytest"
