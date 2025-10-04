# Haystack Data Simulator - API Extension & GUI Implementation Plan

**Date:** 2025-10-03
**Status:** Planning Complete - Ready for Implementation
**Decision:** Extend existing `db-service-layer` API (approved by team)

---

## Executive Summary

After comprehensive analysis of the existing `db-service-layer` API, we've confirmed that **extending the existing API is the optimal approach**. The Haystack Data Simulator fits naturally as a "virtual poller" in the existing architecture, leveraging established patterns for multi-database writes, authentication, and poller management.

---

## Key Findings from db-service-layer Analysis

### ✅ Existing Infrastructure (Perfect Alignment!)

| Feature | Status | Details |
|---------|--------|---------|
| **Framework** | ✅ FastAPI | Same stack we'd choose for new API |
| **Multi-Database** | ✅ Implemented | Already handles multiple TimescaleDB instances |
| **Poller Infrastructure** | ✅ Complete | CRUD endpoints for poller management |
| **Bulk Value Insertion** | ✅ Production-ready | `POST /bulk/value` writes to all databases |
| **ACL/Authentication** | ✅ User/Org permissions | Complete access control system |
| **ORM** | ✅ SQLAlchemy | Same as simulator uses |
| **Connection Pooling** | ✅ Configured | Proper pool management with health checks |

### Existing Poller Model

The API already has a `poller_config` table in the `core` schema:

```python
class PollerConfig(Base):
    __tablename__ = "poller_config"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("core.org.id"), nullable=False)
    poller_type = Column(String, nullable=False)      # "bacnet", "modbus", "simulator"
    poller_id = Column(Integer, nullable=False, unique=True)
    poller_name = Column(String, nullable=False)
    config = Column(String, nullable=False)           # JSON configuration
    status = Column(String, nullable=False)           # "active", "inactive"
    created_at = Column(TIMESTAMP, server_default=text('NOW()'))
```

**Existing Endpoints:**
```
GET  /org/{org_id}/poller      # List pollers for organization
GET  /poller/{poller_id}        # Get specific poller details
GET  /poller?type={type}        # Get pollers by type
POST /poller                    # Create new poller
```

### Multi-Database Write Pattern (Already Implemented!)

The existing API has sophisticated multi-database handling:

```python
def create_bulk_value_multi_db(all_databases: list, values: ValueBulkCreate, ...):
    """
    - Iterates through all_databases array
    - Writes to each TimescaleDB instance
    - PRIMARY database failure → raises 503 error (poller should stop)
    - SECONDARY database failure → logs warning, continues
    - Returns success if primary succeeds
    """

    for db_config in all_databases:
        db_session = db_config['database'].get_local_session()
        try:
            value_service.add_bulk_value(db_session, values)
            value_service.add_bulk_value_current(db_session, values)
            db_session.commit()
            successful_writes += 1
        except Exception as e:
            if db_config.get('is_primary', False):
                raise PrimaryDatabaseException(...)  # Stop everything
            else:
                logger.warning(...)  # Continue with other DBs
```

**Key Insight:** Our simulator can use `POST /bulk/value` exactly as-is!

---

## Recommended Architecture

### Three-Tier Extension Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 3: Web GUI (Next.js + shadcn/ui)                      │
│  - System Dashboard                                          │
│  - Simulator Control Panel                                   │
│  - Database Inspector                                         │
│  - Activity Timeline                                          │
│  - Data Explorer (Haystack tag filtering)                    │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP/REST
                 │
