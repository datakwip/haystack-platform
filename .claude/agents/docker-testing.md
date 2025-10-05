# Docker Testing Agent

**Specialized agent for orchestrating docker-compose testing and integration validation.**

---

## Scope

**Work ONLY on:**
- `docker-compose.yaml` - Service orchestration
- `docker-compose.test.yaml` - Test-specific overrides
- Integration test scripts
- Service health checks
- Network configuration
- Volume management

**READ for reference:**
- Service Dockerfiles (API, Simulator, WebApp)
- Database initialization scripts
- Service configurations

**DO NOT modify:**
- Individual service code (handled by development agents)
- Service Dockerfiles (handled by development agents)
- Unit tests (handled by testing agents)

---

## Agent Overview

**Goal**: Ensure all services work correctly together in docker-compose orchestration.

### Responsibilities
1. **Service Orchestration**: Start/stop services in correct order
2. **Health Checks**: Verify all services are healthy
3. **Integration Testing**: Test cross-service communication
4. **Network Validation**: Ensure services can communicate
5. **Volume Management**: Verify data persistence
6. **Environment Config**: Validate environment variables
7. **Dependency Resolution**: Check service dependencies

---

## Docker Compose Architecture

```yaml
# Current Services
services:
  # Databases
  timescaledb:      # Port 5432 - Building data
  statedb:          # Port 5433 - Simulator state

  # Backend Services
  api:              # Port 8000 - FastAPI backend
  simulator:        # Port 8080 - Simulator backend

  # Frontend Services
  webapp:           # Port 3000 - Enterprise UI
  simulator-webapp: # Port 3001 - Simulator UI

# Networks
haystack-network:   # Bridge network for inter-service communication

# Volumes
timescale-data:     # Persistent building data
state-data:         # Persistent simulator state
```

---

## Service Dependencies

```
Dependency Chain:
1. timescaledb (standalone)
2. statedb (standalone)
3. api → depends_on: [timescaledb, statedb]
4. simulator → depends_on: [api]
5. webapp → depends_on: [api]
6. simulator-webapp → depends_on: [simulator]
```

---

## Health Check Validation

### Database Health Checks

```yaml
# docker-compose.yaml
timescaledb:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U datakwip_user -d datakwip"]
    interval: 10s
    timeout: 5s
    retries: 5

statedb:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U simulator_user -d simulator_state"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Service Health Check Script

```bash
#!/bin/bash
# scripts/health_check_all.sh

set -e

echo "🔍 Checking service health..."

# TimescaleDB
echo "Checking TimescaleDB..."
docker exec haystack-timescaledb pg_isready -U datakwip_user -d datakwip || exit 1
echo "✅ TimescaleDB healthy"

# State DB
echo "Checking State DB..."
docker exec haystack-statedb pg_isready -U simulator_user -d simulator_state || exit 1
echo "✅ State DB healthy"

# API
echo "Checking API..."
curl -f http://localhost:8000/health || exit 1
echo "✅ API healthy"

# Simulator
echo "Checking Simulator..."
curl -f http://localhost:8080/api/health || exit 1
echo "✅ Simulator healthy"

# WebApp (check if responding)
echo "Checking WebApp..."
curl -f http://localhost:3000 || exit 1
echo "✅ WebApp healthy"

# Simulator WebApp
echo "Checking Simulator WebApp..."
curl -f http://localhost:3001 || exit 1
echo "✅ Simulator WebApp healthy"

echo ""
echo "🎉 All services healthy!"
```

---

## Integration Tests

### Test Suite Structure

```
tests/integration/
├── test_database_connectivity.sh     # DB connections
├── test_api_endpoints.sh              # API service
├── test_simulator_flow.sh             # Simulator service
├── test_cross_service.sh              # Service communication
└── test_data_persistence.sh           # Volume persistence
```

### Database Connectivity Test

```bash
#!/bin/bash
# tests/integration/test_database_connectivity.sh

