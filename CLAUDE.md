# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Haystack Platform** is a monorepo containing a complete building automation data platform with realistic data generation, API services, and web interfaces.

### Services Architecture

1. **api/** - FastAPI backend (extended from db-service-layer)
   - Building data management (entities, tags, time-series)
   - Simulator control endpoints (future)
   - Multi-database support (TimescaleDB + PostgreSQL)

2. **simulator/** - Standalone data generator service
   - Generates realistic Haystack v3 building automation data
   - FastAPI backend for control (port 8080)
   - Independent web UI (port 3001)
   - Persists state between runs

3. **webapp/** - Enterprise web interface (future)
   - System dashboard
   - Data explorer with Haystack tag filtering
   - Currently minimal - focus is on simulator service

### Two-Database Architecture

- **TimescaleDB** (port 5432): Building data (entities, tags, time-series)
  - Tables: `core.entity`, `core.entity_tag`, `core.values_*`
  - Hypertables for time-series data

- **PostgreSQL** (port 5433): Simulator operational state
  - Tables: `simulator_state`, `simulator_activity_log`
  - Tracks generation progress and domain events

**Why**: Clean separation between user-facing data and simulator internals.

## Common Commands

### Starting Services

```bash
# All services (from project root)
docker-compose up

# Specific services
docker-compose up timescaledb statedb simulator simulator-webapp

# View logs
docker-compose logs -f simulator

# Stop and remove volumes (full reset)
docker-compose down -v
```

### Running Tests

```bash
# Simulator tests (from simulator/ directory)
python test/test_state_manager.py
python test/test_gap_filler.py
python test/test_continuous_service.py
python test/test_resumption.py

# Validation scripts
python validation/validate_service_state.py
python validation/validate_gaps.py
python validation/validate_service_health.py

# API tests (from api/ directory)
# PREREQUISITES:
#   1. Start databases: docker-compose up -d timescaledb statedb
#   2. Run simulator to seed data: docker-compose up simulator
#   3. Wait for simulator to create test user and entities
pytest                              # Run all tests
pytest test/integration/            # Integration tests only
pytest -v --tb=short                # Verbose with short tracebacks
pytest --cov=app --cov-report=html  # With coverage report
```

### Test User Setup

The simulator automatically creates a test user for API testing:

**Test User**: `test@datakwip.local`
- Created in `core.user` table
- Granted `org_admin` permissions for simulator-created org
- Used by API tests via `dk_env=local` config

**Safety Features**:
- Test user ONLY created for whitelisted org keys: `{'docker_test', 'demo', 'test', 'simulator'}`
- Raises `ValueError` if attempting to create for non-simulator orgs
- Implementation: `simulator/src/database/schema_setup.py:initialize_test_user()`

**Configuration**:
- Default user email: `api/config.json` → `defaultUser: "test@datakwip.local"`
- Org key whitelist: `simulator/src/database/schema_setup.py:SIMULATOR_ORG_KEYS`
- Test fixtures: `api/test/conftest.py`

### Running Simulator Locally

```bash
# From simulator/ directory
cd simulator

# Install dependencies (use conda environment)
conda env create -f ../environment.yml
conda activate haystack-platform

# Start databases first
cd ..
docker-compose up timescaledb statedb

# Run simulator
cd simulator
python src/service_main.py
```

### Environment Setup

```bash
# Create conda environment (recommended)
conda env create -f environment.yml
conda activate haystack-platform

# Or use pip (from respective directories)
cd api && pip install -r requirements.txt
cd simulator && pip install -r requirements.txt
```

## Architecture Highlights

### Monorepo Structure

This is a monorepo with coordinated services. When making changes:

**✅ DO**: Make atomic changes across all affected services in one session
```
Example: Adding a /simulator/metrics endpoint requires:
1. API endpoint: api/src/app/api/simulator/simulator_api.py
2. Simulator service: simulator/src/service/continuous_generator.py
3. Simulator API: simulator/src/api/simulator_api.py
4. WebApp clients: simulator/webapp/lib/api-client.ts AND webapp/lib/api-client.ts
```

**❌ DON'T**: Make changes one service at a time across multiple sessions

### Simulator Service Design

The simulator is a **standalone service** (like IoT device manufacturer software):
- Has its own FastAPI backend (`simulator/src/api/`)
- Has its own Next.js web UI (`simulator/webapp/`)
- Manages its own state database
- Currently writes directly to TimescaleDB (API integration pending)

**Key Design Decision**: Simulator is NOT part of the enterprise API. It operates independently and will eventually call API endpoints instead of direct DB writes.

### Database Schema Conventions

**Dynamic Table Naming**: Table names are generated from organization key:
```python
# From config file: organization.key = "demo"
value_table = "values_demo"
current_table = "values_demo_current"
```

**CRITICAL**: Never hardcode table names. Always read from config:
```python
db_config = load_config_with_env('config/database_config.yaml')
table_name = db_config['tables']['value_table']
```

### Data Coherency Requirements

**Critical Principle**: The entire dataset must be coherent after every execution.

This means:
- Equipment relationships must be valid (VAVs → AHUs → Site)
- Time-series data must correspond to existing entities
- No orphaned or duplicate entities
- Totalizers must monotonically increase

**Reset Pattern**: When regenerating data, use full reset:
```bash
python src/main.py --reset  # Truncates ALL data tables
```

See `knowledge/CRITICAL_DESIGN_DECISIONS.md` for detailed rationale.

### Configuration Files

- `config/database_config.yaml` - Database connections (TimescaleDB + State DB)
- `config/database_config.docker.yaml` - Docker-specific config
- `config/building_config.yaml` - Building equipment hierarchy
- `environment.yml` - Conda environment with all dependencies

Environment variables override config files:
- `DATABASE_URL` - TimescaleDB connection (Railway format)
- `STATE_DB_URL` - State DB connection (Railway format)
- Individual vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

## File Placement Rules

### API Service (`api/`)
- Endpoints: `api/src/app/api/source_objects/` (entities, tags, values)
- Future simulator endpoints: `api/src/app/api/simulator/`
- Business logic: `api/src/app/services/`
- Models: `api/src/app/model/pydantic/` and `api/src/app/model/sqlalchemy/`

### Simulator Service (`simulator/`)
- Core logic: `simulator/src/service/`
  - `continuous_generator.py` - Main generation service
  - `state_manager.py` - State persistence
  - `gap_filler.py` - Backfill missing intervals
  - `scheduler.py` - APScheduler integration
  - `activity_logger.py` - Domain event logging
- API endpoints: `simulator/src/api/simulator_api.py`
- Data generators: `simulator/src/generators/` (entities, time_series, weather)
- Database utilities: `simulator/src/database/`
- Tests: `simulator/test/`
- Validation: `simulator/validation/`
- Web UI: `simulator/webapp/` (Next.js app)

### Shared Resources
- Database schemas: `schema/` (SQL initialization files)
- Documentation: `docs/`
- Critical decisions: `knowledge/` (MUST READ before major changes)

## Development Workflow

### Making Changes to Simulator

1. **Modify code** in `simulator/src/`
2. **Update tests** if behavior changed
3. **Test locally**:
   ```bash
   docker-compose up timescaledb statedb  # Databases
   python src/service_main.py              # Simulator
   ```
4. **Run validation**:
   ```bash
   python validation/validate_service_state.py
   python validation/validate_gaps.py
   ```
5. **Test in Docker**:
   ```bash
   docker-compose up simulator simulator-webapp
   ```

### Database Schema Changes

1. Update schema file: `schema/01_sql_schema_core_v2.sql` or `schema/02_simulator_state.sql`
2. Update SQLAlchemy models if in API: `api/src/app/model/sqlalchemy/`
3. Rebuild containers:
   ```bash
   docker-compose down -v  # Remove volumes
   docker-compose up       # Recreate with new schema
   ```

### Common Development Pitfalls

1. **Timezone handling**: PostgreSQL returns timezone-aware timestamps, Python's `datetime.now()` is naive
   ```python
   # Always strip timezone for comparison
   ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
   ```

2. **Decimal vs Float**: PostgreSQL interval queries return Decimal
   ```python
   interval = float(row['interval_minutes'])  # Explicit cast
   ```

3. **Table name configuration**: Never hardcode `values_demo`
   ```python
   table_name = db_config['tables']['value_table']  # From config
   ```

4. **Reset completeness**: Ensure all related tables are truncated
   ```python
   # Must include value tables, not just entities
   db.reset_all_data(
       value_table=config['tables']['value_table'],
       current_table=config['tables']['current_table']
   )
   ```

## Current Status (2025-10-05)

**Phase 1: Standalone Simulator** ✅ COMPLETE & RUNNING
- Simulator backend API operational (port 8080)
- Simulator web UI functional (port 3001)
- Activity logging and state persistence working
- Continuous generation with gap filling tested
- **Test user creation** ✅ IMPLEMENTED
  - Simulator automatically creates `test@datakwip.local` user
  - User granted org admin permissions for API testing
  - Safety whitelist prevents test user creation in production orgs

**Phase 2: Authentication** ⏳ IN PROGRESS
- Test user authentication working for local development (`dk_env=local`)
- API tests now pass authorization (21/28 tests passing)
- AWS Cognito integration not yet implemented
- Service account for simulator pending
- WebApp authentication pending

**Phase 3: API Integration** ⏳ PENDING
- Simulator currently writes directly to TimescaleDB
- Future: Simulator will call API endpoints instead
- Requires API client implementation in `simulator/src/service/api_client.py`

See `IMPLEMENTATION_STATUS.md` for detailed roadmap.

### API Test Status (2025-10-05)

**Test Results**: 21 passing, 7 failing (75% pass rate, up from 10%)
- **Test coverage**: 43% (up from 38%)

**✅ Working** (authorization fixed):
- Entity CRUD operations (create, read, update, delete)
- Entity tags (list, filter, create)
- Tag metadata (list, create)
- System health checks
- Pagination for all endpoints

**❌ Remaining Failures** (next priority):
1. `test_get_entity_not_found` - Returns 403 instead of 404
   - **Issue**: ACL check happens before entity existence check
   - **Location**: `api/src/app/api/source_objects/entity.py:57`

2. `test_list_tag_defs` - No tag definitions found
   - **Issue**: Simulator not creating tag definitions in database
   - **Expected**: Tag defs for `site`, `equip`, `ahu`, `vav`, `point`, `temp`, etc.

3. **Value endpoint failures** (5 tests):
   - `test_get_values_for_entity` - 403 Forbidden
   - `test_get_values_pagination` - 403 Forbidden
   - `test_create_value` - 503 Service Unavailable
   - `test_bulk_create_values` - 503 Service Unavailable
   - `test_get_values_for_invalid_entity` - 403 instead of 404
   - **Issues**:
     - ACL permissions for value access not configured correctly
     - Value service may have database connection issues (503 errors)
     - Similar ACL-before-existence issue as entity endpoint

**Next Steps**:
1. Fix tag definition creation in simulator (should happen during entity generation)
2. Fix ACL order-of-operations (check existence before permission)
3. Investigate value service 503 errors (likely dynamic table creation issue)
4. Add test coverage for value ACL permissions

## Key Documentation

- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Current status, roadmap, next steps
- **[knowledge/CRITICAL_DESIGN_DECISIONS.md](knowledge/CRITICAL_DESIGN_DECISIONS.md)** - Data coherency, timezone handling, table naming
- **[knowledge/DB_SERVICE_LAYER_ANALYSIS.md](knowledge/DB_SERVICE_LAYER_ANALYSIS.md)** - API architecture analysis
- **[README.md](README.md)** - Quick start and service overview

## Important Principles

1. **Data Coherency First**: Every operation must maintain valid building automation relationships
2. **Configuration-Driven**: Never hardcode table names, ports, or database credentials
3. **Test Before Commit**: Run validation scripts after any data generation changes
4. **Monorepo Coordination**: Update all affected services atomically
5. **Read Critical Decisions**: Check `knowledge/` before major architectural changes
