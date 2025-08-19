"""Test database connection and basic functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

try:
    import yaml
    print("✓ PyYAML import successful")
except ImportError as e:
    print(f"✗ PyYAML import failed: {e}")
    sys.exit(1)

try:
    import psycopg2
    print("✓ psycopg2 import successful")
except ImportError as e:
    print(f"✗ psycopg2 import failed: {e}")
    print("Please install: pip install psycopg2-binary")
    sys.exit(1)

try:
    import pandas as pd
    import numpy as np
    from rich.console import Console
    print("✓ Additional dependencies import successful")
except ImportError as e:
    print(f"✗ Additional dependencies import failed: {e}")
    print("Please install: pip install -r requirements.txt")
    sys.exit(1)

# Test configuration loading
try:
    with open('config/database_config.yaml', 'r') as f:
        db_config = yaml.safe_load(f)
    print("✓ Database config loaded successfully")
except Exception as e:
    print(f"✗ Failed to load database config: {e}")
    sys.exit(1)

try:
    with open('config/building_config.yaml', 'r') as f:
        building_config = yaml.safe_load(f)
    print("✓ Building config loaded successfully")
except Exception as e:
    print(f"✗ Failed to load building config: {e}")
    sys.exit(1)

# Test database connection
try:
    from database.connection import DatabaseConnection
    
    db = DatabaseConnection(db_config['database'])
    result = db.execute_query("SELECT 1 as test")
    
    if result and result[0]['test'] == 1:
        print("✓ Database connection test successful")
    else:
        print("✗ Database connection test failed - unexpected result")
        sys.exit(1)
        
    # Test basic table queries
    result = db.execute_query("SELECT COUNT(*) as count FROM core.entity")
    print(f"✓ Found {result[0]['count']} existing entities")
    
    result = db.execute_query("SELECT COUNT(*) as count FROM core.tag_def")
    print(f"✓ Found {result[0]['count']} tag definitions")
    
    db.close()
    print("✓ Database connection closed cleanly")
    
except Exception as e:
    print(f"✗ Database connection test failed: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure TimescaleDB is running")
    print("2. Check database credentials in config/database_config.yaml")
    print("3. Verify database 'datakwip' exists")
    print("4. Test manual connection: psql -h localhost -U demo -d datakwip")
    sys.exit(1)

# Test module imports
try:
    from generators.entities import EntityGenerator
    from generators.time_series import TimeSeriesGenerator
    from generators.weather import WeatherSimulator
    from generators.schedules import ScheduleGenerator
    from database.schema_setup import SchemaSetup
    from database.data_loader import DataLoader
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Module import failed: {e}")
    sys.exit(1)

print("\n🎉 All tests passed! Ready to generate building data.")
print("\nTo generate data, run:")
print("python src/main.py --days 7  # Generate 7 days of data")
print("python src/main.py --entities-only  # Generate entities only")