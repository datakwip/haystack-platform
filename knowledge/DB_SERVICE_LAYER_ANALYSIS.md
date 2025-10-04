# db-service-layer API - Technical Analysis

**Repository:** https://github.com/datakwip/db-service-layer
**Analysis Date:** 2025-10-03
**Purpose:** Understanding existing API for Haystack Simulator integration

---

## Executive Summary

The `db-service-layer` is a production FastAPI application that provides REST endpoints for managing building automation data in TimescaleDB. It has sophisticated multi-database support, poller management infrastructure, and ACL/authentication. The simulator can integrate naturally as a `poller_type='simulator'`.

---

## Core Architecture

### Technology Stack

```
FastAPI (Python web framework)
├── SQLAlchemy (ORM)
├── psycopg2 (PostgreSQL driver)
├── Pydantic (data validation)
└── uvicorn (ASGI server)

TimescaleDB (time-series data)
├── Connection pooling (configurable)
├── Multiple database support
└── Same schema as simulator (core.entity, core.entity_tag, etc.)
```

### Configuration System

**File:** `src/app/services/config_service.py`

```python
# Loads from config.json
config = jsoncfg.load_config('./config.json')

# Supports comma-separated configs
dk_env = os.getenv('dk_env')  # "tigerdata,prod,staging"
config_keys = [key.strip() for key in dk_env.split(',')]

# First config is primary
primary_config_key = config_keys[0]

# Each config has:
{
    'key': 'tigerdata',
    'dbUrl': 'postgresql://...',
    'dbUrlGrafanaConnector': 'postgresql://...',
    'dbScheme': 'core',
    'app_client_id': '...',
    'user_pool_id': '...',
    'is_primary': True,
    'is_available': True  # Checked via test connection
}
```

**Key Insight:** API already supports multiple TimescaleDB instances!

---

## Database Layer

### Database Class

**File:** `src/app/db/database.py`

```python
class Database():
    def __init__(self, databaseUrl: str, pool_size: int = 5, max_overflow: int = 5):
        self.__databaseUrl = databaseUrl
        self.__pool_size = pool_size
        self.__max_overflow = max_overflow

    def init_database(self):
        self.__engine = create_engine(
            self.__databaseUrl,
            echo=False,
            pool_size=self.__pool_size,
            max_overflow=self.__max_overflow,
            pool_pre_ping=True,      # Validates connections before use
            pool_recycle=3600,       # Recycle connections every hour
        )
        self.__session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.__engine
        )
        self.__base = declarative_base()

    def get_engine(self):
        return self.__engine

    def get_local_session(self):
        return self.__session()

    def get_base(self):
        return self.__base

    def log_connection_stats(self):
        """Log current connection pool statistics"""
        pool = self.__engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow()
        }
```

**Key Features:**
- Connection pooling with configurable size
- Pre-ping for connection validation
- Hourly connection recycling
- Connection stats logging

### Multi-Database Initialization

**File:** `src/app/main.py`

```python
# Primary database (for most operations)
database = Database(
    config_service.database,
    config_service.main_db_pool_size,
    config_service.main_db_max_overflow
)
database.init_database()

# Grafana connector database (read-only queries)
database_grafana_connector = DatabaseGrafanaConnector(
    config_service.database_grafana_connector,
    config_service.grafana_db_pool_size,
    config_service.grafana_db_max_overflow
)
database_grafana_connector.init_database()

# All databases (for multi-write operations)
all_databases = []
for config in config_service.available_configs:
    db = Database(config['dbUrl'], ...)
    db.init_database()
    all_databases.append({
        'key': config['key'],
        'database': db,
        'is_primary': config['is_primary'],
        'is_available': config['is_available']
    })
```

### Request Middleware

**File:** `src/app/main.py`

