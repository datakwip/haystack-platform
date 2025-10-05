# Haystack Database Agent

**Specialized agent for database schema, Haystack data model, and TimescaleDB/PostgreSQL optimization.**

---

## Scope

**Work ONLY on:**
- `/schema/*.sql` - Database schema definitions
- Database migrations and schema changes
- Query optimization
- Hypertable configuration
- Index management
- Database documentation

**READ for reference:**
- Service code that uses database (API, Simulator)
- Data model documentation
- Haystack v3 specification

**DO NOT modify:**
- Service application code (Development Agents)
- Docker orchestration (Docker Testing Agent)
- Test files (Testing Agents)

---

## Agent Overview

**Goal**: Maintain robust, performant, and Haystack-compliant database schema for building automation data.

### Responsibilities
1. **Schema Management**: Design and maintain database schema
2. **Haystack Compliance**: Ensure adherence to Project Haystack v3 specification
3. **Query Optimization**: Optimize database queries for performance
4. **Hypertable Management**: Configure TimescaleDB hypertables for time-series data
5. **Index Strategy**: Design and maintain indexes
6. **Data Integrity**: Enforce constraints and relationships
7. **Migration Scripts**: Create safe migration paths for schema changes

---

## Database Architecture

### Two-Database Design

**Why Two Databases?**
Clean separation between user-facing building data and simulator operational state.

```
TimescaleDB (Port 5432)           PostgreSQL (Port 5433)
├── Building Data                 ├── Simulator State
│   ├── Entities (equipment)      │   ├── Runtime state
│   ├── Tags (metadata)           │   ├── Totalizers
│   ├── Time-series values        │   └── Config snapshots
│   └── Organizations             └── Activity Log
│                                     └── Domain events
└── Schema: core
```

---

## TimescaleDB Schema (Port 5432)

### Database: `datakwip`
### Schema: `core`

### Core Tables

#### 1. entity
**Building equipment, spaces, points**

```sql
CREATE TABLE core.entity (
    id SERIAL PRIMARY KEY,
    value_table_id VARCHAR,              -- Reference to value table
    disabled_ts TIMESTAMP                -- Soft delete timestamp
);

CREATE INDEX ix_core_entity_id ON core.entity (id);
```

**Usage:**
- Represents any "thing" in building automation
- Equipment: AHU, VAV, Chiller, Meter
- Spaces: Floor, Room, Zone
- Points: Temperature sensor, Setpoint, Command

#### 2. entity_tag
**Haystack tag assignments**

```sql
CREATE TABLE core.entity_tag (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES core.entity(id),
    tag_id INTEGER REFERENCES core.tag_def(id),

    -- Value storage by type
    value_n NUMERIC,                     -- Number
    value_b BOOLEAN,                     -- Boolean (marker)
    value_s VARCHAR,                     -- String
    value_ts TIMESTAMP,                  -- Timestamp
    value_list VARCHAR[],                -- List
    value_dict JSONB,                    -- Dict/Grid
    value_ref INTEGER,                   -- Ref (entity ID)
    value_enum INTEGER,                  -- Enum value

    disabled_ts TIMESTAMP,               -- Soft delete

    UNIQUE (entity_id, tag_id, disabled_ts)
);

CREATE INDEX ix_core_entity_tag_entity_id ON core.entity_tag (entity_id);
CREATE INDEX ix_core_entity_tag_tag_id ON core.entity_tag (tag_id);
```

**Haystack Value Types:**
- **Marker**: value_b = true (presence of tag)
- **Number**: value_n = 72.5
- **String**: value_s = "Building A"
- **Ref**: value_ref = 123 (references another entity.id)
- **Timestamp**: value_ts = '2025-01-04 12:00:00'
- **List**: value_list = ['a', 'b', 'c']
- **Dict**: value_dict = {"key": "value"}

#### 3. tag_def
**Tag definitions (Haystack vocabulary)**

```sql
CREATE TABLE core.tag_def (
    id VARCHAR PRIMARY KEY,              -- e.g., 'site', 'equip', 'temp'
    name VARCHAR UNIQUE,
    type VARCHAR,                        -- 'Marker', 'Number', 'Str', 'Ref', etc.
    unit VARCHAR,                        -- e.g., '°F', 'kW', 'cfm'
    description TEXT,
    category VARCHAR,                    -- 'entity', 'point', 'marker', etc.
    disabled_ts TIMESTAMP
);

CREATE INDEX ix_core_tag_def_name ON core.tag_def (name);
CREATE INDEX ix_core_tag_def_type ON core.tag_def (type);
```

