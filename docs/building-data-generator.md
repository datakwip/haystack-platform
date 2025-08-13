# Building Data Generator - Claude Code Instructions

## Project Overview
Create a realistic building data generation application that populates a local TimescaleDB instance with authentic Project Haystack-compliant building data. The application should simulate a real office building with proper equipment relationships, sensor readings, and operational patterns that would be familiar to building operations experts.

## Database Setup Requirements

### 1. TimescaleDB Connection Configuration
**IMPORTANT: Use these specific database credentials:**
- **Host**: localhost
- **Port**: 5432  
- **Database**: datakwip
- **Username**: demo
- **Password**: demo123

### 2. TimescaleDB Local Setup
```sql
-- TimescaleDB is already running in Docker with the provided schema
-- Connect using: psql -h localhost -U demo -d datakwip

-- Add TimescaleDB hypertables for time-series optimization
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert values tables to hypertables for better time-series performance
SELECT create_hypertable('core.values_demo', 'ts', if_not_exists => TRUE);
SELECT create_hypertable('core.values_demo_current', 'ts', if_not_exists => TRUE);
```

### 3. Organization Setup
Create the demo organization with proper isolation:

```sql
-- Create demo organization
INSERT INTO core.org (name, key, value_table, schema_name) 
VALUES ('Demo Building Corp', 'demo', 'values_demo', 'demo');

-- Get the org_id for later use
SELECT id FROM core.org WHERE name = 'Demo Building Corp';
```

**Use these specific table names for time-series data:**
- Primary time-series table: `core.values_demo`
- Current values table: `core.values_demo_current`

## Building Profile to Simulate

### Target Building: "Downtown Office Tower"
- **Type**: Commercial office building
- **Size**: 150,000 sq ft, 12 floors
- **Built**: 2018 (modern building automation)
- **Occupancy**: 8 AM - 6 PM weekdays
- **HVAC**: Variable Air Volume (VAV) system with chillers
- **Lighting**: LED with occupancy sensors
- **Energy**: Utility meters + sub-meters by floor

## Entity Structure to Generate

### 1. Site Entity
```python
# Project Haystack site entity
site_tags = {
    "id": "site-downtown-tower",
    "site": True,
    "dis": "Downtown Office Tower", 
    "area": 150000,  # sq ft
    "areaUnit": "ft²",
    "geoAddr": "123 Business St, Metro City, State 12345",
    "tz": "America/New_York",
    "yearBuilt": 2018,
    "primaryFunction": "office",
    "occupancy": "commercial",
    "weather_station_ref": "weather-metro-city"
}
```

### 2. Equipment Hierarchy (Realistic HVAC System)

#### Chillers (2 units for redundancy)
```python
chiller_1_tags = {
    "id": "equip-chiller-1",
    "equip": True,
    "chiller": True,
    "dis": "Chiller #1 - Primary",
    "siteRef": "site-downtown-tower",
    "cooling": True,
    "coolingCapacity": 400,  # tons
    "coolingCapacityUnit": "tonRefrig",
    "equip_manufacturer": "Carrier",
    "equip_model": "30XA0404",
    "installDate": "2018-03-15",
    "primaryEquip": True
}

chiller_2_tags = {
    "id": "equip-chiller-2", 
    "equip": True,
    "chiller": True,
    "dis": "Chiller #2 - Backup",
    "siteRef": "site-downtown-tower",
    "cooling": True,
    "coolingCapacity": 400,
    "coolingCapacityUnit": "tonRefrig", 
    "equip_manufacturer": "Carrier",
    "equip_model": "30XA0404",
    "installDate": "2018-03-15",
    "primaryEquip": False
}
```

#### Air Handlers (4 units, 3 floors each)
```python
# Generate 4 air handlers
ahu_configs = [
    {"id": "equip-ahu-1", "dis": "AHU-1 Floors 1-3", "floors": [1,2,3]},
    {"id": "equip-ahu-2", "dis": "AHU-2 Floors 4-6", "floors": [4,5,6]}, 
    {"id": "equip-ahu-3", "dis": "AHU-3 Floors 7-9", "floors": [7,8,9]},
    {"id": "equip-ahu-4", "dis": "AHU-4 Floors 10-12", "floors": [10,11,12]}
]

for ahu in ahu_configs:
    ahu_tags = {
        "id": ahu["id"],
        "equip": True,
        "ahu": True,
        "dis": ahu["dis"],
        "siteRef": "site-downtown-tower",
        "airHandling": True,
        "equip_manufacturer": "Trane",
        "equip_model": "Voyager",
        "chilledWaterRef": "equip-chiller-1",  # Primary chiller
        "floors_served": ahu["floors"]
    }
```

#### VAV Boxes (48 total - 4 per floor)
```python
# Generate VAV boxes: 4 zones per floor × 12 floors = 48 VAV boxes
zones_per_floor = ["North", "South", "East", "West"]
for floor in range(1, 13):
    ahu_ref = f"equip-ahu-{((floor-1)//3)+1}"  # Each AHU serves 3 floors
    
    for zone in zones_per_floor:
        vav_tags = {
            "id": f"equip-vav-{floor}-{zone.lower()}",
            "equip": True, 
            "vav": True,
            "dis": f"VAV-{floor}{zone[0]} Floor {floor} {zone}",
            "siteRef": "site-downtown-tower",
            "ahuRef": ahu_ref,
            "floor": floor,
            "zone": zone.lower(),
            "airTerminalUnit": True
        }
```

