# Critical Design Decisions and Learnings

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