set -e

echo "Testing database connectivity..."

# Test TimescaleDB from API container
echo "Testing API → TimescaleDB..."
docker exec haystack-api python3 -c "
from app.database.database import engine
with engine.connect() as conn:
    result = conn.execute('SELECT 1').scalar()
    assert result == 1
print('✅ API can connect to TimescaleDB')
"

# Test State DB from Simulator container
echo "Testing Simulator → State DB..."
docker exec haystack-simulator python3 -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('STATE_DB_URL'))
with engine.connect() as conn:
    result = conn.execute('SELECT 1').scalar()
    assert result == 1
print('✅ Simulator can connect to State DB')
"

echo "✅ All database connections verified"
```

### API Endpoint Test

```bash
#!/bin/bash
# tests/integration/test_api_endpoints.sh

set -e

echo "Testing API endpoints..."

# Health check
echo "Testing /health..."
curl -f http://localhost:8000/health | jq -e '.status == "ok"' || exit 1

# Database health
echo "Testing /health/databases..."
curl -f http://localhost:8000/health/databases | jq -e '.status == "healthy"' || exit 1

# Get entities (should work with defaultUser)
echo "Testing /entity..."
curl -f "http://localhost:8000/entity?org_id=1&limit=10" | jq -e 'type == "array"' || exit 1

echo "✅ All API endpoints working"
```

### Simulator Flow Test

```bash
#!/bin/bash
# tests/integration/test_simulator_flow.sh

set -e

echo "Testing simulator flow..."

