#!/usr/bin/env python3
"""Validation script to check if site entities are properly cleaned up after data deletion."""

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


def validate_cleanup(db: DatabaseConnection):
    """Validate that all site-related data has been properly cleaned up.
    
    Args:
        db: Database connection instance
        
    Returns:
        Dictionary with validation results
    """
    results = {}
    
    # Check for orphaned entity tags
    query = """
        SELECT COUNT(*) as orphaned_tags
        FROM core.entity_tag et
        LEFT JOIN core.entity e ON et.entity_id = e.id
        WHERE e.id IS NULL
    """
    orphaned_tags = db.execute_query(query)[0]['orphaned_tags']
    results['orphaned_entity_tags'] = orphaned_tags
    
    # Check for orphaned permissions
    query = """
        SELECT COUNT(*) as orphaned_permissions
        FROM core.org_entity_permission oep
        LEFT JOIN core.entity e ON oep.entity_id = e.id
        WHERE e.id IS NULL
    """
    try:
        orphaned_permissions = db.execute_query(query)[0]['orphaned_permissions']
        results['orphaned_permissions'] = orphaned_permissions
    except Exception as e:
        if "does not exist" in str(e):
            results['orphaned_permissions'] = "Table does not exist"
        else:
            raise
    
    # Check for orphaned time-series data
    query = """
        SELECT COUNT(*) as orphaned_values
        FROM core.values_demo vd
        LEFT JOIN core.entity e ON vd.entity_id = e.id
        WHERE e.id IS NULL
    """
    orphaned_values = db.execute_query(query)[0]['orphaned_values']
    results['orphaned_values'] = orphaned_values
    
    # Check for orphaned current values
    query = """
        SELECT COUNT(*) as orphaned_current_values
        FROM core.values_demo_current vdc
        LEFT JOIN core.entity e ON vdc.entity_id = e.id
        WHERE e.id IS NULL
    """
    orphaned_current_values = db.execute_query(query)[0]['orphaned_current_values']
    results['orphaned_current_values'] = orphaned_current_values
    
    # Count remaining entities by type
    entity_types = ['site', 'equip', 'point']
    for entity_type in entity_types:
        query = """
            SELECT COUNT(DISTINCT et.entity_id) as count
            FROM core.entity_tag et
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = %s AND et.value_b = true
        """
        count = db.execute_query(query, (entity_type,))[0]['count']
        results[f'remaining_{entity_type}_entities'] = count
    
    # Check tag definitions (these should remain)
    query = "SELECT COUNT(*) as tag_def_count FROM core.tag_def"
    tag_defs = db.execute_query(query)[0]['tag_def_count']
    results['tag_definitions'] = tag_defs
    
    # Check organizations (these should remain)
    query = "SELECT COUNT(*) as org_count FROM core.org"
    orgs = db.execute_query(query)[0]['org_count']
    results['organizations'] = orgs
    
    return results


def run_cleanup_validation():
    """Run the cleanup validation and return results."""
    logger.info("Starting site cleanup validation...")
    
    try:
        # Load database configuration
        db_config = load_database_config()
        logger.info(f"Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Create database connection
        db = DatabaseConnection(db_config)
        
        # Validate cleanup
        results = validate_cleanup(db)
        
        # Print results
        print("\n" + "="*50)
        print("SITE CLEANUP VALIDATION RESULTS")
        print("="*50)
        
        # Check for orphaned data
        print("Orphaned Data Check:")
        print("-" * 30)
        issues_found = 0
        
        if results['orphaned_entity_tags'] > 0:
            print(f"⚠️  WARNING: {results['orphaned_entity_tags']} orphaned entity tags found")
            issues_found += 1
        else:
            print("✅ No orphaned entity tags")
            
        if isinstance(results['orphaned_permissions'], int) and results['orphaned_permissions'] > 0:
            print(f"⚠️  WARNING: {results['orphaned_permissions']} orphaned permissions found")
            issues_found += 1
        elif isinstance(results['orphaned_permissions'], str):
            print(f"ℹ️  Permissions table: {results['orphaned_permissions']}")
        else:
            print("✅ No orphaned permissions")
            
        if results['orphaned_values'] > 0:
            print(f"⚠️  WARNING: {results['orphaned_values']} orphaned time-series values found")
            issues_found += 1
        else:
            print("✅ No orphaned time-series values")
            
        if results['orphaned_current_values'] > 0:
            print(f"⚠️  WARNING: {results['orphaned_current_values']} orphaned current values found")
            issues_found += 1
        else:
            print("✅ No orphaned current values")
        
        # Check remaining entities
        print("\nRemaining Entities:")
        print("-" * 30)
        print(f"Site entities: {results['remaining_site_entities']}")
        print(f"Equipment entities: {results['remaining_equip_entities']}")
        print(f"Point entities: {results['remaining_point_entities']}")
        
        # Check preserved data
        print("\nPreserved Data:")
        print("-" * 30)
        print(f"Tag definitions: {results['tag_definitions']}")
        print(f"Organizations: {results['organizations']}")
        
        # Overall assessment
        print("\n" + "="*50)
        print("OVERALL ASSESSMENT")
        print("="*50)
        
        if issues_found == 0:
            print("✅ CLEANUP VALIDATION PASSED: No orphaned data found")
        else:
            print(f"⚠️  CLEANUP VALIDATION FAILED: {issues_found} issue(s) found")
            
        total_entities = (results['remaining_site_entities'] + 
                         results['remaining_equip_entities'] + 
                         results['remaining_point_entities'])
        
        if total_entities == 0:
            print("✅ All entities successfully deleted")
        else:
            print(f"ℹ️  {total_entities} entities remain in database")
        
        # Close connection
        db.close()
        
        return results, issues_found == 0
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


def main():
    """Main validation function."""
    results, passed = run_cleanup_validation()
    exit_code = 0 if passed else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()