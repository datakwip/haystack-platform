# API Development Agent

**Specialized agent for building and modifying the FastAPI backend service.**

---

## Scope

**Work ONLY on:**
- `/api/src/app/` - Application code
- `/api/config.json` - Configuration
- `/api/requirements.txt` - Dependencies
- `/api/Dockerfile` - Container build

**DO NOT touch:**
- `/api/test/` - Tests (handled by API Testing Agent)
- Other services (`/simulator`, `/webapp`)
- Database schema files (read-only reference)
- `docker-compose.yaml` (handled by Docker Testing Agent)

---

## Service Overview

**FastAPI Building Data API** - Port 8000

### Core Responsibilities
1. **Source Objects API**: Entities, tags, tag definitions, time-series values
2. **Access Control (ACL)**: Organizations, users, permissions
3. **DQQL Filtering**: Query language for data filtering
4. **Health Monitoring**: Database connection health checks
5. **Future**: Simulator control endpoints (in `/api/src/app/api/simulator/`)

### Tech Stack
- **Framework**: FastAPI (Python)
- **Database**: TimescaleDB (port 5432) + State PostgreSQL (port 5433)
- **Authentication**: AWS Cognito JWT (production) or defaultUser (local dev)
- **Schema**: `core` schema in TimescaleDB

---

## File Structure

```
api/
├── src/app/
│   ├── api/                          # Route handlers
│   │   ├── source_objects/           # Core data endpoints
│   │   │   ├── entity.py             # Entities (equipment, spaces)
│   │   │   ├── tag_def.py            # Tag definitions
│   │   │   ├── tag_meta.py           # Tag metadata
│   │   │   ├── entity_tag.py         # Entity-tag associations
│   │   │   └── value.py              # Time-series values
│   │   ├── acl/                      # Access control
│   │   │   ├── org/                  # Organizations
│   │   │   └── user/                 # Users
│   │   ├── filter/                   # DQQL filtering
│   │   ├── views/                    # Database views
│   │   ├── exporter/                 # Data export
│   │   ├── system.py                 # Health checks
│   │   └── simulator/                # Future: Simulator control
│   ├── services/                     # Business logic layer
│   │   ├── acl/                      # ACL services
│   │   ├── config_service.py         # Config loading
│   │   └── request_service.py        # Request handling
│   ├── dto/                          # Data access objects
│   ├── model/
│   │   ├── pydantic/                 # Request/response schemas
│   │   └── sqlalchemy/               # ORM models
│   ├── database/                     # DB utilities
│   └── main.py                       # App entry point
├── config.json                       # Configuration
├── requirements.txt                  # Dependencies
└── Dockerfile                        # Container build
```

---

## Database Knowledge

### TimescaleDB (Port 5432)
- **Database**: `datakwip`
- **Schema**: `core`
- **Connection**: `config.json` → `dbUrl`

**Key Tables:**
- `core.entity` - Building equipment, spaces, points
- `core.entity_tag` - Haystack tag assignments (value_n, value_s, value_b, etc.)
- `core.tag_def` - Tag definitions (name, type, unit, description)
- `core.values_{org_key}` - Time-series data (hypertables, org-specific)
- `core.org` - Organizations (has `value_table` column)
- `core.user` - Users for authentication

**Critical Concept - Dynamic Table Naming:**
```python
# ❌ NEVER hardcode
"SELECT * FROM values_demo WHERE entity_id = ?"

# ✅ ALWAYS get from org table
org = db.query("SELECT value_table FROM core.org WHERE id = ?", org_id)
table_name = org['value_table']  # e.g., "values_demo"
query = f"SELECT * FROM {table_name} WHERE entity_id = :id"
```

### State PostgreSQL (Port 5433)
- **Database**: `simulator_state`
- **Connection**: Environment `STATE_DB_URL`
- **Tables**: `simulator_state`, `simulator_activity_log`
- **API Role**: READ-ONLY (simulator service owns writes)

---

## Configuration

### config.json Structure
```json
{
  "local": {
    "dbUrl": "postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip",
    "dbScheme": "core",
    "loadDataFromCsv": false,
    "logLevel": "info",
    "app_client_id": "local-dev-no-auth",
    "user_pool_id": "local-dev-no-auth",
    "defaultUser": "test@datakwip.local"  // Skip JWT validation
  },
  "production": {
    "dbUrl": "postgresql://user:pass@host:port/db?sslmode=require",
    "dbScheme": "core",
    "app_client_id": "YOUR_COGNITO_APP_CLIENT_ID",
    "user_pool_id": "YOUR_COGNITO_USER_POOL_ID"
    // No defaultUser - enforce JWT validation
  }
}
```

### Environment Variables
- `dk_env` - Config key to use (local/production)
- `DATABASE_URL` - Override dbUrl from config.json
- `STATE_DB_URL` - State database connection

---

## Authentication Implementation

### Production Flow (AWS Cognito)
1. Extract JWT from `Authorization: Bearer {token}` header
2. Download JWKS from Cognito
3. Verify JWT signature using public key (RS256)
4. Validate issuer and audience claims
5. Extract email/username from token
6. Lookup user in `core.user` table by email
7. Attach `user_id` to `request.state`

**Code References:**
- Middleware: `api/src/app/main.py:118, 122-128`
- Header extraction: `api/src/app/services/request_service.py:13-28`
- JWT validation: `api/src/app/services/acl/user_service.py:16-103`

