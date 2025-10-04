#!/usr/bin/env python3
"""Validation script for data continuity in continuous mode.

Checks for gaps, duplicate timestamps, and totalizer monotonicity.
"""

import logging
import sys
import os
import yaml
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.connection import DatabaseConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_database_config():
    """Load database configuration."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'database_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        return config['database']


def check_data_gaps(db: DatabaseConnection, hours_back: int = 24):
    """Check for gaps in 15-minute intervals."""
    print(f"\n=== CHECKING DATA GAPS (last {hours_back} hours) ===")

    since_time = datetime.now() - timedelta(hours=hours_back)
    query = """
        SELECT DISTINCT ts
        FROM core.values_demo
        WHERE ts >= %s
        ORDER BY ts
    """

    result = db.execute_query(query, (since_time,))
    timestamps = [row['ts'] for row in result]

    if not timestamps:
        print("❌ No data found in specified range")
        return False

    # Check for gaps
    gaps = []
    for i in range(len(timestamps) - 1):
        diff = (timestamps[i+1] - timestamps[i]).total_seconds()
        if diff > 900:  # More than 15 minutes
            gaps.append((timestamps[i], timestamps[i+1], diff/60))

    if gaps:
        print(f"⚠️  Found {len(gaps)} gaps:")
        for start, end, minutes in gaps[:5]:  # Show first 5
            print(f"  {start} to {end} ({minutes:.0f} minutes)")
    else:
        print(f"✅ No gaps detected - continuous 15-minute intervals")

    return len(gaps) == 0


def check_duplicate_timestamps(db: DatabaseConnection):
    """Check for duplicate timestamps per entity."""
    print("\n=== CHECKING DUPLICATE TIMESTAMPS ===")

    query = """
        SELECT entity_id, ts, COUNT(*) as count
        FROM core.values_demo
        GROUP BY entity_id, ts
        HAVING COUNT(*) > 1
        LIMIT 10
    """

    result = db.execute_query(query)

    if result:
        print(f"⚠️  Found {len(result)} duplicate timestamp/entity combinations (showing max 10):")
        for row in result:
            print(f"  Entity {row['entity_id']} at {row['ts']}: {row['count']} records")
        return False
    else:
        print("✅ No duplicate timestamps detected")
        return True


def check_totalizer_monotonicity(db: DatabaseConnection):
    """Verify totalizers only increase (never decrease)."""
    print("\n=== CHECKING TOTALIZER MONOTONICITY ===")

    # Check electric energy
    query = """
        WITH energy_changes AS (
            SELECT
                v.entity_id,
                v.ts,
                v.value_n as current_value,
                LAG(v.value_n) OVER (PARTITION BY v.entity_id ORDER BY v.ts) as prev_value
            FROM core.values_demo v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'energy'
            AND v.ts > NOW() - INTERVAL '7 days'
        )
        SELECT entity_id, ts, current_value, prev_value
        FROM energy_changes
        WHERE prev_value IS NOT NULL
        AND current_value < prev_value
        LIMIT 5
    """

    result = db.execute_query(query)

    if result:
        print(f"❌ Found {len(result)} totalizer decreases (showing max 5):")
        for row in result:
            print(f"  Entity {row['entity_id']} at {row['ts']}: {row['prev_value']} → {row['current_value']}")
        return False
    else:
        print("✅ All totalizers are monotonically increasing")
        return True


def check_interval_consistency(db: DatabaseConnection):
    """Verify 15-minute interval consistency."""
    print("\n=== CHECKING INTERVAL CONSISTENCY ===")

    query = """
        WITH interval_check AS (
            SELECT
                ts,
                LEAD(ts) OVER (ORDER BY ts) as next_ts,
                EXTRACT(EPOCH FROM (LEAD(ts) OVER (ORDER BY ts) - ts))/60 as interval_minutes
            FROM (SELECT DISTINCT ts FROM core.values_demo WHERE ts > NOW() - INTERVAL '24 hours') t
        )
        SELECT
            COUNT(*) as total_intervals,
            COUNT(CASE WHEN interval_minutes = 15 THEN 1 END) as correct_intervals,
            COUNT(CASE WHEN interval_minutes != 15 THEN 1 END) as incorrect_intervals
        FROM interval_check
        WHERE next_ts IS NOT NULL
    """

    result = db.execute_query(query)[0]

    total = result['total_intervals']
    correct = result['correct_intervals']
    incorrect = result['incorrect_intervals']

    if total > 0:
        pct = (correct / total) * 100
        print(f"Total intervals: {total}")
        print(f"Correct (15min): {correct} ({pct:.1f}%)")
        print(f"Incorrect: {incorrect}")

        if pct >= 95:
            print("✅ Interval consistency is good")
            return True
        else:
            print("⚠️  Interval consistency issues detected")
            return False
    else:
        print("❌ No intervals found to check")
        return False


def main():
    """Main validation function."""
    print("=" * 60)
    print("DATA CONTINUITY VALIDATION")
    print("=" * 60)

    try:
        db_config = load_database_config()
        db = DatabaseConnection(db_config)

        results = {
            'gaps': check_data_gaps(db, hours_back=24),
            'duplicates': check_duplicate_timestamps(db),
            'totalizers': check_totalizer_monotonicity(db),
            'intervals': check_interval_consistency(db)
        }

        db.close()

        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        all_passed = all(results.values())

        for check, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{check.upper()}: {status}")

        if all_passed:
            print("\n✅ All continuity checks passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some continuity issues detected")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
