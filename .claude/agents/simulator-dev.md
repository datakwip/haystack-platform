# Simulator Development Agent

**Specialized agent for building and modifying the building data simulator service.**

---

## Scope

**Work ONLY on:**
- `/simulator/src/` - Application code (excluding tests)
- `/simulator/config/` - Configuration files
- `/simulator/requirements.txt` - Dependencies
- `/simulator/Dockerfile` - Container build
- `/simulator/webapp/` - Simulator web interface

**DO NOT touch:**
- `/simulator/test/` - Tests (handled by Simulator Testing Agent)
- `/simulator/validation/` - Validation scripts (handled by Simulator Testing Agent)
- Other services (`/api`, `/webapp`)
- Database schema files (read-only reference)
- `docker-compose.yaml` (handled by Docker Testing Agent)

---

## Service Overview

**Haystack Building Data Simulator** - Standalone data generation service with web UI

### Core Responsibilities
1. **Data Generation**: Realistic building automation data (equipment, points, time-series)
2. **State Management**: Persist runtime state, totalizers, generation progress
3. **Gap Filling**: Detect and backfill missing time intervals
4. **Activity Logging**: Track all domain events and operations
5. **API Control**: REST API for start/stop/status/config
6. **Web Dashboard**: Real-time monitoring and control interface

### Tech Stack
- **Backend**: FastAPI (Python) on port 8080
- **Frontend**: Next.js (TypeScript) on port 3001
- **Building Data DB**: TimescaleDB (port 5432) - writes directly for now, API integration pending
- **State DB**: PostgreSQL (port 5433) - simulator operational state
- **Scheduler**: APScheduler for continuous generation

---

## Architecture

```
Simulator Service
├── Backend API (Port 8080)
│   ├── Control: start, stop, reset
│   ├── Status: state, metrics, health
│   ├── Config: get/update building config
│   └── Activity: event log with pagination
├── Frontend (Port 3001)
│   ├── Dashboard: real-time status
│   ├── Config Editor: JSON editor for building config
│   └── Activity Log: event timeline
└── Core Services
    ├── ContinuousGenerator: main orchestration
    ├── StateManager: persistence layer
    ├── GapFiller: backfill missing intervals
    ├── ActivityLogger: domain events
    └── Scheduler: APScheduler integration
```

---

## File Structure

```
simulator/
├── src/
│   ├── api/
│   │   └── simulator_api.py          # FastAPI endpoints
│   ├── service/
│   │   ├── continuous_generator.py   # Main generation service
│   │   ├── state_manager.py          # State persistence
│   │   ├── gap_filler.py             # Gap detection/filling
│   │   ├── scheduler.py              # APScheduler integration
│   │   └── activity_logger.py        # Event logging
│   ├── generators/
│   │   ├── entity_generator.py       # Equipment hierarchy
│   │   ├── time_series_generator.py  # Point values
│   │   └── weather_simulator.py      # Weather patterns
│   ├── database/
│   │   ├── db_operations.py          # DB utilities
│   │   └── config_loader.py          # Config loading
│   ├── models/
│   │   └── state_models.py           # Pydantic models
│   └── service_main.py               # Entry point
├── config/
│   ├── building_config.yaml          # Building specification
│   ├── database_config.yaml          # DB config (local)
│   └── database_config.docker.yaml   # DB config (Docker)
├── webapp/
│   ├── app/
│   │   ├── page.tsx                  # Dashboard
│   │   ├── config/page.tsx           # Config editor
│   │   └── activity/page.tsx         # Activity log
│   ├── components/ui/                # shadcn/ui components
│   ├── lib/
│   │   └── api-client.ts             # API client library
│   └── Dockerfile
├── requirements.txt                  # Python deps
└── Dockerfile                        # Backend container
```

---

## Database Knowledge

### TimescaleDB (Port 5432) - Building Data
- **Database**: `datakwip`
- **Schema**: `core`
- **Tables**: `entity`, `entity_tag`, `values_{org_key}` (hypertables)
- **Access**: Direct writes (temporary) - API integration pending