```python
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Provide database sessions in request state
    request.state.db = database.get_local_session()
    request.state.db_grafana_connector = database_grafana_connector.get_local_session()
    request.state.all_databases = all_databases  # For multi-DB writes
    request.state.request_id = request_id
    request.state.user_id = user_service.get_current_user(request, ...)

    try:
        response = await call_next(request)
        response.headers["dq-request-id"] = request_id
    finally:
        request.state.db.close()
        request.state.db_grafana_connector.close()

    return response
```

**Key Insight:** Every request has access to all database sessions!

---

## Poller Infrastructure

### Poller Config Model

**SQLAlchemy Model:** `src/app/model/sqlalchemy/poller_config_table.py`

```python
class PollerConfig(Base):
    __tablename__ = "poller_config"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("core.org.id"), nullable=False, index=True)
    poller_type = Column(String, nullable=False)      # "bacnet", "modbus", "simulator"
    poller_id = Column(Integer, nullable=False, unique=True)
    poller_name = Column(String, nullable=False)
    config = Column(String, nullable=False)           # JSON configuration
    status = Column(String, nullable=False)           # "active", "inactive"
    created_at = Column(TIMESTAMP, server_default=text('NOW()'))

    __table_args__ = (
        {'schema': config_service.dbSchema}  # Lives in 'core' schema
    )
```

**Pydantic Schema:** `src/app/model/pydantic/source_objects/poller_config_schema.py`

```python
class PollerConfigBase(BaseModel):
    poller_type: str
    poller_name: str
    config: str          # JSON string
    status: str

class PollerConfigCreate(PollerConfigBase):
    org_id: int

class PollerConfig(PollerConfigBase):
    id: int
    org_id: int
    poller_id: int       # Auto-incremented unique ID
    created_at: datetime

    class Config:
        from_attributes = True
```

### Poller Service Layer

**File:** `src/app/services/poller_config_service.py`

```python
def get_poller_configs_by_org(db: Session, org_id: int) -> List[PollerConfig]:
    """Get all active pollers for organization"""
    db_configs = db.query(PollerConfig).filter(
        PollerConfig.org_id == org_id,
        PollerConfig.status == "active"
    ).all()
    return [_convert_to_schema(config) for config in db_configs]

def get_poller_config_by_poller_id(db: Session, poller_id: int) -> PollerConfig:
    """Get specific poller by ID"""
    db_config = db.query(PollerConfig).filter(
        PollerConfig.poller_id == poller_id,
        PollerConfig.status == "active"
    ).first()
    if db_config:
        return _convert_to_schema(db_config)
    return None

def get_poller_configs_by_type(db: Session, poller_type: str) -> List[PollerConfig]:
    """Get all pollers of specific type"""
    db_configs = db.query(PollerConfig).filter(
        PollerConfig.poller_type == poller_type,
        PollerConfig.status == "active"
    ).all()
    return [_convert_to_schema(config) for config in db_configs]

def create_poller_config(db: Session, config: PollerConfigCreate) -> PollerConfig:
    """Create new poller configuration"""
    # Generate next available poller_id
    max_poller_id = db.query(PollerConfig.poller_id).order_by(
        PollerConfig.poller_id.desc()
    ).first()
    next_poller_id = (max_poller_id[0] if max_poller_id else 0) + 1

    db_config = PollerConfig(
        org_id=config.org_id,
        poller_type=config.poller_type,
        poller_id=next_poller_id,
        poller_name=config.poller_name,
        config=config.config,
        status=config.status
    )

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return _convert_to_schema(db_config)
```

### Poller API Endpoints

**File:** `src/app/api/poller_config/poller_config.py`

