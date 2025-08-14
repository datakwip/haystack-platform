#!/usr/bin/env python3
"""Comprehensive validation script to check current values and historical data for ALL points."""

import logging
import sys
import os
import yaml
from datetime import datetime, timedelta

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


def validate_all_points_data(db: DatabaseConnection):
    """Comprehensive validation of all points data."""
    
    print("=== COMPREHENSIVE POINTS DATA VALIDATION ===\n")
    
    # 1. Count total points
    query = """
        SELECT COUNT(*) as total_points
        FROM core.entity e
        JOIN core.entity_tag et ON e.id = et.entity_id
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'point' AND et.value_b = true
    """
    result = db.execute_query(query)
    total_points = result[0]['total_points']
    print(f"Total point entities: {total_points}")
    
    # 2. Count points with current values
    query = """
        SELECT COUNT(*) as points_with_current
        FROM core.entity e
        JOIN core.entity_tag et ON e.id = et.entity_id
        JOIN core.tag_def td ON et.tag_id = td.id
        JOIN core.values_demo_current cv ON e.id = cv.entity_id
        WHERE td.name = 'point' AND et.value_b = true
    """
    result = db.execute_query(query)
    points_with_current = result[0]['points_with_current']
    print(f"Points with current values: {points_with_current}")
    print(f"Current value coverage: {(points_with_current/total_points*100):.1f}%")
    
    # 3. Count points with historical data (last 24 hours)
    since_time = datetime.now() - timedelta(hours=24)
    query = """
        SELECT COUNT(DISTINCT entity_id) as points_with_history
        FROM core.values_demo
        WHERE ts >= %s
    """
    result = db.execute_query(query, (since_time,))
    points_with_history = result[0]['points_with_history']
    print(f"Points with historical data (24h): {points_with_history}")
    print(f"Historical data coverage: {(points_with_history/total_points*100):.1f}%")
    
    # 4. Points missing current values
    query = """
        SELECT 
            e.id as entity_id,
            et_id.value_s as point_id,
            et_name.value_s as point_name,
            et_equipref.value_s as equip_ref
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        LEFT JOIN core.entity_tag et_id ON e.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity_tag et_name ON e.id = et_name.entity_id
        LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
        LEFT JOIN core.entity_tag et_equipref ON e.id = et_equipref.entity_id
        LEFT JOIN core.tag_def td_equipref ON et_equipref.tag_id = td_equipref.id AND td_equipref.name = 'equipRef'
        LEFT JOIN core.values_demo_current cv ON e.id = cv.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND cv.entity_id IS NULL
        ORDER BY et_equipref.value_s, et_id.value_s
        LIMIT 20
    """
    missing_current = db.execute_query(query)
    
    if missing_current:
        print(f"\n=== POINTS MISSING CURRENT VALUES ({len(missing_current)} shown, max 20) ===")
        for point in missing_current:
            print(f"  {point['point_id']} ({point['point_name']}) - Equipment: {point['equip_ref']}")
    
    # 5. Points missing historical data
    query = """
        SELECT 
            e.id as entity_id,
            et_id.value_s as point_id,
            et_name.value_s as point_name,
            et_equipref.value_s as equip_ref
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        LEFT JOIN core.entity_tag et_id ON e.id = et_id.entity_id
        LEFT JOIN core.tag_def td_id ON et_id.tag_id = td_id.id AND td_id.name = 'id'
        LEFT JOIN core.entity_tag et_name ON e.id = et_name.entity_id
        LEFT JOIN core.tag_def td_name ON et_name.tag_id = td_name.id AND td_name.name = 'dis'
        LEFT JOIN core.entity_tag et_equipref ON e.id = et_equipref.entity_id
        LEFT JOIN core.tag_def td_equipref ON et_equipref.tag_id = td_equipref.id AND td_equipref.name = 'equipRef'
        LEFT JOIN (
            SELECT DISTINCT entity_id 
            FROM core.values_demo 
            WHERE ts >= %s
        ) hd ON e.id = hd.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND hd.entity_id IS NULL
        ORDER BY et_equipref.value_s, et_id.value_s
        LIMIT 20
    """
    missing_history = db.execute_query(query, (since_time,))
    
    if missing_history:
        print(f"\n=== POINTS MISSING HISTORICAL DATA ({len(missing_history)} shown, max 20) ===")
        for point in missing_history:
            print(f"  {point['point_id']} ({point['point_name']}) - Equipment: {point['equip_ref']}")
    
    # 6. Data coverage by equipment type
    query = """
        SELECT 
            et_equipref.value_s as equipment_id,
            COUNT(*) as total_points,
            COUNT(cv.entity_id) as points_with_current,
            COUNT(hd.entity_id) as points_with_history
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        LEFT JOIN core.entity_tag et_equipref ON e.id = et_equipref.entity_id
        LEFT JOIN core.tag_def td_equipref ON et_equipref.tag_id = td_equipref.id AND td_equipref.name = 'equipRef'
        LEFT JOIN core.values_demo_current cv ON e.id = cv.entity_id
        LEFT JOIN (
            SELECT DISTINCT entity_id 
            FROM core.values_demo 
            WHERE ts >= %s
        ) hd ON e.id = hd.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        GROUP BY et_equipref.value_s
        ORDER BY et_equipref.value_s
    """
    equipment_coverage = db.execute_query(query, (since_time,))
    
    print(f"\n=== DATA COVERAGE BY EQUIPMENT ===")
    print(f"{'Equipment':<25} {'Total':<8} {'Current':<8} {'History':<8} {'Curr %':<8} {'Hist %':<8}")
    print("-" * 70)
    
    for equip in equipment_coverage:
        equip_id = equip['equipment_id'] or 'Unknown'
        curr_pct = (equip['points_with_current'] / equip['total_points'] * 100) if equip['total_points'] > 0 else 0
        hist_pct = (equip['points_with_history'] / equip['total_points'] * 100) if equip['total_points'] > 0 else 0
        
        print(f"{equip_id:<25} {equip['total_points']:<8} {equip['points_with_current']:<8} {equip['points_with_history']:<8} {curr_pct:<7.1f}% {hist_pct:<7.1f}%")
    
    # 7. Sample current values by data type
    query = """
        SELECT 
            'Boolean' as data_type,
            COUNT(*) as count,
            COUNT(CASE WHEN cv.value_b IS NOT NULL THEN 1 END) as with_values
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        JOIN core.entity_tag et_kind ON e.id = et_kind.entity_id
        JOIN core.tag_def td_kind ON et_kind.tag_id = td_kind.id
        LEFT JOIN core.values_demo_current cv ON e.id = cv.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND td_kind.name = 'kind' AND et_kind.value_s = 'Bool'
        
        UNION ALL
        
        SELECT 
            'Number' as data_type,
            COUNT(*) as count,
            COUNT(CASE WHEN cv.value_n IS NOT NULL THEN 1 END) as with_values
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        JOIN core.entity_tag et_kind ON e.id = et_kind.entity_id
        JOIN core.tag_def td_kind ON et_kind.tag_id = td_kind.id
        LEFT JOIN core.values_demo_current cv ON e.id = cv.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND td_kind.name = 'kind' AND et_kind.value_s = 'Number'
        
        UNION ALL
        
        SELECT 
            'String' as data_type,
            COUNT(*) as count,
            COUNT(CASE WHEN cv.value_s IS NOT NULL THEN 1 END) as with_values
        FROM core.entity e
        JOIN core.entity_tag et_point ON e.id = et_point.entity_id
        JOIN core.tag_def td_point ON et_point.tag_id = td_point.id
        JOIN core.entity_tag et_kind ON e.id = et_kind.entity_id
        JOIN core.tag_def td_kind ON et_kind.tag_id = td_kind.id
        LEFT JOIN core.values_demo_current cv ON e.id = cv.entity_id
        WHERE td_point.name = 'point' AND et_point.value_b = true
        AND td_kind.name = 'kind' AND et_kind.value_s = 'Str'
    """
    
    data_types = db.execute_query(query)
    
    print(f"\n=== DATA COVERAGE BY TYPE ===")
    print(f"{'Data Type':<10} {'Total Points':<12} {'With Values':<12} {'Coverage':<10}")
    print("-" * 50)
    
    for dt in data_types:
        coverage = (dt['with_values'] / dt['count'] * 100) if dt['count'] > 0 else 0
        print(f"{dt['data_type']:<10} {dt['count']:<12} {dt['with_values']:<12} {coverage:<9.1f}%")
    
    # 8. Historical data volume check
    query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT entity_id) as unique_points,
            MIN(ts) as earliest_data,
            MAX(ts) as latest_data,
            AVG(EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts)))/3600) as hours_span
        FROM core.values_demo
        WHERE ts >= %s
    """
    
    volume_stats = db.execute_query(query, (since_time,))[0]
    
    print(f"\n=== HISTORICAL DATA VOLUME (24h) ===")
    print(f"Total records: {volume_stats['total_records']:,}")
    print(f"Unique points with data: {volume_stats['unique_points']}")
    print(f"Data time span: {volume_stats['earliest_data']} to {volume_stats['latest_data']}")
    
    if volume_stats['total_records'] > 0:
        avg_records_per_point = volume_stats['total_records'] / volume_stats['unique_points']
        print(f"Average records per point: {avg_records_per_point:.1f}")
    
    # 9. Overall assessment
    print(f"\n=== OVERALL ASSESSMENT ===")
    
    current_coverage = (points_with_current / total_points * 100) if total_points > 0 else 0
    history_coverage = (points_with_history / total_points * 100) if total_points > 0 else 0
    
    print(f"Current Values Coverage: {current_coverage:.1f}%")
    if current_coverage >= 90:
        print("✅ EXCELLENT: Most points have current values")
    elif current_coverage >= 70:
        print("⚠️  GOOD: Majority of points have current values") 
    elif current_coverage >= 50:
        print("⚠️  FAIR: Some points missing current values")
    else:
        print("❌ POOR: Many points missing current values")
    
    print(f"Historical Data Coverage: {history_coverage:.1f}%")
    if history_coverage >= 90:
        print("✅ EXCELLENT: Most points have recent historical data")
    elif history_coverage >= 70:
        print("⚠️  GOOD: Majority of points have recent historical data")
    elif history_coverage >= 50:
        print("⚠️  FAIR: Some points missing recent historical data")
    else:
        print("❌ POOR: Many points missing recent historical data")
    
    if current_coverage < 100 or history_coverage < 100:
        print(f"\n⚠️  RECOMMENDATION: Review data generation and loading processes")
        print(f"   - Check time-series data generators")
        print(f"   - Verify current value table updates")
        print(f"   - Review point configuration")


def main():
    """Main validation function."""
    try:
        db_config = load_database_config()
        print(f"Connecting to database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        db = DatabaseConnection(db_config)
        validate_all_points_data(db)
        db.close()
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()