**Standard Haystack Tags:**
- Entity tags: `site`, `equip`, `space`, `point`
- Equipment: `ahu`, `vav`, `chiller`, `boiler`
- Point: `sensor`, `cmd`, `sp` (setpoint)
- Measurement: `temp`, `pressure`, `flow`, `energy`
- Metadata: `dis` (display name), `navName`, `geoAddr`

#### 4. values_{org_key} (Hypertables)
**Time-series data - org-specific**

```sql
-- Example: values_demo
CREATE TABLE core.values_demo (
    entity_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC,
    org_id INTEGER NOT NULL,

    PRIMARY KEY (entity_id, timestamp)
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable(
    'core.values_demo',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_values_demo_entity_time ON core.values_demo (entity_id, timestamp DESC);
CREATE INDEX idx_values_demo_org ON core.values_demo (org_id);
```

**Hypertable Benefits:**
- Automatic partitioning by time
- Optimized time-series queries
- Compression for old data
- Continuous aggregates for rollups

#### 5. org
**Organizations (multi-tenancy)**

```sql
CREATE TABLE core.org (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    key VARCHAR UNIQUE NOT NULL,         -- URL-safe key: 'acme', 'demo'
    value_table VARCHAR,                 -- 'values_demo'
    current_table VARCHAR,               -- 'values_demo_current'
    disabled_ts TIMESTAMP
);

CREATE INDEX ix_core_org_key ON core.org (key);
```

**Dynamic Table Naming:**
Each org gets its own value tables based on `org.key`:
- `values_{org.key}` - All historical values
- `values_{org.key}_current` - Latest values only

#### 6. user
**Users for authentication**

```sql
CREATE TABLE core."user" (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    disabled_ts TIMESTAMP
);

CREATE INDEX ix_core_user_email ON core."user" (email);
```

#### 7. org_user
**User-organization membership**

```sql
CREATE TABLE core.org_user (
    id SERIAL PRIMARY KEY,
    org_id INTEGER REFERENCES core.org(id),
    user_id INTEGER REFERENCES core."user"(id),

    UNIQUE (org_id, user_id)
);
```

---

## PostgreSQL State Schema (Port 5433)

### Database: `simulator_state`

#### 1. simulator_state
**Runtime state and totalizers**

```sql
CREATE TABLE simulator_state (
    id SERIAL PRIMARY KEY,
    is_running BOOLEAN NOT NULL DEFAULT FALSE,
    last_run_time TIMESTAMPTZ,
    next_run_time TIMESTAMPTZ,
    generated_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Totalizers: {entity_id: current_value}
    totalizers JSONB,

    -- Config snapshot
    config JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_simulator_state_is_running ON simulator_state (is_running);
CREATE INDEX idx_simulator_state_updated ON simulator_state (updated_at DESC);
```

**Totalizer Storage:**
```json
{
  "123": 15234.5,  // entity_id 123 = 15234.5 kWh
  "456": 8921.2    // entity_id 456 = 8921.2 gal
}
```

#### 2. simulator_activity_log
**Domain event logging**

```sql
CREATE TABLE simulator_activity_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,     -- 'started', 'stopped', 'data_generated', etc.
    message TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_activity_log_timestamp ON simulator_activity_log (timestamp DESC);
CREATE INDEX idx_activity_log_event_type ON simulator_activity_log (event_type);
```

**Event Types:**
- `initialized` - Simulator initialized
- `started` - Generation started
- `stopped` - Generation stopped
- `data_generated` - Data points created
- `gaps_filled` - Missing intervals backfilled
- `error` - Error occurred
- `reset` - All data cleared

---

## Haystack v3 Data Model

### Entity-Attribute-Value (EAV) Pattern

**Haystack uses flexible tag-based schema:**

