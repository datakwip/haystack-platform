#!/usr/bin/env python3
"""Test script to count site entities in the database."""

import logging
import sys
import os
import yaml

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_database_config():
    """Load database configuration from config file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'database_config.yaml')
    
    if not os.path.exists(config_path):
        # Fallback to environment variables
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'haystack'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        return config['database']


def count_site_entities(db: DatabaseConnection):
    """Count site entities in the database.
    
    Args:
        db: Database connection instance
        
    Returns:
        Dictionary with entity counts
    """
    results = {}
    
    # Count total entities
    query = "SELECT COUNT(*) as total FROM core.entity"
    total_entities = db.execute_query(query)[0]['total']
    results['total_entities'] = total_entities
    
    # Count site entities (entities with site=true tag)
    query = """
        SELECT COUNT(DISTINCT et.entity_id) as site_count
        FROM core.entity_tag et
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'site' AND et.value_b = true
    """
    site_entities = db.execute_query(query)[0]['site_count']
    results['site_entities'] = site_entities
    
    # Get site entity details
    query = """
        SELECT 
            e.id as entity_id,
            et_id.value_s as site_id,
            et_name.value_s as site_name
        FROM core.entity e
        JOIN core.entity_tag et_site ON e.id = et_site.entity_id
        JOIN core.tag_def td_site ON et_site.tag_id = td_site.id
        LEFT JOIN core.entity_tag et_id ON e.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity_tag et_name ON e.id = et_name.entity_id
        LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
        WHERE td_site.name = 'site' AND et_site.value_b = true
    """
    site_details = db.execute_query(query)
    results['site_details'] = site_details
    
    # Count equipment entities
    query = """
        SELECT COUNT(DISTINCT et.entity_id) as equip_count
        FROM core.entity_tag et
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'equip' AND et.value_b = true
    """
    equip_entities = db.execute_query(query)[0]['equip_count']
    results['equipment_entities'] = equip_entities
    
    # Count point entities
    query = """
        SELECT COUNT(DISTINCT et.entity_id) as point_count
        FROM core.entity_tag et
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'point' AND et.value_b = true
    """
    point_entities = db.execute_query(query)[0]['point_count']
    results['point_entities'] = point_entities
    
    return results


def main():
    """Main test function."""
    logger.info("Starting site entity count test...")
    
    try:
        # Load database configuration
        db_config = load_database_config()
        logger.info(f"Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Create database connection
        db = DatabaseConnection(db_config)
        
        # Count entities
        results = count_site_entities(db)
        
        # Print results
        print("\n" + "="*50)
        print("SITE ENTITY COUNT RESULTS")
        print("="*50)
        print(f"Total entities: {results['total_entities']}")
        print(f"Site entities: {results['site_entities']}")
        print(f"Equipment entities: {results['equipment_entities']}")
        print(f"Point entities: {results['point_entities']}")
        
        print("\nSite Details:")
        print("-" * 30)
        if results['site_details']:
            for site in results['site_details']:
                print(f"  Entity ID: {site['entity_id']}")
                print(f"  Site ID: {site['site_id']}")
                print(f"  Site Name: {site['site_name']}")
                print()
        else:
            print("  No site entities found!")
            
        # Calculate breakdown
        other_entities = results['total_entities'] - results['site_entities'] - results['equipment_entities'] - results['point_entities']
        print(f"Other entities: {other_entities}")
        
        # Validation warnings
        print("\n" + "="*50)
        print("VALIDATION CHECKS")
        print("="*50)
        
        if results['site_entities'] == 0:
            print("⚠️  WARNING: No site entities found! Data may not have been generated properly.")
        elif results['site_entities'] > 1:
            print(f"⚠️  WARNING: Found {results['site_entities']} sites. Expected 1 site for typical building simulation.")
        else:
            print("✅ Site count looks normal (1 site found)")
            
        if results['total_entities'] == 0:
            print("⚠️  WARNING: No entities found in database! Database appears empty.")
        else:
            print(f"✅ Database contains {results['total_entities']} total entities")
            
        # Close connection
        db.close()
        
        return results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise


if __name__ == "__main__":
    main()