**Current Pattern:**
```python
# Direct DB writes (Phase 1)
from simulator.src.database.db_operations import DatabaseOperations

db_config = load_config_with_env('config/database_config.yaml')
db = DatabaseOperations(db_config)

# Write entities
entity_id = db.insert_entity(tags=[...])

# Write values
db.insert_values(
    entity_id=entity_id,
    timestamp=now,
    value=72.5,
    table_name=db_config['tables']['value_table']
)
```

**Future Pattern (Phase 3):**
```python
# API writes (pending implementation)
from simulator.src.service.api_client import HaystackAPIClient

api_client = HaystackAPIClient(base_url=os.getenv('API_URL'))
entity_id = api_client.create_entity(org_id=1, tags=[...])
api_client.create_values(entity_id=entity_id, values=[...])
```

### PostgreSQL (Port 5433) - Simulator State
- **Database**: `simulator_state`
- **Connection**: Environment `STATE_DB_URL`

**Tables:**

**simulator_state** - Runtime state
```sql
CREATE TABLE simulator_state (
    id SERIAL PRIMARY KEY,
    is_running BOOLEAN,
    last_run_time TIMESTAMP,
    next_run_time TIMESTAMP,
    generated_count INTEGER,
    error_count INTEGER,
    totalizers JSONB,  -- {entity_id: current_value}
    config JSONB,      -- Building config snapshot
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**simulator_activity_log** - Domain events
```sql
CREATE TABLE simulator_activity_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'started', 'stopped', 'data_generated', etc.
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Configuration Management

### building_config.yaml
```yaml
organization:
  name: "Demo Building"
  key: "demo"  # Used for value_table: values_demo

building:
  name: "Office Building A"
  area: 50000
  floors: 10

equipment:
  chillers: 2
  ahus: 4
  vavs_per_ahu: 10

weather:
  latitude: 40.7128
  longitude: -74.0060
  simulate: true

generation:
  interval_minutes: 15
  start_date: "2025-01-01T00:00:00Z"
```

### database_config.yaml (local)
```yaml
database:
  host: localhost
  port: 5432
  database: datakwip
  user: datakwip_user
  password: datakwip_password
  schema: core

state_database:
  host: localhost
  port: 5433
  database: simulator_state
  user: simulator_user
  password: simulator_password

tables:
  entity_table: entity
  entity_tag_table: entity_tag
  value_table: values_demo  # Dynamic from org.key
  current_table: values_demo_current
```

### Environment Variables
```bash
# Backend
API_URL=http://api:8000                # Future: API endpoint
STATE_DB_URL=postgresql://...           # State database
DATABASE_URL=postgresql://...           # TimescaleDB (temporary)
BUILDING_CONFIG_PATH=config/building_config.yaml
DB_CONFIG_PATH=config/database_config.docker.yaml
SERVICE_INTERVAL_MINUTES=15
HEALTH_CHECK_PORT=8080

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8080
```

---

## Core Service Implementation

### 1. ContinuousGenerator (service/continuous_generator.py)

**Main orchestration service for data generation.**