### 3. Points with Realistic Sensor Data

#### Chiller Points (per chiller)
```python
chiller_points = [
    # Operational status
    {"suffix": "status", "dis": "Status", "kind": "Bool", "writable": False},
    {"suffix": "enable", "dis": "Enable Command", "kind": "Bool", "writable": True},
    
    # Temperatures
    {"suffix": "chwSupplyTemp", "dis": "CHW Supply Temp", "kind": "Number", "unit": "°F", "temp": True, "sensor": True},
    {"suffix": "chwReturnTemp", "dis": "CHW Return Temp", "kind": "Number", "unit": "°F", "temp": True, "sensor": True},
    {"suffix": "condenserSupplyTemp", "dis": "Condenser Supply Temp", "kind": "Number", "unit": "°F", "temp": True, "sensor": True},
    
    # Flow rates
    {"suffix": "chwFlow", "dis": "CHW Flow Rate", "kind": "Number", "unit": "gpm", "flow": True, "sensor": True},
    
    # Power/Energy
    {"suffix": "power", "dis": "Power Consumption", "kind": "Number", "unit": "kW", "elec": True, "sensor": True},
    {"suffix": "energy", "dis": "Energy Consumption", "kind": "Number", "unit": "kWh", "elec": True, "sensor": True},
    
    # Efficiency
    {"suffix": "cop", "dis": "Coefficient of Performance", "kind": "Number", "unit": "COP", "sensor": True}
]
```

#### VAV Box Points (per VAV)
```python
vav_points = [
    # Status and control
    {"suffix": "status", "dis": "Status", "kind": "Bool", "writable": False},
    {"suffix": "enable", "dis": "Enable", "kind": "Bool", "writable": True},
    
    # Temperature control
    {"suffix": "zoneTemp", "dis": "Zone Temperature", "kind": "Number", "unit": "°F", "temp": True, "sensor": True},
    {"suffix": "zoneTempSp", "dis": "Zone Temp Setpoint", "kind": "Number", "unit": "°F", "temp": True, "writable": True},
    {"suffix": "supplyTemp", "dis": "Supply Air Temp", "kind": "Number", "unit": "°F", "temp": True, "sensor": True},
    
    # Airflow
    {"suffix": "airFlow", "dis": "Supply Air Flow", "kind": "Number", "unit": "cfm", "air": True, "sensor": True},
    {"suffix": "airFlowSp", "dis": "Air Flow Setpoint", "kind": "Number", "unit": "cfm", "air": True, "writable": True},
    
    # Damper position
    {"suffix": "damperPos", "dis": "Damper Position", "kind": "Number", "unit": "%", "damper": True, "sensor": True},
    
    # Occupancy
    {"suffix": "occupied", "dis": "Occupancy Status", "kind": "Bool", "occupied": True, "sensor": True}
]
```

#### Utility Meters
```python
utility_meters = [
    {
        "id": "meter-main-electric",
        "dis": "Main Electric Meter", 
        "elec": True,
        "meter": True,
        "points": ["power", "energy", "voltage", "current", "powerFactor"]
    },
    {
        "id": "meter-main-gas",
        "dis": "Main Gas Meter",
        "gas": True, 
        "meter": True,
        "points": ["flow", "volume", "pressure"]
    },
    {
        "id": "meter-main-water",
        "dis": "Main Water Meter",
        "water": True,
        "meter": True, 
        "points": ["flow", "volume", "pressure"]
    }
]
```

## Realistic Data Generation Patterns

### 1. Time-Series Data Generation Strategy

#### Occupancy-Based Schedule
```python
def generate_occupancy_schedule():
    """Generate realistic occupancy patterns"""
    schedule = {
        "weekday": {
            "6:00": 0.05,   # Early arrivals
            "7:00": 0.15,   # Some early workers
            "8:00": 0.60,   # Main arrival time
            "9:00": 0.85,   # Peak occupancy
            "12:00": 0.70,  # Lunch time dip
            "13:00": 0.85,  # Back from lunch
            "17:00": 0.70,  # Some leaving early
            "18:00": 0.20,  # Most gone
            "19:00": 0.05,  # Cleaning crew
            "22:00": 0.02   # Security only
        },
        "weekend": {
            "all_day": 0.05  # Minimal occupancy
        }
    }
    return schedule
```

#### Temperature Control Logic
```python
def generate_zone_temperature(hour, occupancy_ratio, outdoor_temp, season):
    """Generate realistic zone temperatures"""
    
    # Base setpoints based on occupancy
    if occupancy_ratio > 0.1:  # Occupied
        base_setpoint = 72.0
    else:  # Unoccupied
        base_setpoint = 75.0 if season == "summer" else 68.0
    
    # Add realistic variations
    temp_variance = random.uniform(-1.5, 1.5)  # Sensor noise
    solar_load = calculate_solar_load(hour, season)  # Solar heating effect
    
    actual_temp = base_setpoint + temp_variance + solar_load
    
    # Clamp to realistic bounds
    return max(65.0, min(80.0, actual_temp))
```

