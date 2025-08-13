# MCP Server Implementation Guide for Haystack Data Simulator

## Overview
This document provides all implementation details needed to build an MCP (Model Context Protocol) server for the Haystack building data simulator database. The simulator generates Project Haystack compliant building automation data stored in PostgreSQL/TimescaleDB.

---

## Database Architecture

### Connection Details
- **Database**: PostgreSQL with TimescaleDB extension
- **Configuration**: Located in `config/database_config.yaml`
- **Connection Class**: `src/database/connection.py` - `DatabaseConnection`
- **Schema**: Primarily uses `core` schema

### Core Tables

#### Entity Management
- **`core.entity`**: Main entity table
  - `id` (primary key): Auto-incrementing entity ID
  - `value_table_id`: Links to value table (e.g., "demo")
  
- **`core.entity_tag`**: Entity tags (Haystack tag-value pairs)
  - `entity_id`: References `core.entity.id`
  - `tag_id`: References `core.tag_def.id`
  - `value_n`: Numeric value
  - `value_b`: Boolean value
  - `value_s`: String value
  - Additional value columns for different types

- **`core.tag_def`**: Tag definitions
  - `id`: Tag definition ID
  - `name`: Tag name (e.g., 'temp', 'chiller', 'point')

#### Time-Series Data
- **`core.values_demo`**: Historical time-series data (TimescaleDB hypertable)
  - `entity_id`: References entity
  - `ts`: Timestamp (partition key)
  - `value_n`: Numeric value
  - `value_b`: Boolean value
  - `value_s`: String value
  - `status`: Data quality status

- **`core.values_demo_current`**: Current/latest values (TimescaleDB hypertable)
  - Same structure as `values_demo`
  - Contains most recent value for each entity

#### Organization Management
- **`core.org`**: Organizations
  - `id`: Organization ID
  - `name`: Organization name
  - `key`: Organization key (e.g., "demo")

---

## Entity Hierarchy and Relationships

### Building Structure
```
Site (1)
├── Chillers (2) - Primary/Backup
├── AHUs (4) - Air Handling Units (serve specific floors)
│   └── VAV Boxes (48) - Variable Air Volume boxes
│       └── Points (sensors/actuators per VAV)
├── Meters (3) - Electric, Gas, Water
└── Equipment Points - Sensors and actuators for each equipment piece
```

### Entity Counts (Typical Generation)
- **Total Entities**: ~351
- **Site**: 1
- **Equipment**: ~58 (chillers, AHUs, VAVs, meters)
- **Points**: ~292 (sensors, actuators, setpoints)

### Key Relationships
- **Site Reference**: All equipment has `siteRef` tag pointing to site entity
- **Equipment Reference**: All points have `equipRef` tag pointing to parent equipment
- **AHU-VAV Relationship**: VAV boxes have `ahuRef` tag pointing to controlling AHU
- **Floor Assignment**: AHUs serve specific floor ranges, VAVs inherit floor assignments

---

## Data Generation Patterns

### Time-Series Data Characteristics
- **Historical Range**: 30 days by default (configurable with `--days` flag)
- **Data Frequency**: Approximately every 15 minutes per point
- **Total Records**: ~768K for 30 days across all points
- **Current Values**: 271 entities with latest readings

### Realistic Data Values
- **Zone Temperatures**: 65-78°F normal range, seasonal variation
- **Supply Temperatures**: 55-65°F for cooling, 80-120°F for heating
- **Damper Positions**: 0-100% based on zone demand
- **Flow Rates**: Variable based on occupancy and weather
- **Energy Consumption**: Correlated with weather and occupancy patterns

### Weather Integration
- **Seasonal Patterns**: Affects equipment load and energy consumption
- **Dry Bulb Temperature**: Drives chiller operation and AHU supply temps
- **Weather Simulator**: `src/generators/weather.py`

### Occupancy Integration
- **Schedule-Based**: Business hours vs. after-hours operation
- **Zone Impact**: Affects temperature setpoints and VAV airflow
- **Schedule Generator**: `src/generators/schedules.py`

---

## Critical Implementation Tags

