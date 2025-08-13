"""Validation script to verify the Haystack data simulator setup."""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from database.connection import DatabaseConnection
import yaml

def main():
    # Load database config
    with open('config/database_config.yaml', 'r') as f:
        db_config = yaml.safe_load(f)
    
    db = DatabaseConnection(db_config['database'])
    
    print("HAYSTACK BUILDING DATA SIMULATOR - VALIDATION RESULTS")
    print("=" * 60)
    
    # Check entity counts
    queries = {
        "Total Entities": "SELECT COUNT(*) as count FROM core.entity",
        "Entity Tags": "SELECT COUNT(*) as count FROM core.entity_tag",
        "Tag Definitions": "SELECT COUNT(*) as count FROM core.tag_def"
    }
    
    for name, query in queries.items():
        result = db.execute_query(query)
        count = result[0]['count'] if result else 0
        print(f"{name:20}: {count:,}")
    
    print("\nENTITY BREAKDOWN")
    print("-" * 30)
    
    # Get entity types
    entity_types_query = """
        SELECT 
            CASE 
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'site' AND et.entity_id = e.id) THEN 'Site'
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'equip' AND et.entity_id = e.id) THEN 'Equipment'
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'point' AND et.entity_id = e.id) THEN 'Point'
                ELSE 'Other'
            END as entity_type,
            COUNT(*) as count
        FROM core.entity e
        GROUP BY entity_type
        ORDER BY count DESC
    """
    
    result = db.execute_query(entity_types_query)
    for row in result:
        print(f"{row['entity_type']:12}: {row['count']:,}")
    
    print("\nEQUIPMENT TYPES")
    print("-" * 20)
    
    # Get equipment breakdown
    equipment_query = """
        SELECT 
            CASE 
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'chiller' AND et.entity_id = e.id) THEN 'Chiller'
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'ahu' AND et.entity_id = e.id) THEN 'AHU'
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'vav' AND et.entity_id = e.id) THEN 'VAV'
                WHEN EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                           WHERE td.name = 'meter' AND et.entity_id = e.id) THEN 'Meter'
                ELSE 'Other'
            END as equip_type,
            COUNT(*) as count
        FROM core.entity e
        WHERE EXISTS (SELECT 1 FROM core.entity_tag et JOIN core.tag_def td ON et.tag_id = td.id 
                     WHERE td.name = 'equip' AND et.entity_id = e.id)
        GROUP BY equip_type
        ORDER BY count DESC
    """
    
    result = db.execute_query(equipment_query)
    for row in result:
        print(f"{row['equip_type']:8}: {row['count']}")
    
    print("\nSAMPLE ENTITIES")
    print("-" * 17)
    
    # Show sample entities
    sample_query = """
        SELECT e.id, string_agg(
            CASE WHEN td.name = 'dis' THEN et.value_s ELSE NULL END, ''
        ) as display_name
        FROM core.entity e
        JOIN core.entity_tag et ON e.id = et.entity_id
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name IN ('dis', 'site', 'equip', 'point')
        GROUP BY e.id
        HAVING string_agg(
            CASE WHEN td.name = 'dis' THEN et.value_s ELSE NULL END, ''
        ) IS NOT NULL
        ORDER BY e.id
        LIMIT 10
    """
    
    result = db.execute_query(sample_query)
    for row in result:
        display_name = row['display_name'] or f"Entity {row['id']}"
        print(f"ID {row['id']:4}: {display_name}")
    
    print("\nSUCCESS: Setup Validation Complete!")
    print("\nNext Steps:")
    print("1. Generate time-series data: python src/main.py --days 7")
    print("2. View validation results: python src/main.py --skip-validation")
    
    db.close()

if __name__ == '__main__':
    main()