```python
class ContinuousGenerator:
    def __init__(self, db_ops, state_manager, gap_filler, activity_logger, building_config):
        self.db = db_ops
        self.state_manager = state_manager
        self.gap_filler = gap_filler
        self.activity_logger = activity_logger
        self.config = building_config

    def start(self):
        """Start continuous generation"""
        state = self.state_manager.get_state()

        if state and state.is_running:
            raise ValueError("Simulator already running")

        # Load or initialize state
        if not state:
            self._initialize_state()
            self.activity_logger.log('initialized', 'Simulator initialized')

        # Check for gaps
        gaps = self.gap_filler.detect_gaps()
        if gaps:
            self.gap_filler.fill_gaps(gaps)
            self.activity_logger.log('gaps_filled', f'Filled {len(gaps)} gaps')

        # Update state
        self.state_manager.update_state(is_running=True)
        self.activity_logger.log('started', 'Simulator started')

    def generate_interval(self):
        """Generate data for single interval"""
        state = self.state_manager.get_state()

        if not state.is_running:
            return

        # Calculate next timestamp
        next_time = state.last_run_time + timedelta(minutes=self.config['interval_minutes'])

        # Generate values for all entities
        entities = self.db.get_all_entities()
        values = []

        for entity in entities:
            value = self._generate_value_for_entity(entity, next_time, state.totalizers)
            values.append(value)

            # Update totalizer if needed
            if self._is_totalizer(entity):
                state.totalizers[entity.id] = value

        # Bulk insert
        self.db.insert_values_bulk(values, table_name=self.config['value_table'])

        # Update state
        self.state_manager.update_state(
            last_run_time=next_time,
            generated_count=state.generated_count + len(values),
            totalizers=state.totalizers
        )

        self.activity_logger.log('data_generated', f'Generated {len(values)} values at {next_time}')

    def stop(self):
        """Stop generation"""
        self.state_manager.update_state(is_running=False)
        self.activity_logger.log('stopped', 'Simulator stopped')

    def reset(self):
        """Reset all data and state"""
        self.db.reset_all_data(
            value_table=self.config['value_table'],
            current_table=self.config['current_table']
        )
        self.state_manager.reset_state()
        self.activity_logger.log('reset', 'Simulator reset - all data cleared')
```

### 2. StateManager (service/state_manager.py)

**Persistence layer for simulator state.**

```python
class StateManager:
    def __init__(self, state_db_url):
        self.engine = create_engine(state_db_url)

    def get_state(self) -> SimulatorState:
        """Get current state"""
        with self.engine.connect() as conn:
            result = conn.execute(
                "SELECT * FROM simulator_state ORDER BY id DESC LIMIT 1"
            ).fetchone()

            if not result:
                return None

            return SimulatorState(
                id=result['id'],
                is_running=result['is_running'],
                last_run_time=result['last_run_time'],
                generated_count=result['generated_count'],
                totalizers=result['totalizers'],
                config=result['config']
            )

    def update_state(self, **kwargs):
        """Update state fields"""
        state = self.get_state()

        if not state:
            # Create initial state
            self._create_state(**kwargs)
        else:
            # Update existing
            set_clause = ', '.join([f"{k} = :{k}" for k in kwargs.keys()])
            with self.engine.connect() as conn:
                conn.execute(
                    f"UPDATE simulator_state SET {set_clause}, updated_at = NOW() WHERE id = :id",
                    {'id': state.id, **kwargs}
                )
                conn.commit()

    def reset_state(self):
        """Delete all state"""
        with self.engine.connect() as conn:
            conn.execute("DELETE FROM simulator_state")
            conn.commit()
```

### 3. GapFiller (service/gap_filler.py)

**Detect and backfill missing intervals.**

```python
class GapFiller:
    def __init__(self, db_ops, state_manager, config):
        self.db = db_ops
        self.state_manager = state_manager
        self.config = config

    def detect_gaps(self) -> List[Tuple[datetime, datetime]]:
        """Find missing time intervals"""
        state = self.state_manager.get_state()

        if not state or not state.last_run_time:
            return []

        # Query for actual data timestamps
        actual_timestamps = self.db.get_distinct_timestamps(
            table_name=self.config['value_table']
        )

        # Expected timestamps based on interval
        expected = []
        current = state.last_run_time
        while current < datetime.now(timezone.utc):
            expected.append(current)
            current += timedelta(minutes=self.config['interval_minutes'])

        # Find gaps
        gaps = []
        for exp_time in expected:
            if exp_time not in actual_timestamps:
                gap_start = exp_time
                gap_end = exp_time + timedelta(minutes=self.config['interval_minutes'])
                gaps.append((gap_start, gap_end))

        return gaps

    def fill_gaps(self, gaps: List[Tuple[datetime, datetime]]):
        """Generate data for missing intervals"""
        state = self.state_manager.get_state()
        entities = self.db.get_all_entities()

        for gap_start, gap_end in gaps:
            values = []

            for entity in entities:
                value = self._generate_value_for_entity(
                    entity, gap_start, state.totalizers
                )
                values.append(value)

                if self._is_totalizer(entity):
                    state.totalizers[entity.id] = value

            self.db.insert_values_bulk(values, table_name=self.config['value_table'])

        self.state_manager.update_state(totalizers=state.totalizers)
```

