# Critical Design Decisions and Learnings

**← [Back to Main README](../README.md)** | **Developer Documentation**

**Related Documentation**:
- [Empty vs Existing DB](../docs/EMPTY_VS_EXISTING_DB.md) - Database initialization
- [Service Mode Guide](../docs/SERVICE_MODE_SUMMARY.md) - Implementation overview

## Instructions for Maintaining This Document
**IMPORTANT**: Always log critical design decisions, functional conclusions, and important learnings in this file. This ensures knowledge persistence across sessions and helps maintain consistent behavior.

When to update this file:
- After identifying critical bugs or design flaws
- When making architectural decisions
- After discovering important domain-specific requirements
- When implementing solutions to complex problems

---

## Data Coherency and Multiple Run Handling
**Date**: 2025-08-13
**Issue**: Running main.py multiple times creates incoherent datasets

### Problem Identified
The simulator was creating duplicate entities on each run while updating existing time-series data, resulting in:
- Multiple sets of equipment entities (e.g., multiple "AHU-1" with different entity IDs)
- Orphaned time-series data pointing to old entity IDs
- Broken relationships between VAVs→AHUs, Points→Equipment
- Invalid dataset from a building operations domain expert perspective

### Critical Requirement
**The entire dataset must be coherent after every execution**. This means:
- Equipment relationships must be valid (VAVs connected to correct AHUs)
- Time-series data must correspond to existing entities
- Weather and occupancy patterns must align with equipment behavior
- No orphaned or duplicate entities

### Solution Implemented
**Option 1: Full Reset Approach**
- Added `--reset` flag to main.py
- When used, truncates all data tables before generating new data
- Ensures complete data coherency
- Guarantees a valid building operations dataset

### Database Tables Affected by Reset
```sql
TRUNCATE core.entity CASCADE;
TRUNCATE core.entity_tag CASCADE;
TRUNCATE core.values_demo CASCADE;
TRUNCATE core.values_demo_current CASCADE;
-- Organization table is preserved (checked for existence)
```

### Usage Pattern
```bash
# Safe rerun with coherent data (RECOMMENDED)
python src/main.py --reset

# Generate only entities with reset
python src/main.py --reset --entities-only

# Normal run (only safe for first run)
python src/main.py
```

### Implementation Details
- Added `reset_all_data()` method to DatabaseConnection class
- Truncates: `values_demo`, `values_demo_current`, `entity`, `entity_tag`
- Preserves organization data (reused if exists)
- Handles optional tables gracefully (e.g., `entity_his` if not present)
- Integrated into main.py with `--reset` command line flag

### Why This Matters
Building automation systems require logical consistency:
- A temperature sensor must belong to exactly one VAV box
- A VAV box must be controlled by exactly one AHU
- Historical data must match the equipment that generated it
- Energy consumption must align with occupancy and weather patterns

### Future Considerations
Alternative approaches for future implementation:
1. **Idempotent Generation**: Check entity existence before creation
2. **Append Mode**: Only add new time-series to existing entities
3. **Transaction-Based**: Atomic operations with rollback capability

---

## Entity Relationship Model
**Date**: 2025-08-13

### Hierarchy
```
Site
├── Chillers (Primary/Backup)
├── AHUs (serve specific floors)
│   └── VAV Boxes (multiple per AHU)
│       └── Zones
├── Meters (Electric, Gas, Water)
└── Points (sensors and actuators for each equipment)
```

### Key Relationships
- VAVs reference their parent AHU via `ahuRef`
- Points reference their parent equipment via `equipRef`
- All equipment references the site via `siteRef`
- Time-series data links to entities via `entity_id`

---

## Data Generation Logic
**Date**: 2025-08-13

### Coherency Rules
1. **Occupancy affects**:
   - Zone temperature setpoints
   - VAV airflow
   - Lighting and equipment loads

2. **Weather affects**:
   - Chiller load
   - AHU supply temperature
   - Building heat gain/loss

3. **Equipment interactions**:
   - Chiller status affects AHU operation
   - AHU status affects VAV operation
   - VAV damper position affects zone temperature

These relationships must be preserved across all data generation runs.

---

## SQL Query Fixes
**Date**: 2025-08-13
**Issue**: Ambiguous column reference in validation queries

### Problem
Validation query in `display_validation_results()` failed with:
```
column reference "value_n" is ambiguous
```

### Root Cause
The query joined multiple tables that may contain columns with the same name. Without table aliasing, PostgreSQL couldn't determine which table's column to use.

### Fix
Explicitly qualified column references with table aliases:
```sql
-- Before (ambiguous)
SELECT AVG(value_n) as avg_temp 

-- After (explicit)
SELECT AVG(v.value_n) as avg_temp 
```

### Best Practice
Always use table aliases in JOINs and qualify column references to avoid ambiguity, especially in complex queries with multiple tables.

---

## Table Naming and Configuration Flexibility
**Date**: 2025-10-03
**Issue**: Hardcoded table names in tests and validation scripts caused Docker testing failures