┌────────────────▼────────────────────────────────────────────┐
│  Tier 2: API Extensions (db-service-layer + /simulator/*)   │
│  - Existing: /bulk/value, /poller, /entity, /tag_def        │
│  - NEW: /simulator/config, /simulator/state, /simulator/... │
│  - Manages simulator configs and operational state          │
└────┬───────────────────────────────────────────┬────────────┘
     │                                             │
     │ Writes to                                   │ Reads/writes
     ▼                                             ▼
┌────────────────────────┐            ┌──────────────────────┐
│  TimescaleDB           │            │  PostgreSQL          │
│  (Building Data)       │            │  (Simulator State)   │
│  - Entities            │            │  - simulator_state   │
│  - Tags                │            │  - activity_log      │
│  - Time-series values  │            │  - Last run time     │
└────────────────────────┘            └──────────────────────┘
     ▲
     │ Calls POST /bulk/value
     │
┌────┴───────────────────────────────────────────────────────┐
│  Tier 1: Simulator Service (haystack-data-simulator)       │
│  - Generates realistic building data                        │
│  - Calls API instead of direct DB writes                    │
│  - Manages internal generation state                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: API Extensions to db-service-layer (Week 1)

#### 1.1 Add State Database Connection

**File:** `src/app/services/config_service.py`

```python
# Add after existing database configuration
state_database = os.getenv('STATE_DB_URL',
    'postgresql://simulator_user:simulator_password@localhost:5433/simulator_state')

# Add pool size configs
state_db_pool_size = int(os.getenv('STATE_DB_POOL_SIZE', '5'))
state_db_max_overflow = int(os.getenv('STATE_DB_MAX_OVERFLOW', '5'))
```

**File:** `src/app/main.py`

```python
from app.db.database import Database

# Add after existing database initialization
state_database = Database(
    config_service.state_database,
    config_service.state_db_pool_size,
    config_service.state_db_max_overflow
)
state_database.init_database()

# Make available in request state
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    # ... existing code ...
    request.state.state_db = state_database.get_local_session()
    # ... existing code ...
    request.state.state_db.close()
```

#### 1.2 Create Simulator Models

**File:** `src/app/model/pydantic/simulator/simulator_config_schema.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SimulatorConfigBase(BaseModel):
    org_id: int
    simulator_name: str
    building_config: str      # JSON - building_config.yaml as JSON
    database_config: str      # JSON - which databases to write to
    interval_minutes: int
    status: str               # "active", "stopped", "error"

class SimulatorConfigCreate(SimulatorConfigBase):
    pass

class SimulatorConfig(SimulatorConfigBase):
    id: int
    simulator_id: int         # Unique ID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**File:** `src/app/model/pydantic/simulator/simulator_state_schema.py`

```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SimulatorState(BaseModel):
    id: int
    simulator_id: int
    service_name: str
    last_run_timestamp: Optional[datetime]
    totalizers: Dict[str, Any]        # Electric, gas, water meters
    status: str                        # "running", "stopped", "error"
    config: Dict[str, Any]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**File:** `src/app/model/pydantic/simulator/simulator_activity_schema.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ActivityLog(BaseModel):
    id: int
    simulator_id: int
    timestamp: datetime
    event_type: str           # "generation", "gap_fill", "error", "startup", "shutdown"
    message: str              # Domain-level description
    details: Optional[dict]   # Additional context (entity counts, interval info)

    class Config:
        from_attributes = True
```

#### 1.3 Create Simulator Services

**File:** `src/app/services/simulator_config_service.py`

```python
from sqlalchemy.orm import Session
from app.model.pydantic.simulator import simulator_config_schema
from app.model.sqlalchemy.poller_config_table import PollerConfig

def create_simulator_config(db: Session, config: simulator_config_schema.SimulatorConfigCreate):
    """Create simulator configuration and register as poller"""
    # Generate next simulator_id
    max_poller_id = db.query(PollerConfig.poller_id).order_by(
        PollerConfig.poller_id.desc()
    ).first()
    next_simulator_id = (max_poller_id[0] if max_poller_id else 0) + 1

    # Create poller_config entry
    db_config = PollerConfig(
        org_id=config.org_id,
        poller_type='simulator',
        poller_id=next_simulator_id,
        poller_name=config.simulator_name,
        config=config.model_dump_json(),  # Store full config as JSON
        status=config.status
    )

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return db_config

def get_simulator_configs(db: Session, org_id: int):
    """Get all simulator configs for organization"""
    return db.query(PollerConfig).filter(
        PollerConfig.org_id == org_id,
        PollerConfig.poller_type == 'simulator'
    ).all()
```

#### 1.4 Create New API Endpoints

**File:** `src/app/api/simulator/simulator_api.py`

```python
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.model.pydantic.simulator import simulator_config_schema, simulator_state_schema
from app.services import simulator_config_service, simulator_state_service

def init(app, get_db, get_state_db):

    # Configuration Management
    @app.post("/simulator/config", response_model=simulator_config_schema.SimulatorConfig)
    def create_simulator(
        config: simulator_config_schema.SimulatorConfigCreate,
        request: Request,
        db: Session = Depends(get_db)
    ):
        """Create new simulator configuration"""
        user_id = request.state.user_id
        # TODO: Check user has permission for org_id
        return simulator_config_service.create_simulator_config(db, config)

    @app.get("/simulator/config", response_model=list[simulator_config_schema.SimulatorConfig])
    def get_simulators(
        org_id: int,
        request: Request,
        db: Session = Depends(get_db)
    ):
        """Get all simulators for organization"""
        return simulator_config_service.get_simulator_configs(db, org_id)

    @app.get("/simulator/config/{simulator_id}", response_model=simulator_config_schema.SimulatorConfig)
    def get_simulator(
        simulator_id: int,
        request: Request,
        db: Session = Depends(get_db)
    ):
        """Get specific simulator configuration"""
        return simulator_config_service.get_simulator_config(db, simulator_id)

    # State Management
    @app.get("/simulator/state/{simulator_id}", response_model=simulator_state_schema.SimulatorState)
    def get_simulator_state(
        simulator_id: int,
        request: Request,
        state_db: Session = Depends(get_state_db)
    ):
        """Get simulator operational state"""
        return simulator_state_service.get_state(state_db, simulator_id)

    @app.post("/simulator/state/{simulator_id}")
    def update_simulator_state(
        simulator_id: int,
        state_update: dict,
        request: Request,
        state_db: Session = Depends(get_state_db)
    ):
        """Update simulator state (called by simulator service)"""
        return simulator_state_service.update_state(state_db, simulator_id, state_update)

    # Activity & Health
    @app.get("/simulator/activity/{simulator_id}")
    def get_activity_log(
        simulator_id: int,
        limit: int = 100,
        request: Request,
        state_db: Session = Depends(get_state_db)
    ):
        """Get recent activity log entries"""
        return simulator_state_service.get_activity_log(state_db, simulator_id, limit)

    @app.get("/simulator/health/{simulator_id}")
    def get_simulator_health(
        simulator_id: int,
        request: Request,
        db: Session = Depends(get_db),
        state_db: Session = Depends(get_state_db)
    ):
        """Get simulator health status"""
        config = simulator_config_service.get_simulator_config(db, simulator_id)
        state = simulator_state_service.get_state(state_db, simulator_id)

        return {
            'simulator_id': simulator_id,
            'name': config.simulator_name,
            'status': state.status,
            'last_run': state.last_run_timestamp,
            'config_status': config.status,
            'healthy': state.status == 'running' and state.error_message is None
        }
```

**Register in main.py:**

```python
from app.api.simulator import simulator_api

# After other API initializations
simulator_api.init(app, get_db, get_state_db)
```

---

### Phase 2: Modify Simulator Service to Use API (Week 2)

#### 2.1 Add API Client to Simulator

**File:** `src/service/api_client.py` (NEW)

```python
"""API client for communicating with db-service-layer"""

import logging
import requests
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DataKwipAPIClient:
    """Client for db-service-layer API"""

    def __init__(self, api_url: str, api_token: str, simulator_id: int):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.simulator_id = simulator_id
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }

    def bulk_insert_values(self, org_id: int, values: List[Dict]) -> bool:
        """Insert batch of values using /bulk/value endpoint"""
        try:
            response = requests.post(
                f"{self.api_url}/bulk/value",
                json={
                    'org_id': org_id,
                    'values': values
                },
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 503:
                logger.error("Primary database unavailable - stopping generation")
                return False

            response.raise_for_status()
            logger.info(f"Successfully inserted {len(values)} values via API")
            return True

        except Exception as e:
            logger.error(f"API bulk insert failed: {e}")
            return False

    def update_state(self, state_update: Dict[str, Any]) -> bool:
        """Update simulator state"""
        try:
            response = requests.post(
                f"{self.api_url}/simulator/state/{self.simulator_id}",
                json=state_update,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            return False

    def log_activity(self, event_type: str, message: str, details: Dict = None):
        """Log activity event"""
        try:
            response = requests.post(
                f"{self.api_url}/simulator/activity/{self.simulator_id}",
                json={
                    'event_type': event_type,
                    'message': message,
                    'details': details or {}
                },
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to log activity: {e}")
```

#### 2.2 Modify ContinuousDataService

**File:** `src/service/continuous_generator.py`

```python
# Add to __init__:
def __init__(self, db_config: Dict[str, Any], building_config: Dict[str, Any],
             value_table: str = 'values_demo', api_client: Optional[APIClient] = None):
    # ... existing code ...
    self.api_client = api_client  # NEW
    self.use_api = api_client is not None  # NEW

# Modify generate_current_interval:
def generate_current_interval(self) -> bool:
    try:
        # ... existing generation code ...

        if self.use_api:
            # NEW: Use API instead of direct DB writes
            values_payload = [
                {
                    'ts': dp.timestamp.isoformat(),
                    'entity_id': dp.entity_id,
                    'value_n': dp.value_n,
                    'value_b': dp.value_b,
                    'value_s': dp.value_s,
                    'value_ts': dp.value_ts.isoformat() if dp.value_ts else None
                }
                for dp in data_points
            ]

            success = self.api_client.bulk_insert_values(
                org_id=self.db_config['organization']['id'],
                values=values_payload
            )

            if not success:
                return False

            # Update state via API
            self.api_client.update_state({
                'last_run_timestamp': aligned_time.isoformat(),
                'totalizers': ts_gen.totalizers,
                'status': 'running'
            })

            # Log activity
            self.api_client.log_activity(
                event_type='generation',
                message=f"Generated {len(data_points)} points for interval {aligned_time}",
                details={
                    'interval': aligned_time.isoformat(),
                    'point_count': len(data_points),
                    'weather': weather,
                    'occupancy': occupancy
                }
            )
        else:
            # EXISTING: Direct DB writes (for local development)
            data_loader.insert_time_series_batch(data_points)
            data_loader.update_current_values(data_points)
            self.state_manager.save_service_state(...)

        return True
```

#### 2.3 Update service_main.py

**File:** `src/service_main.py`

```python
from service.api_client import DataKwipAPIClient

def main():
    # ... existing config loading ...

    # NEW: API configuration
    api_url = os.getenv('API_URL')
    api_token = os.getenv('API_TOKEN')
    simulator_id = int(os.getenv('SIMULATOR_ID', '1'))

    api_client = None
    if api_url and api_token:
        logger.info(f"Using API mode: {api_url}")
        api_client = DataKwipAPIClient(api_url, api_token, simulator_id)
    else:
        logger.info("Using direct DB mode (local development)")

    # Initialize service with API client
    service = ContinuousDataService(
        db_config,
        building_config,
        value_table,
        api_client=api_client  # NEW
    )
```

---

### Phase 3: Web GUI (Next.js + shadcn/ui) (Weeks 3-4)

#### 3.1 Project Structure

```
webapp/
├── app/
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Authenticated layout
│   │   ├── page.tsx             # Main dashboard
│   │   ├── simulator/
│   │   │   └── page.tsx         # Simulator control
│   │   ├── activity/
│   │   │   └── page.tsx         # Activity timeline
│   │   ├── database/
│   │   │   └── page.tsx         # Database inspector
│   │   ├── explorer/
│   │   │   └── page.tsx         # Data explorer
│   │   └── settings/
│   │       └── page.tsx         # Settings
│   └── api/
│       ├── auth/
│       │   └── route.ts         # Login endpoint
│       └── [...proxy]/
│           └── route.ts         # Proxy to db-service-layer
├── components/
│   ├── ui/                      # shadcn/ui components
│   ├── dashboard/
│   │   ├── StatusCard.tsx
│   │   ├── HealthCheck.tsx
│   │   └── QuickActions.tsx
│   ├── simulator/
│   │   ├── ConfigEditor.tsx
│   │   ├── ControlPanel.tsx
│   │   └── MetricsDisplay.tsx
│   ├── activity/
│   │   ├── Timeline.tsx
│   │   └── EventCard.tsx
│   └── explorer/
│       ├── TagFilter.tsx
│       └── TimeSeriesChart.tsx
├── lib/
│   ├── api-client.ts            # API fetch utilities
│   ├── auth.ts                  # Authentication utilities
│   └── utils.ts                 # Helper functions
└── package.json
```

#### 3.2 Key Features

**Dashboard (`app/(dashboard)/page.tsx`):**

```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import { StatusCard } from '@/components/dashboard/StatusCard'
import { HealthCheck } from '@/components/dashboard/HealthCheck'

export default function DashboardPage() {
  const { data: health } = useQuery({
    queryKey: ['simulator-health'],
    queryFn: () => fetch('/api/simulator/health/1').then(r => r.json()),
    refetchInterval: 5000  // Poll every 5 seconds
  })

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <StatusCard
        title="Simulator Status"
        value={health?.status || 'Unknown'}
        icon={health?.healthy ? '✓' : '✗'}
      />
      <StatusCard
        title="Last Run"
        value={health?.last_run ? new Date(health.last_run).toLocaleString() : 'Never'}
      />
      <StatusCard
        title="Data Points Generated"
        value={health?.total_points?.toLocaleString() || '0'}
      />

      <HealthCheck
        timescaledb={health?.databases?.timescaledb}
        statedb={health?.databases?.statedb}
      />
    </div>
  )
}
```

**Activity Timeline (`app/(dashboard)/activity/page.tsx`):**

```typescript
'use client'

import { useEffect, useState } from 'react'
import { Timeline } from '@/components/activity/Timeline'

export default function ActivityPage() {
  const [events, setEvents] = useState([])

  useEffect(() => {
    // Server-Sent Events for real-time updates
    const eventSource = new EventSource('/api/simulator/activity/stream/1')

    eventSource.onmessage = (event) => {
      const newEvent = JSON.parse(event.data)
      setEvents(prev => [newEvent, ...prev].slice(0, 100))
    }

    return () => eventSource.close()
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-bold">Activity Timeline</h1>
      <Timeline events={events} />
    </div>
  )
}
```

**Data Explorer (`app/(dashboard)/explorer/page.tsx`):**

```typescript
'use client'

import { useState } from 'react'
import { TagFilter } from '@/components/explorer/TagFilter'
import { TimeSeriesChart } from '@/components/explorer/TimeSeriesChart'

export default function ExplorerPage() {
  const [selectedTags, setSelectedTags] = useState({})
  const [entities, setEntities] = useState([])

  return (
    <div className="space-y-4">
      <TagFilter
        tags={selectedTags}
        onChange={setSelectedTags}
        onSearch={() => {
          // Fetch entities matching tag filter
          fetch('/api/filter', {
            method: 'POST',
            body: JSON.stringify({ tags: selectedTags })
          }).then(r => r.json()).then(setEntities)
        }}
      />

      <TimeSeriesChart entities={entities} />
    </div>
  )
}
```

#### 3.3 Authentication

```typescript
// lib/auth.ts
import { SignJWT, jwtVerify } from 'jose'

const SECRET = new TextEncoder().encode(process.env.AUTH_SECRET)

export async function createToken(username: string) {
  return await new SignJWT({ username })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('24h')
    .sign(SECRET)
}

export async function verifyToken(token: string) {
  try {
    const verified = await jwtVerify(token, SECRET)
    return verified.payload
  } catch {
    return null
  }
}

// middleware.ts
import { NextResponse } from 'next/server'
import { verifyToken } from '@/lib/auth'

export async function middleware(request) {
  const token = request.cookies.get('auth-token')?.value

  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  const payload = await verifyToken(token)
  if (!payload) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/(dashboard|simulator|activity|database|explorer|settings)/:path*']
}
```

---

### Phase 4: Docker Compose & Deployment (Week 5)

#### 4.1 Updated docker-compose.yaml

```yaml
version: '3.8'

services:
  # TimescaleDB - Building Data
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    container_name: haystack-timescaledb
    environment:
      POSTGRES_DB: datakwip
      POSTGRES_USER: datakwip_user
      POSTGRES_PASSWORD: datakwip_password
    ports:
      - "5432:5432"
    volumes:
      - timescale-data:/var/lib/postgresql/data
      - ./schema/01_sql_schema_core_v2.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U datakwip_user -d datakwip"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - haystack-network

  # PostgreSQL - Simulator State
  statedb:
    image: postgres:15-alpine
    container_name: haystack-statedb
    environment:
      POSTGRES_DB: simulator_state
      POSTGRES_USER: simulator_user
      POSTGRES_PASSWORD: simulator_password
    ports:
      - "5433:5432"
    volumes:
      - state-data:/var/lib/postgresql/data
      - ./schema/02_simulator_state.sql:/docker-entrypoint-initdb.d/01_state.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U simulator_user -d simulator_state"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - haystack-network

  # API Service (db-service-layer)
  api:
    build:
      context: ../db-service-layer
      dockerfile: Dockerfile
    container_name: haystack-api
    environment:
      DATABASE_URL: postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip
      STATE_DB_URL: postgresql://simulator_user:simulator_password@statedb:5432/simulator_state
      dk_env: "tigerdata"
      MAIN_DB_POOL_SIZE: 10
      MAIN_DB_MAX_OVERFLOW: 10
    ports:
      - "8000:8000"
    depends_on:
      timescaledb:
        condition: service_healthy
      statedb:
        condition: service_healthy
    networks:
      - haystack-network

  # Simulator Service
  simulator:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: haystack-simulator
    environment:
      API_URL: http://api:8000
      API_TOKEN: ${SIMULATOR_API_TOKEN}
      SIMULATOR_ID: 1
      STATE_DB_URL: postgresql://simulator_user:simulator_password@statedb:5432/simulator_state
      HEALTH_CHECK_PORT: 8080
      SERVICE_INTERVAL_MINUTES: 15
      BUILDING_CONFIG_PATH: config/building_config.yaml
    ports:
      - "8080:8080"
    depends_on:
      - api
    networks:
      - haystack-network

  # Web GUI
  webapp:
    build:
      context: ./webapp
      dockerfile: Dockerfile
    container_name: haystack-webapp
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      API_INTERNAL_URL: http://api:8000
      AUTH_SECRET: ${WEB_AUTH_SECRET}
      AUTH_USERNAME: ${WEB_USERNAME}
      AUTH_PASSWORD: ${WEB_PASSWORD}
    ports:
      - "3000:3000"
    depends_on:
      - api
    networks:
      - haystack-network

volumes:
  timescale-data:
  state-data:

networks:
  haystack-network:
    driver: bridge
```

#### 4.2 Railway Deployment

**Three Railway Projects:**

1. **db-service-layer** (API)
   - Add TimescaleDB addon → `DATABASE_URL`
   - Add PostgreSQL addon → `STATE_DB_URL`
   - Deploy from GitHub (db-service-layer repo)

2. **haystack-data-simulator** (Simulator Service)
   - Environment variables:
     - `API_URL` → https://your-api.railway.app
     - `API_TOKEN` → (generate secure token)
     - `SIMULATOR_ID` → 1
     - `STATE_DB_URL` → (same as API's STATE_DB_URL)
   - Deploy from GitHub (haystack-data-simulator repo)

3. **haystack-webapp** (Web GUI)
   - Deploy to Vercel or Railway
   - Environment variables:
     - `NEXT_PUBLIC_API_URL` → https://your-api.railway.app
     - `AUTH_SECRET`, `AUTH_USERNAME`, `AUTH_PASSWORD`

---

## Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| ✅ **Team Alignment** | Extends existing API per team's preference |
| ✅ **Conceptual Fit** | Simulator as "virtual poller" makes sense |
| ✅ **Multi-DB Support** | Leverages existing multi-database writes |
| ✅ **Backwards Compatible** | No changes to existing endpoints |
| ✅ **Clean Separation** | Building data vs. operational state |
| ✅ **Production Ready** | Uses existing ACL, pooling, error handling |
| ✅ **Unified Interface** | One API for all building data operations |
| ✅ **Scalable** | Can add multiple simulator instances |

---

## Migration Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1:** API Extensions | 1 week | `/simulator/*` endpoints, state DB integration |
| **Phase 2:** Simulator Integration | 1 week | API client, modified services, testing |
| **Phase 3:** Web GUI | 2 weeks | Full Next.js app with all features |
| **Phase 4:** Deployment | 3 days | Railway deployment, production testing |
| **Total** | ~4 weeks | Complete integrated system |

---

## Open Questions for Next Session

1. **Authentication Strategy**
   - Should simulator use existing Cognito user pool?
   - Or create separate API token system for simulator?

2. **Activity Log Storage**
   - Add `simulator_activity_log` table to state DB?
   - Or store in TimescaleDB with time-series?

3. **Multi-Simulator Support**
   - Support multiple simulator instances per organization?
   - How to handle simulator discovery/registration?

4. **API Repository**
   - Fork `db-service-layer` or create feature branch?
   - How to coordinate with team's existing development?

5. **Data Explorer Complexity**
   - Build full Haystack query language support?
   - Or start with simple tag AND/OR filtering?

---

## Next Steps

**When ready to implement:**

1. Clone `db-service-layer` repository
2. Create feature branch: `feature/simulator-support`
3. Implement Phase 1 changes (state DB + endpoints)
4. Test locally with existing simulator
5. Build basic GUI dashboard
6. Deploy to Railway for testing

---

**Last Updated:** 2025-10-03
**Status:** Ready for implementation - awaiting team decision on repository access