```
Entity (Site)
├── Tag: site (Marker)
├── Tag: dis (Str) = "Building A"
├── Tag: area (Number) = 50000 ft²
└── Tag: geoAddr (Str) = "123 Main St"

Entity (AHU)
├── Tag: equip (Marker)
├── Tag: ahu (Marker)
├── Tag: siteRef (Ref) → Site entity ID
└── Tag: dis (Str) = "AHU-1"

Entity (Temp Point)
├── Tag: point (Marker)
├── Tag: sensor (Marker)
├── Tag: temp (Marker)
├── Tag: equipRef (Ref) → AHU entity ID
└── Tag: unit (Str) = "°F"
```

### Reference Relationships

**equipRef**: Equipment hierarchy
```
Site
└── equipRef → AHU
    └── equipRef → VAV
        └── equipRef → Temp Sensor (point)
```

**siteRef**: Site association
```
All equipment → siteRef → Site entity
```

### Tag Types and Storage

| Haystack Type | PostgreSQL Column | Example |
|---------------|-------------------|---------|
| Marker | value_b = true | `site`, `equip`, `point` |
| Bool | value_b | `occupied = true` |
| Number | value_n | `temp = 72.5` |
| Str | value_s | `dis = "AHU-1"` |
| Ref | value_ref | `equipRef = 123` |
| Date/Time | value_ts | `installed = 2020-01-15` |
| List | value_list | `tags = ['a', 'b']` |
| Dict/Grid | value_dict | `meta = {"key": "val"}` |

---

## Query Patterns

### 1. Get All Entities with Specific Tags

```sql
-- Find all AHUs
SELECT DISTINCT e.id, e.*
FROM core.entity e
JOIN core.entity_tag et1 ON e.id = et1.entity_id
JOIN core.entity_tag et2 ON e.id = et2.entity_id
WHERE et1.tag_id = 'equip' AND et1.value_b = true
  AND et2.tag_id = 'ahu' AND et2.value_b = true
  AND et1.disabled_ts IS NULL
  AND et2.disabled_ts IS NULL;
```

### 2. Get Entity with All Tags (Haystack Export)

```sql
-- Get entity as Haystack dict
SELECT
    e.id,
    jsonb_object_agg(
        td.name,
        CASE
            WHEN et.value_b IS NOT NULL THEN to_jsonb(et.value_b)
            WHEN et.value_n IS NOT NULL THEN to_jsonb(et.value_n)
            WHEN et.value_s IS NOT NULL THEN to_jsonb(et.value_s)
            WHEN et.value_ref IS NOT NULL THEN to_jsonb(et.value_ref)
            ELSE NULL
        END
    ) as tags
FROM core.entity e
JOIN core.entity_tag et ON e.id = et.entity_id
JOIN core.tag_def td ON et.tag_id = td.id
WHERE e.id = 123
  AND et.disabled_ts IS NULL
GROUP BY e.id;
```

### 3. Time-Series Query (Recent Values)

```sql
-- Get last 24 hours of values for entity
SELECT entity_id, timestamp, value
FROM core.values_demo
WHERE entity_id = 123
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```

### 4. Time-Series Aggregation (Hourly Rollup)

```sql
-- Average values per hour
SELECT
    entity_id,
    time_bucket('1 hour', timestamp) as hour,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value
FROM core.values_demo
WHERE entity_id = 123
  AND timestamp >= NOW() - INTERVAL '7 days'
GROUP BY entity_id, hour
ORDER BY hour DESC;
```

### 5. Equipment Hierarchy Query

```sql
-- Get all VAVs for a specific AHU
WITH ahu AS (
    SELECT id FROM core.entity WHERE id = 100
)
SELECT v.id, v.*
FROM core.entity v
JOIN core.entity_tag et ON v.id = et.entity_id
WHERE et.tag_id = 'equipRef'
  AND et.value_ref = (SELECT id FROM ahu)
  AND et.disabled_ts IS NULL;
```

---

## Indexing Strategy

### Primary Indexes (Already Created)

```sql
-- Entity lookups
CREATE INDEX ix_core_entity_id ON core.entity (id);

-- Tag lookups
CREATE INDEX ix_core_entity_tag_entity_id ON core.entity_tag (entity_id);
CREATE INDEX ix_core_entity_tag_tag_id ON core.entity_tag (tag_id);

-- Time-series queries
CREATE INDEX idx_values_demo_entity_time ON core.values_demo (entity_id, timestamp DESC);
```