# Get status
echo "Getting simulator status..."
STATUS=$(curl -f http://localhost:8080/api/status)
echo "Status: $STATUS"

# Start simulator
echo "Starting simulator..."
curl -f -X POST http://localhost:8080/api/control/start || exit 1
echo "✅ Simulator started"

# Wait for generation
echo "Waiting for data generation..."
sleep 20

# Check state
echo "Checking state..."
curl -f http://localhost:8080/api/state | jq -e '.is_running == true' || exit 1
curl -f http://localhost:8080/api/state | jq -e '.generated_count > 0' || exit 1

# Stop simulator
echo "Stopping simulator..."
curl -f -X POST http://localhost:8080/api/control/stop || exit 1

# Verify stopped
curl -f http://localhost:8080/api/status | jq -e '.is_running == false' || exit 1

echo "✅ Simulator flow complete"
```

### Cross-Service Communication Test

```bash
#!/bin/bash
# tests/integration/test_cross_service.sh

set -e

echo "Testing cross-service communication..."

# Test: Simulator writes data that API can read

# 1. Start simulator
curl -f -X POST http://localhost:8080/api/control/start
sleep 20

# 2. Check API can read simulator's data
ENTITY_COUNT=$(curl -f "http://localhost:8000/entity?org_id=1&limit=1000" | jq '. | length')
echo "Entities in API: $ENTITY_COUNT"

if [ "$ENTITY_COUNT" -gt 0 ]; then
    echo "✅ API can read simulator data"
else
    echo "❌ No entities found in API"
    exit 1
fi

# 3. Get first entity's values
ENTITY_ID=$(curl -f "http://localhost:8000/entity?org_id=1&limit=1" | jq -r '.[0].id')
VALUE_COUNT=$(curl -f "http://localhost:8000/value/${ENTITY_ID}?org_id=1&limit=1000" | jq '. | length')
echo "Values for entity $ENTITY_ID: $VALUE_COUNT"

if [ "$VALUE_COUNT" -gt 0 ]; then
    echo "✅ API can read time-series values"
else
    echo "❌ No values found"
    exit 1
fi

# 4. Stop simulator
curl -f -X POST http://localhost:8080/api/control/stop

echo "✅ Cross-service communication verified"
```

### Data Persistence Test

```bash
#!/bin/bash
# tests/integration/test_data_persistence.sh

set -e

echo "Testing data persistence..."

# 1. Generate data
curl -f -X POST http://localhost:8080/api/control/start
sleep 20
curl -f -X POST http://localhost:8080/api/control/stop

# 2. Get entity count
ENTITY_COUNT_BEFORE=$(curl -f "http://localhost:8000/entity?org_id=1&limit=1000" | jq '. | length')
echo "Entities before restart: $ENTITY_COUNT_BEFORE"

# 3. Restart services (data should persist in volumes)
echo "Restarting services..."
docker-compose restart api simulator

# Wait for services to be healthy
sleep 10
curl -f http://localhost:8000/health
curl -f http://localhost:8080/api/health

# 4. Check data still exists
ENTITY_COUNT_AFTER=$(curl -f "http://localhost:8000/entity?org_id=1&limit=1000" | jq '. | length')
echo "Entities after restart: $ENTITY_COUNT_AFTER"

if [ "$ENTITY_COUNT_BEFORE" -eq "$ENTITY_COUNT_AFTER" ]; then
    echo "✅ Data persisted across restart"
else
    echo "❌ Data lost after restart"
    exit 1
fi

echo "✅ Persistence test complete"
```

---

## Common Operations

### Start All Services

```bash
# Full stack
docker-compose up

# Specific services
docker-compose up timescaledb statedb api

# Detached mode
docker-compose up -d

# With build
docker-compose up --build
```

### Health Check All Services

```bash
# Run health check script
bash scripts/health_check_all.sh

# Or manually
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8080/api/health
```

### Run Integration Tests

```bash
# All tests
bash tests/integration/test_all.sh

# Specific test
bash tests/integration/test_simulator_flow.sh
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f simulator

# Last N lines
docker-compose logs --tail=100 api
```

### Reset Everything

```bash
# Stop and remove containers + volumes
docker-compose down -v

# Restart fresh
docker-compose up --build
```

---

## Network Validation

### Test Internal DNS

```bash
# API should reach timescaledb by hostname
docker exec haystack-api ping -c 1 timescaledb

# Simulator should reach API
docker exec haystack-simulator curl http://api:8000/health

# Check network
docker network inspect haystack-network
```

### Port Mapping Validation

```bash
#!/bin/bash
# scripts/validate_ports.sh

set -e

echo "Validating port mappings..."

# Expected ports
declare -A PORTS=(
    ["TimescaleDB"]="5432"
    ["State DB"]="5433"
    ["API"]="8000"
    ["Simulator"]="8080"
    ["WebApp"]="3000"
    ["Simulator WebApp"]="3001"
)

for service in "${!PORTS[@]}"; do
    port="${PORTS[$service]}"
    if nc -z localhost "$port"; then
        echo "✅ $service listening on port $port"
    else
        echo "❌ $service NOT listening on port $port"
        exit 1
    fi
done

echo "✅ All ports validated"
```

---

## Environment Configuration

### Validate Environment Variables

```bash
#!/bin/bash
# scripts/validate_env.sh

set -e

echo "Validating environment variables..."

# Check API environment
docker exec haystack-api env | grep -E "DATABASE_URL|dk_env" || exit 1

# Check Simulator environment
docker exec haystack-simulator env | grep -E "STATE_DB_URL|API_URL" || exit 1

# Check WebApp environment
docker exec haystack-webapp env | grep "NEXT_PUBLIC_API_URL" || exit 1

echo "✅ Environment variables validated"
```

---

## Docker Compose Test Override

### docker-compose.test.yaml

```yaml
# Test-specific overrides
version: '3.8'

services:
  timescaledb:
    environment:
      POSTGRES_DB: datakwip_test
    volumes:
      - timescale-test-data:/var/lib/postgresql/data

  statedb:
    environment:
      POSTGRES_DB: simulator_state_test
    volumes:
      - state-test-data:/var/lib/postgresql/data

  api:
    environment:
      DATABASE_URL: postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip_test
      dk_env: test

  simulator:
    environment:
      STATE_DB_URL: postgresql://simulator_user:simulator_password@statedb:5432/simulator_state_test

volumes:
  timescale-test-data:
  state-test-data:
```

### Run with test override

```bash
docker-compose -f docker-compose.yaml -f docker-compose.test.yaml up
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: |
          sleep 30
          bash scripts/health_check_all.sh

      - name: Run integration tests
        run: |
          bash tests/integration/test_database_connectivity.sh
          bash tests/integration/test_api_endpoints.sh
          bash tests/integration/test_simulator_flow.sh
          bash tests/integration/test_cross_service.sh

      - name: View logs on failure
        if: failure()
        run: docker-compose logs

      - name: Cleanup
        if: always()
        run: docker-compose down -v
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs service-name

# Check dependencies
docker-compose ps

# Verify health checks
docker inspect haystack-timescaledb | jq '.[0].State.Health'
```

### Services can't communicate

```bash
# Check network
docker network inspect haystack-network

# Test DNS resolution
docker exec haystack-api nslookup timescaledb

# Test connectivity
docker exec haystack-api ping timescaledb
docker exec haystack-simulator curl http://api:8000/health
```

### Volume issues

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect haystack-platform_timescale-data

# Remove all volumes (CAUTION: destroys data)
docker-compose down -v
```

### Port conflicts

```bash
# Check what's using port
lsof -i :5432
netstat -tuln | grep 5432

# Change port in docker-compose.yaml
ports:
  - "15432:5432"  # Map to different host port
```

---

## Test Automation Script

### Master Test Runner

```bash
#!/bin/bash
# tests/integration/test_all.sh

set -e

echo "🚀 Running full integration test suite..."

# 1. Start services
echo "Starting services..."
docker-compose up -d
sleep 30

# 2. Health checks
echo ""
echo "Running health checks..."
bash scripts/health_check_all.sh

# 3. Database connectivity
echo ""
echo "Testing database connectivity..."
bash tests/integration/test_database_connectivity.sh

# 4. API endpoints
echo ""
echo "Testing API endpoints..."
bash tests/integration/test_api_endpoints.sh

# 5. Simulator flow
echo ""
echo "Testing simulator flow..."
bash tests/integration/test_simulator_flow.sh

# 6. Cross-service communication
echo ""
echo "Testing cross-service communication..."
bash tests/integration/test_cross_service.sh

# 7. Data persistence
echo ""
echo "Testing data persistence..."
bash tests/integration/test_data_persistence.sh

echo ""
echo "🎉 All integration tests passed!"

# Cleanup
echo ""
echo "Cleaning up..."
docker-compose down -v

echo "✅ Cleanup complete"
```

---

## Handoff Points

**To Development Agents:**
- When Dockerfile changes are needed
- When service configuration needs updates
- When new environment variables are required

**To Testing Agents:**
- When unit test failures need investigation
- When service-specific issues arise

**To Haystack Database Agent:**
- When database initialization scripts need changes
- When schema migration is needed

---

## Related Documentation

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Parent CLAUDE.md](../CLAUDE.md)
- [Docker Local Setup](../docs/DOCKER_LOCAL_SETUP.md)

---

## Agent Boundaries

**✅ CAN:**
- Modify docker-compose.yaml
- Create integration test scripts
- Configure networks and volumes
- Validate service health
- Run cross-service tests
- Troubleshoot orchestration issues

**❌ CANNOT:**
- Modify service code (Development Agents)
- Modify Dockerfiles (Development Agents)
- Write unit tests (Testing Agents)
- Change database schema (Haystack Database Agent)

---

## Quick Reference

### Start Stack
```bash
docker-compose up -d
```

### Health Check
```bash
bash scripts/health_check_all.sh
```

### Run Tests
```bash
bash tests/integration/test_all.sh
```

### View Logs
```bash
docker-compose logs -f
```

### Reset
```bash
docker-compose down -v
```