```python
def init(app, get_db):

    @app.get("/org/{org_id}/poller", response_model=list[PollerConfig])
    def get_pollers_for_org(org_id: int, db: Session = Depends(get_db)):
        """List all pollers for organization"""
        return poller_config_service.get_poller_configs_by_org(db, org_id)

    @app.get("/poller/{poller_id}", response_model=PollerConfig)
    def get_poller(poller_id: int, db: Session = Depends(get_db)):
        """Get specific poller details"""
        config = poller_config_service.get_poller_config_by_poller_id(db, poller_id)
        if not config:
            raise HTTPException(status_code=404, detail="Poller not found")
        return config

    @app.get("/poller", response_model=list[PollerConfig])
    def get_pollers_by_type(type: str, db: Session = Depends(get_db)):
        """Get all pollers of specific type"""
        return poller_config_service.get_poller_configs_by_type(db, type)

    @app.post("/poller", response_model=PollerConfig)
    def create_poller(config: PollerConfigCreate, db: Session = Depends(get_db)):
        """Create new poller"""
        return poller_config_service.create_poller_config(db, config)
```

**For Simulator Integration:**

```python
# Create simulator as a poller
POST /poller
{
    "org_id": 1,
    "poller_type": "simulator",
    "poller_name": "Haystack Simulator - HQ Building",
    "config": "{\"building_config\": {...}, \"interval_minutes\": 15}",
    "status": "active"
}

# List all simulators
GET /poller?type=simulator

# Get specific simulator
GET /poller/123
```

---

## Value Insertion (Multi-Database Pattern)

### Bulk Value Endpoint

**File:** `src/app/api/source_objects/value.py`

```python
@app.post("/bulk/value", response_model=list[ValueBase])
def add_bulk_values(
    values: ValueBulkCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user_id = request.state.user_id
        default_user_id = request.state.default_user_id
        all_databases = request.state.all_databases

        # Call multi-DB write function
        return value_dto.create_bulk_value_multi_db(
            all_databases=all_databases,
            values=values,
            user_id=user_id,
            default_user_id=default_user_id
        )

    except PrimaryDatabaseException as e:
        # Primary database failed - return 503 to signal poller to stop
        raise HTTPException(status_code=503, detail=f"Primary database unavailable: {e.message}")

    except AccessDeniedException as e:
        raise HTTPException(status_code=403, detail=e.to_json())

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Multi-Database Write Logic

**File:** `src/app/dto/source_objects/value_dto.py`

```python
def create_bulk_value_multi_db(
    all_databases: list,
    values: ValueBulkCreate,
    user_id: int,
    default_user_id: str
):
    """Create bulk values in multiple databases"""

    # Extract entity IDs for permission check
    entity_ids = [value.entity_id for value in values.values]

    # Use primary database for permission checks
    primary_db_config = next(
        (db for db in all_databases if db.get('is_primary', False)),
        all_databases[0]
    )
    primary_db = primary_db_config['database'].get_local_session()

    try:
        # Check permissions on primary DB
        if not (default_user_id is not None or
                user_service.is_entities_visible_for_user(primary_db, values.org_id, user_id, entity_ids)):
            raise AccessDeniedException(...)

        results = []
        successful_writes = 0

        # Write to each database
        for db_config in all_databases:
            db_session = db_config['database'].get_local_session()
            try:
                # Insert to values table
                db_values = value_service.add_bulk_value(db_session, values)

                # Insert to current values table
                db_values_current = value_service.add_bulk_value_current(db_session, values)

                db_session.commit()
                successful_writes += 1
                results.append(db_values)

                logger.info(f"Successfully wrote bulk values to database {db_config['key']}")

            except Exception as e:
                db_session.rollback()

                if db_config.get('is_primary', False):
                    # Primary database failure - STOP EVERYTHING
                    logger.error(f'Primary database {db_config["key"]} failed: {str(e)}')
                    raise PrimaryDatabaseException(
                        f"Primary database {db_config['key']} failed during bulk value creation", e
                    )
                else:
                    # Secondary database failure - log and continue
                    logger.warning(f'Secondary database {db_config["key"]} failed: {str(e)}. Continuing.')

            finally:
                db_session.close()

        logger.info(f"Bulk values successfully written to {successful_writes} out of {len(all_databases)} databases")
        return results[0] if results else []

    finally:
        primary_db.close()
