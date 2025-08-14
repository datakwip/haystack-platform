#!/usr/bin/env python3
"""Simple validation script to check equipment status and current values."""

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
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        return config['database']


def validate_equipment_status_simple(db: DatabaseConnection):
    """Simple validation of equipment status."""
    
    print("=== EQUIPMENT STATUS VALIDATION ===\n")
    
    # 1. Count equipment
    query = """
        SELECT COUNT(DISTINCT e.id) as equip_count
        FROM core.entity e
        JOIN core.entity_tag et ON e.id = et.entity_id
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'equip' AND et.value_b = true
    """
    result = db.execute_query(query)
    equip_count = result[0]['equip_count']
    print(f"Total equipment entities: {equip_count}")
    
    # 2. Count status points
    query = """
        SELECT COUNT(*) as status_point_count
        FROM core.entity p
        JOIN core.entity_tag et_point ON p.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        JOIN core.entity_tag et_id ON p.id = et_id.entity_id
        JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND td_id.name = 'id' AND et_id.value_s LIKE '%status%'
    """
    result = db.execute_query(query)
    status_point_count = result[0]['status_point_count']
    print(f"Status points found: {status_point_count}")
    
    # 3. Count status points with current values
    query = """
        SELECT COUNT(*) as status_with_current
        FROM core.entity p
        JOIN core.entity_tag et_point ON p.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        JOIN core.entity_tag et_id ON p.id = et_id.entity_id
        JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
        JOIN core.values_demo_current cv ON p.id = cv.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND td_id.name = 'id' AND et_id.value_s LIKE '%status%'
    """
    result = db.execute_query(query)
    status_with_current = result[0]['status_with_current']
    print(f"Status points with current values: {status_with_current}")
    
    # 4. Sample status point details
    query = """
        SELECT 
            p.id as entity_id,
            et_id.value_s as point_id,
            et_name.value_s as point_name,
            cv.value_b,
            cv.value_n,
            cv.value_s,
            cv.status,
            cv.ts
        FROM core.entity p
        JOIN core.entity_tag et_point ON p.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        LEFT JOIN core.entity_tag et_id ON p.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity_tag et_name ON p.id = et_name.entity_id
        LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
        LEFT JOIN core.values_demo_current cv ON p.id = cv.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND et_id.value_s LIKE '%status%'
        ORDER BY p.id
        LIMIT 10
    """
    
    status_samples = db.execute_query(query)
    
    print(f"\n=== SAMPLE STATUS POINTS ===")
    for sample in status_samples:
        value = sample['value_b'] if sample['value_b'] is not None else sample['value_n'] if sample['value_n'] is not None else sample['value_s']
        current_status = "HAS VALUE" if value is not None else "NO VALUE"
        print(f"Point: {sample['point_name']} ({sample['point_id']})")
        print(f"  Entity ID: {sample['entity_id']}")
        print(f"  Current Value: {value} (status: {sample['status']})")
        print(f"  Timestamp: {sample['ts']}")
        print(f"  Status: {current_status}")
        print()
    
    # 5. Equipment types and their status coverage
    query = """
        SELECT 
            CASE 
                WHEN et_chiller.value_b THEN 'chiller'
                WHEN et_ahu.value_b THEN 'ahu' 
                WHEN et_vav.value_b THEN 'vav'
                WHEN et_meter.value_b THEN 'meter'
                ELSE 'other'
            END as equip_type,
            COUNT(DISTINCT e.id) as equip_count,
            COUNT(DISTINCT sp.id) as status_points,
            COUNT(DISTINCT cv.entity_id) as status_with_current
        FROM core.entity e
        JOIN core.entity_tag et_equip ON e.id = et_equip.entity_id
        JOIN core.tag_def td_equip ON et_equip.tag_id = td_equip.id AND td_equip.name = 'equip'
        LEFT JOIN core.entity_tag et_chiller ON e.id = et_chiller.entity_id 
        LEFT JOIN core.tag_def td_chiller ON et_chiller.tag_id = td_chiller.id AND td_chiller.name = 'chiller'
        LEFT JOIN core.entity_tag et_ahu ON e.id = et_ahu.entity_id 
        LEFT JOIN core.tag_def td_ahu ON et_ahu.tag_id = td_ahu.id AND td_ahu.name = 'ahu'
        LEFT JOIN core.entity_tag et_vav ON e.id = et_vav.entity_id 
        LEFT JOIN core.tag_def td_vav ON et_vav.tag_id = td_vav.id AND td_vav.name = 'vav'
        LEFT JOIN core.entity_tag et_meter ON e.id = et_meter.entity_id 
        LEFT JOIN core.tag_def td_meter ON et_meter.tag_id = td_meter.id AND td_meter.name = 'meter'
        LEFT JOIN core.entity_tag et_id ON e.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity sp ON sp.id IN (
            SELECT sp_inner.id FROM core.entity sp_inner
            JOIN core.entity_tag et_point ON sp_inner.id = et_point.entity_id
            JOIN core.tag_def td_point ON et_point.tag_id = td_point.id AND td_point.name = 'point'
            JOIN core.entity_tag et_equipref ON sp_inner.id = et_equipref.entity_id
            JOIN core.tag_def td_equipref ON et_equipref.tag_id = td_equipref.id AND td_equipref.name = 'equipRef'
            JOIN core.entity_tag et_sp_id ON sp_inner.id = et_sp_id.entity_id
            JOIN core.tag_def td_sp_id ON et_sp_id.tag_id = td_sp_id.id AND td_sp_id.name = 'id'
            WHERE et_equipref.value_s = et_id.value_s 
            AND et_sp_id.value_s LIKE '%status%'
        )
        LEFT JOIN core.values_demo_current cv ON sp.id = cv.entity_id
        WHERE et_equip.value_b = true
        GROUP BY equip_type
        ORDER BY equip_count DESC
    """
    
    equip_types = db.execute_query(query)
    
    print(f"=== EQUIPMENT TYPE BREAKDOWN ===")
    print(f"{'Type':<10} {'Count':<8} {'Status Pts':<12} {'With Current':<12} {'Coverage':<10}")
    print("-" * 60)
    
    for equip_type in equip_types:
        coverage = 0
        if equip_type['status_points'] > 0:
            coverage = (equip_type['status_with_current'] / equip_type['status_points']) * 100
        
        print(f"{equip_type['equip_type']:<10} {equip_type['equip_count']:<8} {equip_type['status_points']:<12} {equip_type['status_with_current']:<12} {coverage:.1f}%")
    
    # 6. Overall assessment
    print(f"\n=== ASSESSMENT ===")
    if status_point_count == 0:
        print("❌ CRITICAL: No status points found")
    elif status_with_current == 0:
        print("❌ CRITICAL: No status points have current values")
    else:
        coverage = (status_with_current / status_point_count) * 100
        print(f"Status point coverage: {coverage:.1f}%")
        
        if coverage < 50:
            print("❌ POOR: Less than 50% of status points have current values")
        elif coverage < 80:
            print("⚠️  FAIR: Less than 80% of status points have current values")
        else:
            print("✅ GOOD: Most status points have current values")


def main():
    """Main validation function."""
    try:
        db_config = load_database_config()
        db = DatabaseConnection(db_config)
        
        validate_equipment_status_simple(db)
        
        db.close()
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()