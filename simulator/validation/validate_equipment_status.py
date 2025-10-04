#!/usr/bin/env python3
"""Validation script to check equipment status and current values."""

import logging
import sys
import os
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Any

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


def get_equipment_list(db: DatabaseConnection) -> List[Dict[str, Any]]:
    """Get list of all equipment entities.
    
    Args:
        db: Database connection instance
        
    Returns:
        List of equipment dictionaries
    """
    query = """
        SELECT DISTINCT
            e.id as entity_id,
            et_id.value_s as equip_id,
            et_name.value_s as equip_name,
            COALESCE(
                CASE WHEN et_chiller.value_b THEN 'chiller' END,
                CASE WHEN et_ahu.value_b THEN 'ahu' END,
                CASE WHEN et_vav.value_b THEN 'vav' END,
                CASE WHEN et_meter.value_b THEN 'meter' END,
                'unknown'
            ) as equip_type
        FROM core.entity e
        JOIN core.entity_tag et_equip ON e.id = et_equip.entity_id
        JOIN core.tag_def td_equip ON et_equip.tag_id = td_equip.id AND td_equip.name = 'equip'
        LEFT JOIN core.entity_tag et_id ON e.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity_tag et_name ON e.id = et_name.entity_id
        LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
        LEFT JOIN core.entity_tag et_chiller ON e.id = et_chiller.entity_id
        LEFT JOIN core.tag_def td_chiller ON et_chiller.tag_id = td_chiller.id AND td_chiller.name = 'chiller'
        LEFT JOIN core.entity_tag et_ahu ON e.id = et_ahu.entity_id
        LEFT JOIN core.tag_def td_ahu ON et_ahu.tag_id = td_ahu.id AND td_ahu.name = 'ahu'
        LEFT JOIN core.entity_tag et_vav ON e.id = et_vav.entity_id
        LEFT JOIN core.tag_def td_vav ON et_vav.tag_id = td_vav.id AND td_vav.name = 'vav'
        LEFT JOIN core.entity_tag et_meter ON e.id = et_meter.entity_id
        LEFT JOIN core.tag_def td_meter ON et_meter.tag_id = td_meter.id AND td_meter.name = 'meter'
        WHERE et_equip.value_b = true
        ORDER BY e.id
    """
    
    equipment = db.execute_query(query)
    
    # Remove duplicates and clean up
    unique_equipment = {}
    for equip in equipment:
        entity_id = equip['entity_id']
        if entity_id not in unique_equipment:
            unique_equipment[entity_id] = equip
        elif equip['equip_id'] and not unique_equipment[entity_id]['equip_id']:
            unique_equipment[entity_id]['equip_id'] = equip['equip_id']
        elif equip['equip_name'] and not unique_equipment[entity_id]['equip_name']:
            unique_equipment[entity_id]['equip_name'] = equip['equip_name']
            
    return list(unique_equipment.values())


def get_status_points_for_equipment(db: DatabaseConnection, equip_id: str) -> List[Dict[str, Any]]:
    """Get status points for specific equipment.
    
    Args:
        db: Database connection instance
        equip_id: Equipment ID string
        
    Returns:
        List of status point dictionaries
    """
    query = """
        SELECT 
            p.id as point_entity_id,
            et_id.value_s as point_id,
            et_name.value_s as point_name,
            et_kind.value_s as point_kind,
            CASE 
                WHEN et_sensor.value_b = true THEN 'sensor'
                WHEN et_cmd.value_b = true THEN 'cmd'
                ELSE 'unknown'
            END as point_type
        FROM core.entity p
        JOIN core.entity_tag et_point ON p.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id AND td_point.name = 'point'
        JOIN core.entity_tag et_equipref ON p.id = et_equipref.entity_id
        JOIN core.tag_def td_equipref ON et_equipref.tag_id = td_equipref.id AND td_equipref.name = 'equipRef'
        LEFT JOIN core.entity_tag et_id ON p.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity_tag et_name ON p.id = et_name.entity_id
        LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
        LEFT JOIN core.entity_tag et_kind ON p.id = et_kind.entity_id
        LEFT JOIN core.tag_def td_kind ON et_kind.tag_id = td_kind.id AND td_kind.name = 'kind'
        LEFT JOIN core.entity_tag et_sensor ON p.id = et_sensor.entity_id
        LEFT JOIN core.tag_def td_sensor ON et_sensor.tag_id = td_sensor.id AND td_sensor.name = 'sensor'
        LEFT JOIN core.entity_tag et_cmd ON p.id = et_cmd.entity_id
        LEFT JOIN core.tag_def td_cmd ON et_cmd.tag_id = td_cmd.id AND td_cmd.name = 'cmd'
        WHERE et_point.value_b = true 
        AND et_equipref.value_s = %s
        AND (et_id.value_s LIKE '%status%' OR et_name.value_s LIKE '%Status%')
        ORDER BY p.id
    """
    
    return db.execute_query(query, (equip_id,))