### Problem Identified
- Tests and validation scripts used hardcoded `'values_demo'` table name
- Docker config uses organization key `docker_test` → creates `values_docker_test` tables
- Default config uses organization key `demo` → creates `values_demo` tables
- This mismatch caused "relation does not exist" errors during testing

### Root Cause
Table names are generated from `organization.key` in config files:
```python
table_name = f"values_{org_key}"
current_table = f"values_{org_key}_current"
```

### Solution Implemented
- Updated all test files to read table name from config instead of hardcoding
- Updated all validation scripts to get table name from config
- Modified config loading functions to return full config (not just database section)

### Files Fixed
1. `test/test_gap_filler.py` - Now reads `config['tables']['value_table']`
2. `test/test_resumption.py` - Now uses configured table name
3. `validation/validate_service_state.py` - Loads full config
4. `validation/validate_gaps.py` - Uses table_name parameter
5. `validation/validate_service_health.py` - Reads from config

### Best Practice
Never hardcode table names. Always read from configuration:
```python
db_config, building_config = load_config()
table_name = db_config['tables']['value_table']
```

---

## Timezone Handling in Validation Scripts
**Date**: 2025-10-03
**Issue**: TypeError when comparing timezone-aware and timezone-naive datetime objects

### Problem
PostgreSQL returns timezone-aware timestamps (e.g., `2025-10-03 18:15:00+00:00`)
Python's `datetime.now()` returns timezone-naive timestamps
Subtraction between them fails: `TypeError: can't subtract offset-naive and offset-aware datetimes`

### Solution
Convert both to timezone-naive before comparison:
```python
# Make timezone-naive for comparison
ts_naive = ts.replace(tzinfo=None) if ts.tzinfo else ts
now_naive = datetime.now()
diff = (now_naive - ts_naive).total_seconds() / 60
```

### Files Fixed
- `validation/validate_service_state.py` (2 occurrences)
- `validation/validate_service_health.py` (2 occurrences)

### Best Practice
When comparing database timestamps with current time:
1. Always handle both timezone-aware and timezone-naive cases
2. Convert to consistent timezone (naive for local operations)
3. Use `.replace(tzinfo=None)` to strip timezone info

---

## Reset Function Incomplete Cleanup
**Date**: 2025-10-03
**Issue**: `--reset` flag doesn't truncate value tables, causing data overlap

### Problem Identified
During testing, discovered that running with `--reset` flag:
- ✅ Truncates `entity` and `entity_tag` tables
- ❌ Does NOT truncate `values_*` tables
- Result: Old data remains with old entity IDs, new data uses new entity IDs
- Causes totalizer "decreases" when old and new entity IDs overlap

### Manifestation
Running tests showed "❌ Found 2 totalizer decreases!" because:
- Old data: Entities 410-702, dates Sept 26 - Oct 3
- New data: Entities 352-702, dates Oct 2 - Oct 3
- Entity 697 existed in both datasets with different totalizer ranges
- Appeared as massive decrease: 48,894.6 kWh drop

### Workaround Applied
Manual truncation before data generation:
```sql
TRUNCATE TABLE core.values_docker_test CASCADE;
TRUNCATE TABLE core.values_docker_test_current CASCADE;
```

### Fix Applied (2025-10-03)
Updated `DatabaseConnection.reset_all_data()` to accept dynamic table names:
```python
def reset_all_data(self, value_table=None, current_table=None):
    """Reset all data tables to ensure coherent dataset."""
    reset_queries = [
        "TRUNCATE core.entity CASCADE;",
        "TRUNCATE core.entity_tag CASCADE;",
        "TRUNCATE core.org_entity_permission CASCADE;",
        "TRUNCATE core.entity_his CASCADE;",
        "TRUNCATE core.simulator_state CASCADE;"
    ]
    if value_table:
        reset_queries.insert(0, f"TRUNCATE core.{value_table} CASCADE;")
    if current_table:
        reset_queries.insert(1, f"TRUNCATE core.{current_table} CASCADE;")
```

Updated `main.py` to pass table names from config:
```python
db.reset_all_data(
    value_table=db_config['tables']['value_table'],
    current_table=db_config['tables']['current_table']
)
```

### Lesson Learned
Data coherency requires complete cleanup. Partial resets lead to invalid datasets that appear correct on surface but fail validation. Always ensure reset functions are aware of dynamic table naming schemes.

---

## Decimal vs Float Type Mismatch
**Date**: 2025-10-03
**Issue**: PostgreSQL interval queries return Decimal type, Python expects float

### Problem
Gap validation query returns `interval_minutes` as `decimal.Decimal`:
```python
interval = row['interval_minutes']  # This is Decimal
if abs(interval - 15.0) <= 1.0:  # TypeError: unsupported operand type(s)
```

### Solution
Explicitly convert Decimal to float:
```python
interval = float(row['interval_minutes']) if row['interval_minutes'] is not None else 0.0
```

### File Fixed
- `validation/validate_gaps.py`

### Best Practice
When using PostgreSQL's `EXTRACT(EPOCH FROM ...)` or similar time functions:
- PostgreSQL returns numeric/decimal types
- Python arithmetic expects float
- Always cast to float: `float(row['column_name'])`