### Additional Recommended Indexes

```sql
-- equipRef queries (hierarchy traversal)
CREATE INDEX idx_entity_tag_equipref ON core.entity_tag (value_ref)
WHERE tag_id = 'equipRef' AND disabled_ts IS NULL;

-- Tag type filtering
CREATE INDEX idx_tag_def_type ON core.tag_def (type);

-- Org-specific queries
CREATE INDEX idx_values_demo_org_time ON core.values_demo (org_id, timestamp DESC);

-- Activity log filtering
CREATE INDEX idx_activity_log_event_time ON simulator_activity_log (event_type, timestamp DESC);
```

---

## Performance Optimization

### 1. Hypertable Configuration

```sql
-- Compression for old data (after 30 days)
ALTER TABLE core.values_demo SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'entity_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('core.values_demo', INTERVAL '30 days');

-- Retention policy (drop data older than 1 year)
SELECT add_retention_policy('core.values_demo', INTERVAL '1 year');
```

### 2. Continuous Aggregates (Pre-computed Rollups)

```sql
-- Hourly averages (materialized view)
CREATE MATERIALIZED VIEW core.values_demo_hourly
WITH (timescaledb.continuous) AS
SELECT
    entity_id,
    time_bucket('1 hour', timestamp) as hour,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as sample_count
FROM core.values_demo
GROUP BY entity_id, hour;

-- Refresh policy
SELECT add_continuous_aggregate_policy('core.values_demo_hourly',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);
```

### 3. Partitioning Strategy

```sql
-- Hypertable automatically partitions by time
-- Default chunk interval: 7 days

-- Adjust chunk interval for different workloads
SELECT set_chunk_time_interval('core.values_demo', INTERVAL '1 day');  -- High frequency
SELECT set_chunk_time_interval('core.values_demo', INTERVAL '30 days'); -- Low frequency
```

---

## Schema Migrations

### Migration Script Template

```sql
-- migrations/001_add_totalizer_tag.sql

BEGIN;

-- 1. Add new tag definition
INSERT INTO core.tag_def (id, name, type, description)
VALUES ('totalizer', 'totalizer', 'Marker', 'Point that accumulates values (energy, water, etc.)')
ON CONFLICT (id) DO NOTHING;

-- 2. Update existing entities (example)
-- Mark energy points as totalizers
UPDATE core.entity_tag et
SET tag_id = 'totalizer', value_b = true
FROM core.entity_tag et2
WHERE et.entity_id = et2.entity_id
  AND et2.tag_id = 'energy'
  AND et2.value_b = true
  AND NOT EXISTS (
    SELECT 1 FROM core.entity_tag
    WHERE entity_id = et.entity_id AND tag_id = 'totalizer'
  );

-- 3. Verify migration
DO $$
DECLARE
    totalizer_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO totalizer_count
    FROM core.entity_tag
    WHERE tag_id = 'totalizer' AND value_b = true;

    RAISE NOTICE 'Totalizer entities: %', totalizer_count;
END $$;

COMMIT;
```

### Safe Migration Process

1. **Backup**: Always backup before migration
2. **Test**: Run on test database first
3. **Transaction**: Wrap in BEGIN/COMMIT
4. **Validation**: Verify results before commit
5. **Rollback Plan**: Have rollback script ready

---

## Database Initialization

### Schema Load Order

```bash
#!/bin/bash
# scripts/init_db.sh

# 1. TimescaleDB - Core schema
docker exec haystack-timescaledb psql -U datakwip_user -d datakwip -f /docker-entrypoint-initdb.d/01_schema.sql

# 2. State DB - Simulator schema
docker exec haystack-statedb psql -U simulator_user -d simulator_state -f /docker-entrypoint-initdb.d/01_state.sql
docker exec haystack-statedb psql -U simulator_user -d simulator_state -f /docker-entrypoint-initdb.d/02_activity.sql

# 3. Seed data (optional)
docker exec haystack-timescaledb psql -U datakwip_user -d datakwip -f /seeds/tag_definitions.sql
```

### Seed Tag Definitions

