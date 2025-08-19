# Claude Code Assistant Instructions

## Project Overview
This is a Haystack Building Data Simulator that generates realistic building automation system data for a PostgreSQL database following the Haystack v3 schema.

## Folder Structure and File Organization

### Always place files in the correct folders:

```
haystack-data-simulator/
├── config/                 # Configuration files
│   ├── building_config.yaml
│   └── database_config.yaml
│
├── docs/                   # Project documentation
│   └── project-requirements.md
│
├── knowledge/              # Critical design decisions and guides
│   ├── CRITICAL_DESIGN_DECISIONS.md
│   └── MCP_SERVER_IMPLEMENTATION_GUIDE.md
│
├── schema/                 # Database schema files
│   └── sql_schema_core_v2.sql
│
├── src/                    # Source code
│   ├── database/          # Database connection and operations
│   │   ├── connection.py
│   │   ├── data_loader.py
│   │   └── schema_setup.py
│   │
│   ├── generators/        # Data generation modules
│   │   ├── entities.py
│   │   ├── schedules.py
│   │   ├── time_series.py
│   │   └── weather.py
│   │
│   ├── models/           # Data models
│   │   ├── building.py
│   │   ├── hvac.py
│   │   └── sensors.py
│   │
│   └── main.py           # Main entry point
│
├── test/                  # Test files
│   ├── test_*.py         # Unit and integration tests
│   └── verify_*.py       # Verification scripts
│
├── validation/           # Data validation scripts
│   └── validate_*.py     # Various validation utilities
│
└── requirements.txt      # Python dependencies
```

## File Placement Rules

1. **Configuration Files**: Place in `config/`
   - YAML, JSON, or INI configuration files
   - Environment-specific settings

2. **Source Code**: Place in `src/`
   - Database operations → `src/database/`
   - Data generators → `src/generators/`
   - Data models → `src/models/`
   - Main scripts → `src/`

3. **Tests**: Place in `test/`
   - Unit tests → `test/test_*.py`
   - Integration tests → `test/test_*.py`
   - Verification scripts → `test/verify_*.py`

4. **Validation Scripts**: Place in `validation/`
   - Data validation → `validation/validate_*.py`
   - Schema validation → `validation/validate_*.py`

5. **Documentation**: Place in `docs/`
   - Project requirements
   - API documentation
   - User guides

6. **Knowledge Base**: Place in `knowledge/`
   - Critical design decisions
   - Implementation guides
   - Lessons learned

7. **Database Schemas**: Place in `schema/`
   - SQL schema files
   - Migration scripts

8. **Temporary Files**: Don't commit
   - Log files (*.log)
   - Cache files
   - IDE configuration

## Important Commands

### Running the Simulator
```bash
# Full reset and generate 30 days of data
python src/main.py --reset --days 30

# Generate only entities
python src/main.py --reset --entities-only

# Generate 7 days without reset (only safe for first run)
python src/main.py --days 7
```

### Testing
```bash
# Run all tests
python -m pytest test/

# Run specific test
python test/test_missing_points.py

# Verify data coherence
python test/verify_coherence.py
```

### Validation
```bash
# Validate all points have data
python validation/validate_all_points_data.py

# Validate equipment status
python validation/validate_equipment_status.py
```

## Key Design Decisions

1. **Data Coherency**: Always use `--reset` flag when regenerating data to ensure coherent datasets
2. **Missing Data Points**: All sensor points (except command points) should generate data when equipment is running
3. **Totalizers**: Energy and volume meters accumulate monotonically (never decrease)
4. **Physical Relationships**: 
   - Condenser temp > CHW return temp
   - Mixed air temp between outdoor and return temps
   - Static pressure follows fan affinity laws

## Common Issues and Solutions

1. **Database Connection Error**: Ensure PostgreSQL is running and credentials in `config/database_config.yaml` are correct
2. **Missing Data Points**: Check that equipment is running (status=True) - offline equipment doesn't generate sensor data
3. **Incoherent Data**: Use `--reset` flag to clear all data before regenerating

## Development Guidelines

1. Always maintain data coherency - equipment relationships must be valid
2. Follow Haystack v3 tagging conventions
3. Generate physically realistic data that follows building physics
4. Log critical decisions in `knowledge/CRITICAL_DESIGN_DECISIONS.md`
5. Create tests for new functionality in `test/` folder
6. Document complex algorithms and relationships