### Local Dev Flow (Default User)
When `defaultUser` is set in config.json:
1. Skip token validation entirely
2. Lookup user by email directly
3. Attach `user_id` to `request.state`

**No Authorization header required.**

---

## Common Development Tasks

### Adding a New Endpoint

**1. Define Pydantic Schemas** (`api/src/app/model/pydantic/`)
```python
from pydantic import BaseModel

class MyResourceCreate(BaseModel):
    org_id: int
    name: str
    value: float

class MyResource(BaseModel):
    id: int
    org_id: int
    name: str
    value: float
```

**2. Create SQLAlchemy Model** (`api/src/app/model/sqlalchemy/`)
```python
from sqlalchemy import Column, Integer, String, Float
from app.database.database import Base

class MyResource(Base):
    __tablename__ = "my_resource"
    __table_args__ = {'schema': 'core'}

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, nullable=False)
    name = Column(String)
    value = Column(Float)
```

**3. Create DTO** (`api/src/app/dto/my_resource_dto.py`)
```python
from sqlalchemy.orm import Session
from app.model.sqlalchemy.my_resource import MyResource

def create(db: Session, data: MyResourceCreate):
    resource = MyResource(**data.dict())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource

def get_by_org(db: Session, org_id: int, skip: int = 0, limit: int = 100):
    return db.query(MyResource)\
        .filter(MyResource.org_id == org_id)\
        .offset(skip).limit(limit).all()
```

**4. Create Router** (`api/src/app/api/my_resource.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.model.pydantic.my_resource import MyResourceCreate, MyResource
from app.dto import my_resource_dto

router = APIRouter()

@router.post("/my-resource", response_model=MyResource)
def create_resource(
    data: MyResourceCreate,
    db: Session = Depends(get_db)
):
    return my_resource_dto.create(db, data)

@router.get("/my-resource", response_model=list[MyResource])
def list_resources(
    org_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return my_resource_dto.get_by_org(db, org_id, skip, limit)
```

**5. Register Router** (`api/src/app/main.py`)
```python
from app.api.my_resource import router as my_resource_router

app.include_router(my_resource_router, tags=["my-resource"])
```

**6. Hand off to API Testing Agent** for test coverage

---

## Critical Design Principles

### 1. Multi-Tenancy
- **Always** require `org_id` parameter
- Use org-specific value tables from `core.org.value_table`
- Check user permissions: `is_entity_visible_for_user(db, org_id, user_id, entity_id)`

### 2. Never Hardcode Table Names
Every org has a unique value table. Always query `core.org` for the table name.

### 3. Error Handling
- **401 Unauthorized**: Missing/malformed Authorization header
- **403 Forbidden**: Invalid token, user not found, insufficient permissions
- **500 Internal Server Error**: Server-side errors
- Never expose sensitive data in error messages

### 4. Unicode Support
Always properly encode/decode for Windows and Linux:
```python
# File I/O
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Database strings already handled by SQLAlchemy
```

---

## Local Development

```bash
# Start databases
docker-compose up timescaledb statedb

# Install dependencies
cd api
pip install -r requirements.txt

# Run API
python src/app/main.py

# Access:
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - Health: http://localhost:8000/health
# - DB Health: http://localhost:8000/health/databases
```

---

## Troubleshooting

### API won't start
1. Check database connection in `config.json`
2. Verify `dbScheme` is set to `core`
3. Check `dk_env` environment variable
4. View logs: `docker-compose logs api`

### Authentication Errors
**Local Dev (401/403):**
```json
// config.json - local section
{
  "defaultUser": "test@datakwip.local",
  "app_client_id": "local-dev-no-auth",
  "user_pool_id": "local-dev-no-auth"
}
```

Then create test user:
```bash
docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip
```
```sql
INSERT INTO core."user" (email) VALUES ('test@datakwip.local')
ON CONFLICT DO NOTHING RETURNING id;

INSERT INTO core.org_user (org_id, user_id) VALUES (1, 1);
```

**Production (403 - user not found):**
User from JWT must exist in `core.user` table.

### Database Connection Errors
1. Ensure TimescaleDB running: `docker-compose up timescaledb`
2. Check credentials match `config.json`
3. Upgrade psycopg2-binary to >= 2.9.9 for SCRAM auth

### Schema Not Found
```bash
docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip
```
```sql
SELECT schema_name FROM information_schema.schemata;
\dt core.*
```

---

## Handoff Points

**To API Testing Agent:**
- When new endpoint is complete → request test coverage
- When modifying existing endpoint → request regression tests

**To Haystack Database Agent:**
- When database schema changes are needed
- When complex queries need optimization
- When hypertable configuration is needed

**To Docker Testing Agent:**
- When ready for integration testing
- When docker-compose configuration affects API

---

## Related Documentation

- [API README](../api/README.md)
- [Parent CLAUDE.md](../CLAUDE.md)
- [Database Schema](../schema/01_sql_schema_core_v2.sql)

---

## Agent Boundaries

**✅ CAN:**
- Modify API application code
- Update configuration files
- Add/modify endpoints, services, models
- Read database schema for reference
- Request test coverage from API Testing Agent

**❌ CANNOT:**
- Write or modify tests (API Testing Agent)
- Modify other services
- Change database schema (Haystack Database Agent)
- Run docker-compose (Docker Testing Agent)
