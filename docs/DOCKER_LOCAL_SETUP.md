# Docker Local Setup Guide

**← [Back to Main README](../README.md)**

This guide explains how to run the Haystack Data Simulator with TimescaleDB using Docker for local development and testing.

**Related Documentation**:
- [Service Mode Guide](SERVICE_MODE_SUMMARY.md) - Continuous operation
- [Railway Deployment](RAILWAY_DEPLOYMENT.md) - Cloud deployment
- [Docker Scripts](../scripts/README.md) - Automation helpers

## Prerequisites

- Docker installed and running
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

### 1. Start TimescaleDB Only

If you want to run just the database and use the simulator from your local Python environment:

```bash
# Start only the database
docker-compose up -d timescaledb

# Check database is healthy
docker-compose ps

# View logs
docker-compose logs -f timescaledb
```

### 2. Initialize Database Schema

The schema files in `schema/` will automatically run on first startup. To manually initialize:

```bash
# Apply core schema
docker exec -i haystack-timescaledb psql -U datakwip_user -d datakwip < schema/sql_schema_core_v2.sql

# Apply simulator state table
docker exec -i haystack-timescaledb psql -U datakwip_user -d datakwip < schema/simulator_state.sql
```

### 3. Configure Local Connection

**Important**: Table names are determined by the `organization.key` setting in your config file.

For Docker testing, use the Docker-specific config:

```bash
# Copy Docker config (uses 'values_docker_test' tables)
cp config/database_config.docker.yaml config/database_config.yaml
```

This config uses:
- Organization key: `docker_test`
- Value table: `values_docker_test`
- Current table: `values_docker_test_current`

Or set environment variable:

```bash
export DATABASE_URL=postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip
```

**Note**: The default config (`database_config.yaml.backup`) uses organization key `demo` and creates `values_demo` tables.

### 4. Run Simulator from Host

With the database running in Docker, run the simulator locally:

```bash
# Generate entities and data
python src/main.py --reset --days 7

# Or run in continuous service mode
python src/main.py --service
```

## Full Stack with Docker Compose

To run both the database and simulator in Docker:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check health
curl http://localhost:8080/health
```

## Testing with Docker

### Run Tests Against Dockerized Database

```bash
# Ensure database is running
docker-compose up -d timescaledb

# Wait for database to be ready
sleep 5

# Run tests with Docker config
python test/test_state_manager.py
python test/test_continuous_service.py
python test/test_resumption.py

# Run validations
python validation/validate_service_state.py
python validation/validate_gaps.py
```

### Database Operations

```bash
# Connect to database
docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip

# Check tables
docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip -c "\dt core.*"

# Check data (Docker config uses values_docker_test)
docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip -c "SELECT COUNT(*) FROM core.values_docker_test;"

# View recent data
docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip -c "SELECT * FROM core.values_docker_test ORDER BY ts DESC LIMIT 10;"

# Note: Table name depends on your config's organization.key setting
```

## Common Workflows

### Fresh Start

```bash
# Stop and remove everything
docker-compose down -v

# Start database
docker-compose up -d timescaledb

# Wait for healthy
sleep 10

# Initialize with data
python src/main.py --reset --days 30
```

### Service Mode Testing

```bash
# Ensure database is running
docker-compose up -d timescaledb

# Start simulator in service mode (local)
python src/main.py --service

# In another terminal, monitor
watch -n 1 'curl -s http://localhost:8080/health | jq'

# Check state
python src/main.py --check-state
```

### Gap Filling Test

```bash
# Generate initial data
python src/main.py --reset --days 2

# Simulate downtime (stop simulator if running)
# Wait 1 hour...

# Fill gaps
python src/main.py --catchup

# Validate
python validation/validate_gaps.py
```

## Troubleshooting

### Database Won't Start

```bash
# Check logs
docker-compose logs timescaledb

# Remove old data and restart
docker-compose down -v
docker-compose up -d timescaledb
```

### Connection Refused

```bash
# Check database is running
docker-compose ps

# Verify port is exposed
docker ps | grep 5432

# Test connection
docker exec haystack-timescaledb pg_isready -U datakwip_user
```

### Schema Not Applied

```bash
# Manually apply schemas
docker exec -i haystack-timescaledb psql -U datakwip_user -d datakwip < schema/sql_schema_core_v2.sql
docker exec -i haystack-timescaledb psql -U datakwip_user -d datakwip < schema/simulator_state.sql
```

### Reset Everything

```bash
# Nuclear option - removes all data
docker-compose down -v
docker volume rm haystack-data-simulator_timescaledb_data 2>/dev/null || true
docker-compose up -d timescaledb
sleep 10

# Re-initialize
python src/main.py --reset --entities-only
```

## Environment Variables

### For Local Development (simulator on host, DB in Docker)

```bash
export DATABASE_URL=postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip
```

### For Full Docker Stack (simulator in Docker)

Handled automatically by docker-compose.yaml:
- Database host is `timescaledb` (service name)
- Port is 5432 (internal)
- Health endpoint on port 8080

## Data Persistence

Database data persists in Docker volume `timescaledb_data`. To remove:

```bash
# Stop services
docker-compose down

# Remove volume
docker volume rm haystack-data-simulator_timescaledb_data
```

## Performance Tips

### For Development

```bash
# Run database only, simulator on host (faster iteration)
docker-compose up -d timescaledb
python src/main.py --service
```

### For Testing

```bash
# Use smaller datasets
python src/main.py --reset --days 1

# Or generate only entities
python src/main.py --reset --entities-only
```

## Useful Commands

```bash
# View all container logs
docker-compose logs -f

# Restart service
docker-compose restart simulator

# Check database size
docker exec haystack-timescaledb psql -U datakwip_user -d datakwip -c "SELECT pg_size_pretty(pg_database_size('datakwip'));"

# Check table sizes
docker exec haystack-timescaledb psql -U datakwip_user -d datakwip -c "
  SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
  FROM pg_tables
  WHERE schemaname = 'core'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Backup database
docker exec haystack-timescaledb pg_dump -U datakwip_user datakwip > backup.sql

# Restore database
docker exec -i haystack-timescaledb psql -U datakwip_user datakwip < backup.sql
```

## Next Steps

- For Railway deployment, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- For service architecture, see [SERVICE_MODE_SUMMARY.md](SERVICE_MODE_SUMMARY.md)