### Equipment Tags
- **`site`**: Marks site entities
- **`equip`**: Marks equipment entities
- **`chiller`**: Chiller equipment
- **`ahu`**: Air handling unit
- **`vav`**: Variable air volume box
- **`meter`**: Utility meters

### Point Tags
- **`point`**: Marks point entities
- **`sensor`**: Input points (temperatures, flows, etc.)
- **`cmd`**: Command/output points (damper positions, valve positions)
- **`sp`**: Setpoint values
- **`temp`**: Temperature points (most common measurement)
- **`flow`**: Airflow measurements
- **`status`**: Equipment status (on/off, fault states)

### Functional Tags
- **`zone`**: Zone assignment for VAV boxes and temperature points
- **`floor`**: Floor assignment
- **`cooling`**: Cooling-related equipment/points
- **`heating`**: Heating-related equipment/points
- **`discharge`**: Discharge air measurements
- **`return`**: Return air measurements

---

## Database Queries for MCP Server

### Essential Queries

#### Get All Sites
```sql
SELECT e.id, et_name.value_s as name, et_area.value_n as area
FROM core.entity e
JOIN core.entity_tag et_site ON e.id = et_site.entity_id
JOIN core.tag_def td_site ON et_site.tag_id = td_site.id
LEFT JOIN core.entity_tag et_name ON e.id = et_name.entity_id
LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
LEFT JOIN core.entity_tag et_area ON e.id = et_area.entity_id
LEFT JOIN core.tag_def td_area ON et_area.tag_id = td_area.id AND td_area.name = 'area'
WHERE td_site.name = 'site';
```

#### Get Equipment by Type
```sql
SELECT e.id, et_dis.value_s as display_name
FROM core.entity e
JOIN core.entity_tag et_equip ON e.id = et_equip.entity_id
JOIN core.tag_def td_equip ON et_equip.tag_id = td_equip.id AND td_equip.name = 'equip'
JOIN core.entity_tag et_type ON e.id = et_type.entity_id
JOIN core.tag_def td_type ON et_type.tag_id = td_type.id AND td_type.name = ?
LEFT JOIN core.entity_tag et_dis ON e.id = et_dis.entity_id
LEFT JOIN core.tag_def td_dis ON et_dis.tag_id = td_dis.id AND td_dis.name = 'dis'
```

#### Get Points for Equipment
```sql
SELECT e.id, et_dis.value_s as display_name, et_kind.value_s as kind
FROM core.entity e
JOIN core.entity_tag et_point ON e.id = et_point.entity_id
JOIN core.tag_def td_point ON et_point.tag_id = td_point.id AND td_point.name = 'point'
JOIN core.entity_tag et_equipref ON e.id = et_equipref.entity_id
JOIN core.tag_def td_equipref ON et_equipref.tag_id = td_equipref.id AND td_equipref.name = 'equipRef'
LEFT JOIN core.entity_tag et_dis ON e.id = et_dis.entity_id
LEFT JOIN core.tag_def td_dis ON et_dis.tag_id = td_dis.id AND td_dis.name = 'dis'
LEFT JOIN core.entity_tag et_kind ON e.id = et_kind.entity_id
LEFT JOIN core.tag_def td_kind ON et_kind.tag_id = td_kind.id AND td_kind.name = 'kind'
WHERE et_equipref.value_s = ?
```

#### Get Time-Series Data
```sql
SELECT ts, value_n, value_b, value_s, status
FROM core.values_demo
WHERE entity_id = ? 
AND ts BETWEEN ? AND ?
ORDER BY ts;
```

#### Get Current Values
```sql
SELECT v.entity_id, v.ts, v.value_n, v.value_b, v.value_s, et_dis.value_s as display_name
FROM core.values_demo_current v
LEFT JOIN core.entity_tag et_dis ON v.entity_id = et_dis.entity_id
LEFT JOIN core.tag_def td_dis ON et_dis.tag_id = td_dis.id AND td_dis.name = 'dis'
WHERE v.entity_id IN (?)
```

### Performance Considerations
- **Indexes**: Entity relationships are heavily indexed
- **TimescaleDB**: Time-series tables are partitioned by timestamp
- **Connection Pooling**: Use `DatabaseConnection` class for proper connection management

---

## Configuration Files