#### HVAC Equipment Efficiency
```python
def generate_chiller_cop(load_ratio, outdoor_temp):
    """Generate realistic chiller COP based on load and conditions"""
    
    # Chiller efficiency curve (typical centrifugal chiller)
    base_cop = 6.2  # Full load design COP
    
    # Part load efficiency curve
    if load_ratio < 0.2:
        efficiency_factor = 0.3  # Poor efficiency at low loads
    elif load_ratio < 0.4:
        efficiency_factor = 0.7
    elif load_ratio < 0.8:
        efficiency_factor = 0.95  # Peak efficiency
    else:
        efficiency_factor = 0.9   # Slight drop at full load
    
    # Outdoor temperature impact
    temp_factor = 1.0 - ((outdoor_temp - 85.0) * 0.02)  # 2% per degree over 85°F
    
    return base_cop * efficiency_factor * temp_factor
```

### 2. Data Generation Timeline
Generate 30 days of historical data with:
- **15-minute intervals** for time-series data
- **Realistic seasonal patterns** (choose current season)
- **Weekend vs weekday differences**
- **Equipment maintenance events** (occasional shutdowns)
- **Weather correlation** (outdoor temperature impacts)

### 3. Data Quality Simulation
Include realistic data quality issues:
- **Sensor drift**: Gradual calibration errors
- **Communication errors**: Occasional "stale" or "fault" status
- **Maintenance periods**: Equipment offline for service
- **Calibration events**: Sudden corrections in sensor readings

## Implementation Requirements

### 1. Application Structure
```
building_data_generator/
├── src/
│   ├── database/
│   │   ├── connection.py      # TimescaleDB connection
│   │   ├── schema_setup.py    # Create tables and hypertables
│   │   └── data_loader.py     # Insert generated data
│   ├── generators/
│   │   ├── entities.py        # Generate entity hierarchy
│   │   ├── time_series.py     # Generate sensor data
│   │   ├── weather.py         # Weather data simulation
│   │   └── schedules.py       # Occupancy and operational schedules
│   ├── models/
│   │   ├── building.py        # Building system models
│   │   ├── hvac.py           # HVAC equipment models
│   │   └── sensors.py         # Sensor behavior models
│   └── main.py               # Main generation script
├── config/
│   ├── building_config.yaml   # Building parameters
│   └── database_config.yaml   # Database connection settings
├── requirements.txt
└── README.md
```

### 2. Core Technologies
- **Python 3.11+** for data generation
- **SQLAlchemy + Pydantic** for database operations
- **TimescaleDB** for time-series storage
- **NumPy/Pandas** for data manipulation
- **PyYAML** for configuration
- **Rich** for progress bars and CLI output

### 3. Configuration Management
Use YAML configuration files for:
- Building parameters (size, equipment counts, etc.)
- Data generation settings (time ranges, intervals)
- Database connection details
- Equipment specifications and performance curves

### 4. Data Validation
Include validation to ensure:
- **Project Haystack compliance**: All tags follow standards
- **Physical realism**: Temperature/pressure/flow values make sense
- **Relationship integrity**: Equipment hierarchy is correct
- **Time-series consistency**: No impossible jumps or values

## Expected Output

### 1. Database Population
After running the generator:
- **1 site entity** with proper Project Haystack tags
- **55+ equipment entities** (chillers, AHUs, VAVs, meters)
- **400+ point entities** with realistic sensor configurations
- **720,000+ time-series records** (30 days × 96 intervals/day × 250 points)

### 2. Realistic Data Patterns
- **Occupancy-driven HVAC loads**
- **Seasonal weather impacts** 
- **Equipment efficiency curves**
- **Energy consumption patterns**
- **Temperature control responses**

### 3. Data Quality Examples
- **95% good data** with "ok" status
- **3% stale data** during communication issues
- **2% fault data** during maintenance events
- **Realistic sensor noise** and measurement uncertainty

## Validation Queries

After generation, these queries should return realistic results:

```sql
-- Average zone temperatures during occupied hours
SELECT AVG(value_n) as avg_temp 
FROM core.values_demo 
WHERE entity_id IN (SELECT id FROM core.entity WHERE tags->'zoneTemp' = 'true')
AND EXTRACT(hour FROM ts) BETWEEN 8 AND 18;

-- Chiller efficiency over time
SELECT ts, value_n as cop
FROM core.values_demo
WHERE entity_id IN (SELECT id FROM core.entity WHERE tags->'cop' = 'true')
ORDER BY ts;

-- Building energy consumption by day
SELECT DATE(ts) as date, SUM(value_n) as daily_kwh
FROM core.values_demo  
WHERE entity_id IN (SELECT id FROM core.entity WHERE tags->'energy' = 'true')
GROUP BY DATE(ts)
ORDER BY date;
```

This generator will create a comprehensive, realistic building dataset that building operations experts would recognize as authentic and useful for testing AI-powered building intelligence applications.