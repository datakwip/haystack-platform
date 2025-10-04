# Claude Code Assistant Instructions - Haystack Platform

## Project Overview

This is a **monorepo** containing the complete Haystack Building Data Platform:

### Services

1. **api/** - FastAPI backend (extended db-service-layer)
   - Building data management (entities, tags, time-series)
   - Simulator control endpoints (`/simulator/*`)
   - Multi-database support (TimescaleDB + PostgreSQL)

2. **simulator/** - Haystack data generator service
   - Generates realistic building automation data
   - Calls API endpoints for data insertion
   - Manages operational state

3. **webapp/** - Next.js web interface
   - System dashboard
   - Simulator control panel
   - Data explorer with Haystack tag filtering

## Folder Structure

```
haystack-platform/
├── api/
│   ├── src/app/
│   │   ├── api/simulator/       # NEW: Simulator endpoints
│   │   ├── api/source_objects/  # Existing: Entity, tag, value APIs
│   │   ├── services/            # Business logic
│   │   └── model/               # Pydantic & SQLAlchemy models
│   └── Dockerfile
│
├── simulator/
│   ├── src/
│   │   ├── service/            # Core simulator logic
│   │   │   ├── api_client.py   # Calls ../api endpoints
│   │   │   ├── continuous_generator.py
│   │   │   └── cognito_auth.py
│   │   ├── generators/         # Data generation
│   │   └── database/           # DB utilities
│   ├── config/                 # YAML configs
│   ├── test/                   # Tests
│   └── Dockerfile
│
├── webapp/
│   ├── app/
│   │   ├── (dashboard)/        # Authenticated pages
│   │   │   ├── page.tsx        # Main dashboard
│   │   │   ├── simulator/      # Simulator control
│   │   │   ├── activity/       # Activity timeline
│   │   │   └── explorer/       # Data explorer
│   │   └── api/                # Next.js API routes
│   ├── components/             # React components
│   └── lib/
│       └── api-client.ts       # Calls ../api endpoints
│
├── schema/                     # Database schemas
│   ├── 01_sql_schema_core_v2.sql
│   └── 02_simulator_state.sql
│
├── docs/                       # Documentation
├── knowledge/                  # Critical design decisions
└── docker-compose.yaml         # All services
```

## Important: Multi-Service Coordination

When making changes that span services:

✅ **DO THIS** (Atomic changes across services):
```
You: "Add a /simulator/metrics endpoint that returns generation stats,
     update the simulator to call it every hour, and display metrics
     on the webapp dashboard"

Claude:
1. Adds endpoint in api/src/app/api/simulator/simulator_api.py
2. Updates simulator/src/service/api_client.py with metrics() method
3. Updates simulator/src/service/continuous_generator.py to call it
4. Updates webapp/lib/api-client.ts with getMetrics()
5. Updates webapp/app/(dashboard)/page.tsx to display metrics
```

❌ **NOT THIS** (Making changes one service at a time):
```
You: "Add /simulator/metrics in the API"
Claude: [adds endpoint]
You: "Now update the simulator to call it"
Claude: [updates simulator, might miss details from API]
```

### Cross-Service Guidelines

- **API endpoint changes** → Update both `simulator/src/service/api_client.py` AND `webapp/lib/api-client.ts`
- **Database schema changes** → Update all three services that touch the DB
- **Authentication changes** → Update API middleware, simulator auth, webapp auth
- **Always test with**: `docker-compose up`

## File Placement Rules

1. **API Endpoints**: `api/src/app/api/`
   - Simulator-specific: `api/src/app/api/simulator/`
   - Existing endpoints: `api/src/app/api/source_objects/`

2. **Business Logic**: `api/src/app/services/`
   - Simulator services: `simulator_config_service.py`, `simulator_state_service.py`

3. **Data Models**:
   - Pydantic: `api/src/app/model/pydantic/simulator/`
   - SQLAlchemy: `api/src/app/model/sqlalchemy/`

4. **Simulator Core**: `simulator/src/service/`
   - Generator logic: `simulator/src/generators/`
   - Tests: `simulator/test/`

5. **WebApp Pages**: `webapp/app/(dashboard)/`
   - Components: `webapp/components/`
   - Utilities: `webapp/lib/`

6. **Shared Resources**:
   - Database schemas: `schema/`
   - Documentation: `docs/`
   - Design decisions: `knowledge/`

## Development Workflow

### Starting Services

```bash
# All services
docker-compose up

# Specific service
docker-compose up timescaledb statedb api

# Logs for one service
docker-compose logs -f simulator
```

### Making Changes

1. **Make changes across services** in single Claude session
2. **Test**: `docker-compose up`
3. **Commit all changes together** (atomic)
4. **Deploy all services** (coordinated)

### Running Tests

```bash
# Simulator tests
cd simulator
python test/test_state_manager.py
python test/test_gap_filler.py

# API tests
cd api
pytest

# Webapp tests
cd webapp
npm test
```

## Key Design Decisions

### Two-Database Architecture

- **TimescaleDB** (port 5432): Building data (entities, tags, time-series)
- **PostgreSQL** (port 5433): Simulator operational state

**Why**: Clean separation between user-facing data and simulator internals.

### API-First Architecture

- Simulator **calls API** endpoints (not direct DB writes)
- WebApp **calls API** endpoints
- Single source of truth for data operations

**Why**: Consistent data access, better error handling, multi-database support.

### Haystack v3 Schema

- Follows Project Haystack tagging conventions
- Entity-attribute-value model
- Tag-based filtering

**Why**: Industry standard for building automation systems.

## Common Tasks

### Add New Simulator Endpoint

1. Define endpoint: `api/src/app/api/simulator/simulator_api.py`
2. Add service logic: `api/src/app/services/simulator_*.py`
3. Update API client: `simulator/src/service/api_client.py`
4. Update webapp client: `webapp/lib/api-client.ts`

### Add New GUI Page

1. Create page: `webapp/app/(dashboard)/[name]/page.tsx`
2. Create components: `webapp/components/[name]/`
3. Update navigation: `webapp/components/layout/Navigation.tsx`

### Modify Database Schema

1. Update schema file: `schema/*.sql`
2. Update SQLAlchemy models: `api/src/app/model/sqlalchemy/`
3. Rebuild databases: `docker-compose down -v && docker-compose up`

## Authentication

- **Production**: AWS Cognito (SSO)
  - Users: Human login via webapp
  - Services: Service account with machine-to-machine auth

- **Local Dev**: API key fallback (for testing without Cognito)