### 4. ActivityLogger (service/activity_logger.py)

**Domain event logging.**

```python
class ActivityLogger:
    def __init__(self, state_db_url):
        self.engine = create_engine(state_db_url)

    def log(self, event_type: str, message: str, details: dict = None):
        """Log activity event"""
        with self.engine.connect() as conn:
            conn.execute(
                """
                INSERT INTO simulator_activity_log (timestamp, event_type, message, details)
                VALUES (:timestamp, :event_type, :message, :details)
                """,
                {
                    'timestamp': datetime.now(timezone.utc),
                    'event_type': event_type,
                    'message': message,
                    'details': json.dumps(details) if details else None
                }
            )
            conn.commit()

    def get_recent(self, limit: int = 100, event_type: str = None) -> List[dict]:
        """Get recent activity"""
        query = "SELECT * FROM simulator_activity_log"
        params = {}

        if event_type:
            query += " WHERE event_type = :event_type"
            params['event_type'] = event_type

        query += " ORDER BY timestamp DESC LIMIT :limit"
        params['limit'] = limit

        with self.engine.connect() as conn:
            results = conn.execute(query, params).fetchall()
            return [dict(row) for row in results]
```

---

## API Endpoints (src/api/simulator_api.py)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Haystack Simulator API")

# Dependency injection
generator = None  # Initialize in startup

@app.get("/api/health")
def health_check():
    """Health check"""
    return {"status": "ok"}

@app.get("/api/status")
def get_status():
    """Get simulator status"""
    state = generator.state_manager.get_state()
    return {
        "is_running": state.is_running if state else False,
        "last_run_time": state.last_run_time.isoformat() if state and state.last_run_time else None,
        "generated_count": state.generated_count if state else 0,
        "error_count": state.error_count if state else 0
    }

@app.get("/api/state")
def get_state():
    """Get detailed state"""
    state = generator.state_manager.get_state()
    if not state:
        return {"state": None}
    return state.dict()