### Database Configuration (`config/database_config.yaml`)
```yaml
database:
  host: "localhost"
  port: 5432
  database: "your_db"
  user: "username"
  password: "password"

organization:
  name: "Demo Organization"
  key: "demo"

tables:
  value_table: "values_demo"
  current_table: "values_demo_current"
```

### Building Configuration (`config/building_config.yaml`)
- Defines equipment counts, capacities, and characteristics
- Weather simulation parameters
- Occupancy schedules
- Point generation rules

---

## MCP Server Capabilities Recommendations

### Essential Tools
1. **`get_sites`**: List all building sites
2. **`get_equipment`**: Get equipment by type (chiller, ahu, vav, etc.)
3. **`get_points`**: Get points for specific equipment
4. **`get_entity_tags`**: Get all tags for an entity
5. **`get_time_series`**: Get historical data for points
6. **`get_current_values`**: Get latest values for points
7. **`search_entities`**: Search by tag patterns or names

### Advanced Tools
1. **`get_energy_consumption`**: Aggregate meter data
2. **`get_temperature_summary`**: Zone temperature statistics
3. **`get_equipment_status`**: Equipment operational status
4. **`get_alarms`**: Identify out-of-range conditions
5. **`get_floor_summary`**: Floor-level aggregations

### Resources
1. **Building hierarchy explorer**
2. **Time-series data browser**
3. **Equipment relationship mapper**
4. **Tag documentation**

---

## Data Validation Utilities

### Standalone Validation
- Use `validate_data.py` for database health checks
- Provides entity counts, time ranges, and sample data validation
- Run independently: `python validate_data.py`

### Key Metrics to Expose
- **Entity Counts**: By type (sites, equipment, points)
- **Time Ranges**: Historical data coverage
- **Data Quality**: Missing values, out-of-range readings
- **Relationship Integrity**: Orphaned points, broken references

---

## Common Pitfalls and Solutions

### SQL Query Issues
- **Ambiguous Columns**: Always qualify column names with table aliases
- **Tag Joins**: Entity-tag relationships require multiple joins
- **Time Zones**: TimescaleDB stores timestamps in UTC

### Performance Issues
- **Large Time Ranges**: Limit time-series queries to reasonable ranges
- **Entity Traversal**: Use specific equipment/point filters rather than scanning all entities
- **Connection Management**: Properly close database connections

### Data Coherency
- **Reset Requirement**: Use `--reset` flag for coherent datasets
- **Entity Relationships**: Validate equipRef and siteRef integrity
- **Current vs Historical**: Distinguish between current values and time-series data

---

## Example MCP Tool Implementation

```python
@server.tool()
async def get_zone_temperatures(site_id: str, floor: Optional[int] = None) -> dict:
    """Get current zone temperatures for a site."""
    
    query = """
        SELECT e.id, et_dis.value_s as name, v.value_n as temperature, et_floor.value_n as floor
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id AND td_point.name = 'point'
        JOIN core.entity_tag et_temp ON e.id = et_temp.entity_id  
        JOIN core.tag_def td_temp ON et_temp.tag_id = td_temp.id AND td_temp.name = 'temp'
        JOIN core.entity_tag et_siteref ON e.id = et_siteref.entity_id
        JOIN core.tag_def td_siteref ON et_siteref.tag_id = td_siteref.id AND td_siteref.name = 'siteRef'
        JOIN core.values_demo_current v ON e.id = v.entity_id
        LEFT JOIN core.entity_tag et_dis ON e.id = et_dis.entity_id
        LEFT JOIN core.tag_def td_dis ON et_dis.tag_id = td_dis.id AND td_dis.name = 'dis'
        LEFT JOIN core.entity_tag et_floor ON e.id = et_floor.entity_id
        LEFT JOIN core.tag_def td_floor ON et_floor.tag_id = td_floor.id AND td_floor.name = 'floor'
        WHERE et_siteref.value_s = %s
    """
    
    params = [site_id]
    if floor:
        query += " AND et_floor.value_n = %s"
        params.append(floor)
        
    # Execute query and return results
    # ... implementation details
```

This comprehensive guide should provide everything needed to build a robust MCP server for the Haystack building data simulator.