```

**Key Insights:**

1. **Permission Check Once:** Uses primary DB only
2. **Write to All:** Attempts to write to every database in `all_databases`
3. **Primary DB Failure → 503:** Tells poller to stop trying
4. **Secondary DB Failure → Warning:** Logs but continues
5. **Atomic per DB:** Each database has its own transaction

**For Simulator:**

```python
# Simulator calls this endpoint
POST /bulk/value
{
    "org_id": 1,
    "values": [
        {
            "ts": "2025-10-03T14:00:00Z",
            "entity_id": 123,
            "value_n": 72.5,
            "value_b": null,
            "value_s": null,
            "value_ts": null
        },
        # ... 280 more points
    ]
}

# API writes to ALL configured databases
# Returns 200 if primary succeeds
# Returns 503 if primary fails → simulator should stop
```

### Value Service Layer

**File:** `src/app/services/value_service.py`

```python
def add_bulk_value(db: Session, values: ValueBulkCreate):
    """Insert bulk values into values table"""
    if values.org_id in values_tables.value_tables:
        table = values_tables.value_tables[values.org_id]

        db_values = []
        for val in values.values:
            db_value = {
                "ts": val.ts,
                "entity_id": val.entity_id,
                "value_n": val.value_n,
                "value_b": val.value_b,
                "value_s": val.value_s,
                "value_ts": val.value_ts,
            }
            db_values.append(db_value)

        # Use PostgreSQL UPSERT (ON CONFLICT DO UPDATE)
        stmt = insert(table).values(db_values)
        primary_keys = [key.name for key in inspect(table).primary_key]

        stmt = stmt.on_conflict_do_update(
            index_elements=primary_keys,
            set_={
                "value_n": stmt.excluded.value_n,
                "value_b": stmt.excluded.value_b,
                "value_s": stmt.excluded.value_s,
                "value_ts": stmt.excluded.value_ts,
            }
        )

        db.execute(stmt)
        db.flush()

        return db_values
```

**Key Insight:** Uses UPSERT for idempotency - safe to retry!

---

## Authentication & Authorization

### User Service

The API has existing authentication via AWS Cognito:

```python
# From config
app_client_id = config['app_client_id']
user_pool_id = config['user_pool_id']

# Middleware sets user_id in request state
request.state.user_id = user_service.get_current_user(request, db, default_user)
```

### ACL (Access Control Lists)

**Tables in database:**
- `core.acl_user` - User permissions
- `core.acl_org` - Organization permissions
- `core.org_entity_permission` - Entity-level access

**Permission Checks:**

```python
# Check if user can see entities
user_service.is_entities_visible_for_user(db, org_id, user_id, entity_ids)

# Check if user can see entity
user_service.is_entity_visible_for_user(db, org_id, user_id, entity_id)
```

**For Simulator:**

Option 1: Use existing Cognito authentication
- Simulator has user credentials
- Gets JWT token from Cognito
- Includes in Authorization header

Option 2: Create service account / API token
- Generate long-lived token for simulator
- Store in environment variable
- Bypass Cognito for simulator-specific endpoints

---

## Integration Points for Simulator

### 1. Register Simulator as Poller

```python
# On simulator startup
POST /poller
{
    "org_id": 1,
    "poller_type": "simulator",
    "poller_name": "Haystack Simulator - HQ",
    "config": json.dumps({
        "building_config": {...},
        "interval_minutes": 15,
        "value_table": "values_demo"
    }),
    "status": "active"
}
# Returns: {"poller_id": 123, ...}
```

### 2. Generate Data → Bulk Insert

```python
# In simulator service, every 15 minutes
data_points = generate_current_interval()