def get_current_values_for_points(db: DatabaseConnection, point_entity_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Get current values for list of point entity IDs.
    
    Args:
        db: Database connection instance
        point_entity_ids: List of point entity IDs
        
    Returns:
        Dictionary mapping entity_id to current value data
    """
    if not point_entity_ids:
        return {}
    
    placeholders = ','.join(['%s'] * len(point_entity_ids))
    query = f"""
        SELECT 
            entity_id,
            ts,
            value_n,
            value_b,
            value_s,
            value_ts,
            status
        FROM core.values_demo_current 
        WHERE entity_id IN ({placeholders})
    """
    
    results = db.execute_query(query, tuple(point_entity_ids))
    
    return {row['entity_id']: dict(row) for row in results}


def check_recent_values(db: DatabaseConnection, point_entity_ids: List[int], hours_back: int = 24) -> Dict[int, Dict[str, Any]]:
    """Check for recent values in time-series table.
    
    Args:
        db: Database connection instance
        point_entity_ids: List of point entity IDs
        hours_back: How many hours back to check
        
    Returns:
        Dictionary with recent value statistics
    """
    if not point_entity_ids:
        return {}
    
    since_time = datetime.now() - timedelta(hours=hours_back)
    placeholders = ','.join(['%s'] * len(point_entity_ids))
    
    query = f"""
        SELECT 
            entity_id,
            COUNT(*) as value_count,
            MAX(ts) as latest_ts,
            MIN(ts) as earliest_ts,
            COUNT(DISTINCT status) as status_variety,
            array_agg(DISTINCT status) as statuses
        FROM core.values_demo 
        WHERE entity_id IN ({placeholders})
        AND ts >= %s
        GROUP BY entity_id
    """
    
    params = tuple(point_entity_ids) + (since_time,)
    results = db.execute_query(query, params)
    
    return {row['entity_id']: dict(row) for row in results}


def validate_equipment_status(db: DatabaseConnection):
    """Validate equipment status and current values.
    
    Args:
        db: Database connection instance
        
    Returns:
        Dictionary with validation results
    """
    results = {
        'equipment_count': 0,
        'equipment_with_status_points': 0,
        'status_points_with_current_values': 0,
        'status_points_with_recent_data': 0,
        'equipment_details': [],
        'issues': []
    }
    
    # Get all equipment
    equipment_list = get_equipment_list(db)
    results['equipment_count'] = len(equipment_list)
    
    print(f"Found {len(equipment_list)} equipment entities to check...")
    
    for equip in equipment_list:
        equip_detail = {
            'entity_id': equip['entity_id'],
            'equip_id': equip['equip_id'],
            'equip_name': equip['equip_name'],
            'equip_type': equip['equip_type'],
            'status_points': [],
            'has_status_points': False,
            'status_points_with_current_values': 0,
            'status_points_with_recent_data': 0
        }
        
        # Get status points for this equipment
        if equip['equip_id']:
            status_points = get_status_points_for_equipment(db, equip['equip_id'])
            equip_detail['status_points'] = status_points
            equip_detail['has_status_points'] = len(status_points) > 0
            
            if equip_detail['has_status_points']:
                results['equipment_with_status_points'] += 1
                
                # Check current values for status points
                point_ids = [sp['point_entity_id'] for sp in status_points]
                current_values = get_current_values_for_points(db, point_ids)
                recent_values = check_recent_values(db, point_ids)
                
                for sp in status_points:
                    point_id = sp['point_entity_id']
                    sp['has_current_value'] = point_id in current_values
                    sp['current_value_data'] = current_values.get(point_id)
                    sp['has_recent_data'] = point_id in recent_values
                    sp['recent_data_stats'] = recent_values.get(point_id)
                    
                    if sp['has_current_value']:
                        equip_detail['status_points_with_current_values'] += 1
                        results['status_points_with_current_values'] += 1
                        
                    if sp['has_recent_data']:
                        equip_detail['status_points_with_recent_data'] += 1
                        results['status_points_with_recent_data'] += 1
        
        results['equipment_details'].append(equip_detail)
        
        # Check for issues
        if not equip_detail['has_status_points']:
            results['issues'].append(f"Equipment {equip['equip_id']} ({equip['equip_name']}) has no status points")
        elif equip_detail['status_points_with_current_values'] == 0:
            results['issues'].append(f"Equipment {equip['equip_id']} ({equip['equip_name']}) status points have no current values")
    
    return results


def print_validation_results(results: Dict[str, Any]):
    """Print detailed validation results."""
    print("\n" + "="*60)
    print("EQUIPMENT STATUS VALIDATION RESULTS")
    print("="*60)
    
    # Summary
    print(f"Total equipment entities: {results['equipment_count']}")
    print(f"Equipment with status points: {results['equipment_with_status_points']}")
    print(f"Status points with current values: {results['status_points_with_current_values']}")
    print(f"Status points with recent data: {results['status_points_with_recent_data']}")
    
    # Equipment details
    print("\n" + "="*60)
    print("EQUIPMENT DETAILS")
    print("="*60)
    
    for equip in results['equipment_details']:
        print(f"\nEquipment: {equip['equip_name']} ({equip['equip_id']})")
        print(f"  Type: {equip['equip_type']}")
        print(f"  Entity ID: {equip['entity_id']}")
        print(f"  Status points found: {len(equip['status_points'])}")
        
        if equip['status_points']:
            print(f"  Status points with current values: {equip['status_points_with_current_values']}")
            print(f"  Status points with recent data: {equip['status_points_with_recent_data']}")
            
            for sp in equip['status_points']:
                print(f"    - {sp['point_name']} ({sp['point_id']})")
                print(f"      Type: {sp['point_type']}, Kind: {sp['point_kind']}")
                
                if sp['has_current_value']:
                    cv = sp['current_value_data']
                    value = cv.get('value_b') if cv.get('value_b') is not None else cv.get('value_n') if cv.get('value_n') is not None else cv.get('value_s')
                    print(f"      Current value: {value} (status: {cv.get('status')}, ts: {cv.get('ts')})")
                else:
                    print(f"      Current value: MISSING")
                
                if sp['has_recent_data']:
                    rd = sp['recent_data_stats']
                    print(f"      Recent data: {rd['value_count']} values, latest: {rd['latest_ts']}")
                else:
                    print(f"      Recent data: NONE")
        else:
            print("  No status points found!")
    
    # Issues
    print("\n" + "="*60)
    print("ISSUES FOUND")
    print("="*60)
    
    if results['issues']:
        for issue in results['issues']:
            print(f"- {issue}")
    else:
        print("No issues found!")
    
    # Overall assessment
    print("\n" + "="*60)
    print("OVERALL ASSESSMENT")
    print("="*60)
    
    if results['equipment_count'] == 0:
        print("❌ CRITICAL: No equipment found in database")
    elif results['equipment_with_status_points'] == 0:
        print("❌ CRITICAL: No equipment has status points")
    elif results['status_points_with_current_values'] == 0:
        print("❌ CRITICAL: No status points have current values")
    else:
        coverage = (results['status_points_with_current_values'] / 
                   sum(len(eq['status_points']) for eq in results['equipment_details'])) * 100
        print(f"✅ Status point current value coverage: {coverage:.1f}%")
        
        if coverage < 50:
            print("⚠️  WARNING: Low current value coverage")
        elif coverage < 90:
            print("⚠️  WARNING: Moderate current value coverage")
        else:
            print("✅ Good current value coverage")


def main():
    """Main validation function."""
    logger.info("Starting equipment status validation...")
    
    try:
        # Load database configuration
        db_config = load_database_config()
        logger.info(f"Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Create database connection
        db = DatabaseConnection(db_config)
        
        # Validate equipment status
        results = validate_equipment_status(db)
        
        # Print results
        print_validation_results(results)
        
        # Close connection
        db.close()
        
        return results
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()