@app.post("/api/control/start")
def start_simulator():
    """Start data generation"""
    try:
        generator.start()
        return {"status": "started"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/control/stop")
def stop_simulator():
    """Stop data generation"""
    generator.stop()
    return {"status": "stopped"}

@app.post("/api/control/reset")
def reset_simulator():
    """Reset all data and state"""
    generator.reset()
    return {"status": "reset"}

@app.get("/api/config")
def get_config():
    """Get building configuration"""
    state = generator.state_manager.get_state()
    return state.config if state else generator.config

@app.put("/api/config")
def update_config(config: dict):
    """Update building configuration"""
    generator.state_manager.update_state(config=config)
    return {"status": "updated"}

@app.get("/api/activity")
def get_activity(limit: int = 100, event_type: str = None):
    """Get activity log"""
    return generator.activity_logger.get_recent(limit, event_type)
```

---

## Web Dashboard (webapp/)

### Dashboard (app/page.tsx)

```typescript
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { simulatorApi } from '@/lib/api-client';

export default function Dashboard() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      const data = await simulatorApi.getStatus();
      setStatus(data);
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Poll every 5s

    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    await simulatorApi.start();
    setLoading(false);
  };

  const handleStop = async () => {
    setLoading(true);
    await simulatorApi.stop();
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Simulator Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {status?.is_running ? '🟢 Running' : '🔴 Stopped'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Generated Points</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{status?.generated_count || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Last Run</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{status?.last_run_time || 'Never'}</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-x-4">
        <Button onClick={handleStart} disabled={loading || status?.is_running}>
          Start
        </Button>
        <Button onClick={handleStop} disabled={loading || !status?.is_running} variant="destructive">
          Stop
        </Button>
      </div>
    </div>
  );
}
```

### API Client (lib/api-client.ts)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export const simulatorApi = {
  async getStatus() {
    const res = await fetch(`${API_URL}/api/status`);
    return res.json();
  },

  async getState() {
    const res = await fetch(`${API_URL}/api/state`);
    return res.json();
  },

  async start() {
    const res = await fetch(`${API_URL}/api/control/start`, { method: 'POST' });
    return res.json();
  },

  async stop() {
    const res = await fetch(`${API_URL}/api/control/stop`, { method: 'POST' });
    return res.json();
  },

  async reset() {
    const res = await fetch(`${API_URL}/api/control/reset`, { method: 'POST' });
    return res.json();
  },

  async getActivity(limit = 100) {
    const res = await fetch(`${API_URL}/api/activity?limit=${limit}`);
    return res.json();
  },

  async getConfig() {
    const res = await fetch(`${API_URL}/api/config`);
    return res.json();
  },

  async updateConfig(config: any) {
    const res = await fetch(`${API_URL}/api/config`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return res.json();
  }
};
```

---

## Critical Design Principles

### 1. Data Coherency
**Every execution must produce coherent dataset:**
- Equipment relationships valid (VAVs → AHUs → Chillers → Site)
- Time-series corresponds to existing entities
- No orphaned or duplicate entities
- Totalizers monotonically increase

### 2. Timezone Handling
```python
# ❌ NEVER mix naive and aware datetimes
now = datetime.now()  # Naive

# ✅ ALWAYS use UTC timezone-aware
from datetime import timezone
now = datetime.now(timezone.utc)

# When reading from PostgreSQL (returns aware)
ts = row['timestamp']
ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
```

### 3. Configuration-Driven
**Never hardcode table names or values:**
```python
# ❌ BAD
value_table = "values_demo"

# ✅ GOOD
db_config = load_config_with_env('config/database_config.yaml')
value_table = db_config['tables']['value_table']
```

### 4. State Persistence
- State survives restarts
- Totalizers preserved across runs
- Gap detection on resume
- Activity log for audit trail

---

## Local Development

```bash
# Start databases
docker-compose up timescaledb statedb

# Backend
cd simulator
pip install -r requirements.txt
python src/service_main.py

# Frontend (separate terminal)
cd simulator/webapp
npm install
npm run dev

# Access:
# - Backend API: http://localhost:8080/docs
# - Frontend: http://localhost:3001
```

---

## Troubleshooting

### Simulator won't start
1. Check databases: `docker-compose up timescaledb statedb`
2. Verify config files exist: `config/building_config.yaml`, `config/database_config.yaml`
3. Check STATE_DB_URL environment variable
4. View logs: `docker-compose logs simulator`

### Frontend can't connect
1. Verify `NEXT_PUBLIC_API_URL=http://localhost:8080`
2. Check CORS in `simulator_api.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"]
)
```

### Gaps not filling
1. Check timezone handling (UTC vs naive)
2. Verify interval calculation
3. Check state persistence
4. Run: `python validation/validate_gaps.py`

---

## Handoff Points

**To Simulator Testing Agent:**
- New feature complete → request test coverage
- Bug fix → add regression test
- State management changes → update validation scripts

**To API Development Agent (Future Phase 3):**
- When switching from direct DB writes to API calls
- When simulator control endpoints needed in main API

**To Haystack Database Agent:**
- Schema changes needed
- Query optimization
- Hypertable configuration

---

## Related Documentation

- [Simulator README](../simulator/README.md)
- [Parent CLAUDE.md](../CLAUDE.md)
- [Critical Design Decisions](../knowledge/CRITICAL_DESIGN_DECISIONS.md)

---

## Agent Boundaries

**✅ CAN:**
- Modify simulator application code
- Update configuration files
- Build web dashboard features
- Add API endpoints
- Implement data generators
- Request tests from Simulator Testing Agent

**❌ CANNOT:**
- Write tests (Simulator Testing Agent)
- Modify API service
- Modify webapp service
- Change database schema (Haystack Database Agent)
- Run docker-compose (Docker Testing Agent)