# Convert to API format
values_payload = {
    "org_id": 1,
    "values": [
        {
            "ts": dp.timestamp.isoformat(),
            "entity_id": dp.entity_id,
            "value_n": dp.value_n,
            "value_b": dp.value_b,
            "value_s": dp.value_s,
            "value_ts": dp.value_ts.isoformat() if dp.value_ts else None
        }
        for dp in data_points
    ]
}

# Call API
response = requests.post(
    f"{API_URL}/bulk/value",
    json=values_payload,
    headers={"Authorization": f"Bearer {api_token}"}
)

if response.status_code == 503:
    # Primary DB down - stop generating
    logger.error("Primary database unavailable - stopping")
    return False
```

### 3. New Endpoints Needed

The following endpoints don't exist yet and need to be added:

```python
# Simulator state management
GET    /simulator/state/{simulator_id}
POST   /simulator/state/{simulator_id}

# Simulator control
POST   /simulator/start/{simulator_id}
POST   /simulator/stop/{simulator_id}
POST   /simulator/reset/{simulator_id}

# Simulator monitoring
GET    /simulator/health/{simulator_id}
GET    /simulator/activity/{simulator_id}
GET    /simulator/metrics/{simulator_id}
```

These will be added in Phase 1 of implementation.

---

## Schema Compatibility

### Existing Schema (in TimescaleDB)

```sql
-- Same schema as simulator uses!
core.org
core.entity
core.entity_tag
core.tag_def
core.values_<org_key>          -- Hypertable
core.values_<org_key>_current  -- Hypertable
```

**Key Insight:** API uses EXACT SAME schema as simulator!

### Poller Config Table (Existing)

```sql
CREATE TABLE core.poller_config (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES core.org(id),
    poller_type VARCHAR NOT NULL,
    poller_id INTEGER UNIQUE NOT NULL,
    poller_name VARCHAR NOT NULL,
    config VARCHAR NOT NULL,  -- JSON
    status VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### State Tables (Need to Add to State DB)

```sql
-- Already exists from our implementation
CREATE TABLE core.simulator_state (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) DEFAULT 'haystack_simulator',
    last_run_timestamp TIMESTAMPTZ,
    totalizers JSONB,
    status VARCHAR(50) DEFAULT 'stopped',
    config JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Need to add
CREATE TABLE core.simulator_activity_log (
    id SERIAL PRIMARY KEY,
    simulator_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_log_simulator_id ON core.simulator_activity_log(simulator_id);
CREATE INDEX idx_activity_log_timestamp ON core.simulator_activity_log(timestamp DESC);
```

---

## Summary of Key Findings

| Finding | Implication for Simulator |
|---------|---------------------------|
| ✅ FastAPI framework | Same stack we'd choose |
| ✅ Multi-DB writes implemented | Can write to multiple TimescaleDB instances |
| ✅ Poller infrastructure exists | Simulator fits as `poller_type='simulator'` |
| ✅ Bulk value endpoint | Use `/bulk/value` as-is |
| ✅ Same schema | No schema changes needed |
| ✅ Connection pooling | Production-ready performance |
| ✅ Error handling | 503 on primary DB failure |
| ✅ ACL system | Can integrate with existing permissions |
| ⚠️ State management | Need to add `/simulator/state` endpoints |
| ⚠️ Activity logging | Need to add activity log table and endpoints |

---

## Recommendation

**EXTEND EXISTING API** - All evidence points to this being the correct approach:

1. Infrastructure already exists (poller model, multi-DB, bulk insert)
2. Same technology stack (FastAPI, SQLAlchemy, TimescaleDB)
3. Same database schema (no conflicts)
4. Team preference (maintains single source of truth)
5. Production-ready patterns (pooling, error handling, ACL)

**Implementation approach:**
- Add `/simulator/*` endpoints to `db-service-layer`
- Add state database connection (PostgreSQL)
- Modify simulator to call API instead of direct DB writes
- Build Next.js GUI that talks to extended API

---

**Analysis Complete:** 2025-10-03
**Next Step:** Begin Phase 1 implementation (API extensions)