```sql
-- seeds/tag_definitions.sql

INSERT INTO core.tag_def (id, name, type, category, description) VALUES
-- Entity tags
('site', 'site', 'Marker', 'entity', 'Building or facility'),
('equip', 'equip', 'Marker', 'entity', 'Equipment asset'),
('space', 'space', 'Marker', 'entity', 'Room or zone'),
('point', 'point', 'Marker', 'entity', 'Data point'),

-- Equipment types
('ahu', 'ahu', 'Marker', 'equip', 'Air Handler Unit'),
('vav', 'vav', 'Marker', 'equip', 'Variable Air Volume Box'),
('chiller', 'chiller', 'Marker', 'equip', 'Chiller'),
('boiler', 'boiler', 'Marker', 'equip', 'Boiler'),

-- Point types
('sensor', 'sensor', 'Marker', 'point', 'Sensor point'),
('cmd', 'cmd', 'Marker', 'point', 'Command point'),
('sp', 'sp', 'Marker', 'point', 'Setpoint'),

-- Measurements
('temp', 'temp', 'Marker', 'point', 'Temperature'),
('pressure', 'pressure', 'Marker', 'point', 'Pressure'),
('flow', 'flow', 'Marker', 'point', 'Flow rate'),
('energy', 'energy', 'Marker', 'point', 'Energy consumption'),

-- Metadata
('dis', 'dis', 'Str', 'meta', 'Display name'),
('unit', 'unit', 'Str', 'meta', 'Unit of measurement'),
('equipRef', 'equipRef', 'Ref', 'ref', 'Reference to parent equipment'),
('siteRef', 'siteRef', 'Ref', 'ref', 'Reference to site')

ON CONFLICT (id) DO NOTHING;
```

---

## Troubleshooting

### Schema Issues

```sql
-- List all schemas
SELECT schema_name FROM information_schema.schemata;

-- List tables in core schema
\dt core.*

-- Check table structure
\d core.entity
\d core.entity_tag
```

### Missing Hypertables

```sql
-- Check if table is a hypertable
SELECT * FROM timescaledb_information.hypertables
WHERE hypertable_name = 'values_demo';

-- Convert to hypertable (if missing)
SELECT create_hypertable(
    'core.values_demo',
    'timestamp',
    if_not_exists => TRUE
);
```

### Index Analysis

```sql
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'core'
ORDER BY idx_scan DESC;

-- Find missing indexes (slow queries)
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan as avg_seq_read
FROM pg_stat_user_tables
WHERE schemaname = 'core'
  AND seq_scan > 0
ORDER BY seq_tup_read DESC;
```

---

## Handoff Points

**To Development Agents:**
- When schema changes are needed
- When new indexes are required
- When query optimization is needed

**To Testing Agents:**
- When test data is needed
- When validation queries are required

**To Docker Testing Agent:**
- When database initialization scripts change
- When migration testing is needed

---

## Related Documentation

- [Project Haystack v3 Specification](https://project-haystack.org/doc/docHaystack/Index)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Schema Files](../schema/)

---

## Agent Boundaries

**✅ CAN:**
- Modify database schema files
- Create migration scripts
- Optimize queries and indexes
- Configure hypertables
- Design new tables
- Write seed data scripts
- Provide query optimization guidance

**❌ CANNOT:**
- Modify service application code (Development Agents)
- Write service tests (Testing Agents)
- Run docker-compose (Docker Testing Agent)
- Deploy migrations without review

---

## Quick Reference

### Create New Value Table
```sql
-- For new organization
CREATE TABLE core.values_acme (
    entity_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC,
    org_id INTEGER NOT NULL,
    PRIMARY KEY (entity_id, timestamp)
);

SELECT create_hypertable('core.values_acme', 'timestamp', if_not_exists => TRUE);
CREATE INDEX idx_values_acme_entity_time ON core.values_acme (entity_id, timestamp DESC);
```

### Query Entity with Tags
```sql
SELECT e.id,
       jsonb_object_agg(td.name, COALESCE(et.value_n::text, et.value_s, et.value_b::text)) as tags
FROM core.entity e
JOIN core.entity_tag et ON e.id = et.entity_id
JOIN core.tag_def td ON et.tag_id = td.id
WHERE e.id = ?
GROUP BY e.id;
```

### Time-Series Recent Values
```sql
SELECT * FROM core.values_demo
WHERE entity_id = ?
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
```
