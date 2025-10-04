"""Validate data continuity and detect gaps."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import yaml
from database.connection import DatabaseConnection
from service.state_manager import StateManager
from service.gap_filler import GapFiller


def load_config():
    """Load configurations."""
    db_config_path = Path(__file__).parent.parent / 'config' / 'database_config.yaml'
    building_config_path = Path(__file__).parent.parent / 'config' / 'building_config.yaml'

    with open(db_config_path, 'r') as f:
        db_config = yaml.safe_load(f)

    with open(building_config_path, 'r') as f:
        building_config = yaml.safe_load(f)

    return db_config, building_config


def load_entity_map(db: DatabaseConnection):
    """Load entity map from database."""
    query = """
        SELECT e.id, et_id.value_s as entity_name
        FROM core.entity e
        JOIN core.entity_tag et_id ON e.id = et_id.entity_id
        JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
        WHERE td_id.name = 'id'
    """
    result = db.execute_query(query)
    return {row['entity_name']: row['id'] for row in result if row['entity_name']}


def validate_no_current_gaps(db: DatabaseConnection, table_name: str = 'values_demo') -> bool:
    """Validate there are no gaps from last data to present."""
    print("\n=== Validating Current Data Status ===")

    state_mgr = StateManager(db)

    gap_start, gap_end, num_intervals = state_mgr.calculate_gap(table_name)

    if num_intervals == 0:
        print("✅ No gaps detected - data is current")
        return True
    else:
        print(f"❌ Gap detected: {num_intervals} intervals")
        print(f"   From: {gap_start}")
        print(f"   To: {gap_end}")
        gap_hours = (gap_end - gap_start).total_seconds() / 3600
        print(f"   Duration: {gap_hours:.1f} hours")
        return False


def validate_historical_continuity(db: DatabaseConnection, table_name: str = 'values_demo',
                                   hours_back: int = 24) -> bool:
    """Validate data continuity over historical period."""
    print(f"\n=== Validating Historical Continuity (last {hours_back} hours) ===")

    # Get time range
    end_time = datetime.now().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours_back)

    # Check if we have any data at all
    query = f"SELECT COUNT(*) as count FROM core.{table_name}"
    result = db.execute_query(query)

    if result[0]['count'] == 0:
        print("ℹ️  No data in database (expected for fresh setup)")
        return True

    # Get actual data range
    query = f"""
        SELECT
            MIN(ts) as min_ts,
            MAX(ts) as max_ts
        FROM core.{table_name}
    """
    result = db.execute_query(query)

    min_ts = result[0]['min_ts']
    max_ts = result[0]['max_ts']

    # Adjust start_time if data doesn't go back that far
    if min_ts and start_time < min_ts:
        start_time = min_ts
        print(f"   Adjusted start to earliest data: {start_time}")

    # Get all timestamps for a sample point
    query = f"""
        SELECT DISTINCT ts
        FROM core.{table_name}
        WHERE ts >= %s AND ts <= %s
        ORDER BY ts
    """
    result = db.execute_query(query, (start_time, end_time))

    if not result:
        print(f"ℹ️  No data in specified range")
        return True

    timestamps = [row['ts'] for row in result]

    # Check for gaps (should be 15 min intervals)
    gaps = []
    expected_interval = timedelta(minutes=15)

    for i in range(1, len(timestamps)):
        actual_interval = timestamps[i] - timestamps[i-1]
        if actual_interval > expected_interval + timedelta(seconds=30):  # Allow some tolerance
            gaps.append({
                'start': timestamps[i-1],
                'end': timestamps[i],
                'duration': actual_interval
            })

    print(f"   Checked {len(timestamps)} timestamps")
    print(f"   Time range: {start_time} to {end_time}")

    if gaps:
        print(f"❌ Found {len(gaps)} gap(s):")
        for gap in gaps[:5]:  # Show first 5
            duration_min = gap['duration'].total_seconds() / 60
            print(f"      {gap['start']} to {gap['end']} ({duration_min:.0f} min)")
        if len(gaps) > 5:
            print(f"      ... and {len(gaps) - 5} more")
        return False
    else:
        print("✅ No gaps detected in historical data")
        return True


def validate_all_points_have_data(db: DatabaseConnection, table_name: str = 'values_demo') -> bool:
    """Validate that all expected points have recent data."""
    print("\n=== Validating All Points Have Data ===")

    # Get count of points that should have data
    query = """
        SELECT COUNT(DISTINCT e.id) as total_points
        FROM core.entity e
        JOIN core.entity_tag et ON e.id = et.entity_id
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'point'
    """
    result = db.execute_query(query)
    total_points = result[0]['total_points']

    if total_points == 0:
        print("ℹ️  No points found in database")
        return True

    # Get count of points with recent data (last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    query = f"""
        SELECT COUNT(DISTINCT v.entity_id) as points_with_data
        FROM core.{table_name} v
        WHERE v.ts >= %s
    """
    result = db.execute_query(query, (one_hour_ago,))
    points_with_data = result[0]['points_with_data']

    print(f"   Total points: {total_points}")
    print(f"   Points with recent data: {points_with_data}")

    coverage_pct = (points_with_data / total_points * 100) if total_points > 0 else 0

    if points_with_data == total_points:
        print(f"✅ All points have recent data (100%)")
        return True
    elif coverage_pct >= 95:
        print(f"⚠️  Most points have data ({coverage_pct:.1f}%)")
        print(f"   Missing data for {total_points - points_with_data} points")
        return True
    else:
        print(f"❌ Low data coverage ({coverage_pct:.1f}%)")
        print(f"   Missing data for {total_points - points_with_data} points")
        return False


def validate_interval_consistency(db: DatabaseConnection, table_name: str = 'values_demo') -> bool:
    """Validate that data intervals are consistent (15 minutes)."""
    print("\n=== Validating Interval Consistency ===")

    # Sample recent intervals
    query = f"""
        WITH intervals AS (
            SELECT
                ts,
                LAG(ts) OVER (ORDER BY ts) as prev_ts,
                EXTRACT(EPOCH FROM (ts - LAG(ts) OVER (ORDER BY ts)))/60 as interval_minutes
            FROM (
                SELECT DISTINCT ts
                FROM core.{table_name}
                ORDER BY ts DESC
                LIMIT 100
            ) recent
        )
        SELECT
            interval_minutes,
            COUNT(*) as count
        FROM intervals
        WHERE interval_minutes IS NOT NULL
        GROUP BY interval_minutes
        ORDER BY count DESC
    """

    result = db.execute_query(query)

    if not result:
        print("ℹ️  Not enough data to check intervals")
        return True

    print("   Interval distribution (last 100 timestamps):")
    expected_interval = 15.0
    total_intervals = sum(row['count'] for row in result)
    correct_intervals = 0

    for row in result:
        interval = float(row['interval_minutes']) if row['interval_minutes'] is not None else 0.0
        count = row['count']
        pct = (count / total_intervals * 100) if total_intervals > 0 else 0

        # Check if close to 15 minutes (allow 1 min tolerance)
        if abs(interval - expected_interval) <= 1.0:
            correct_intervals += count
            print(f"      {interval:.1f} min: {count} occurrences ({pct:.1f}%) ✅")
        else:
            print(f"      {interval:.1f} min: {count} occurrences ({pct:.1f}%) ⚠️")

    correct_pct = (correct_intervals / total_intervals * 100) if total_intervals > 0 else 0

    if correct_pct >= 95:
        print(f"✅ Interval consistency good ({correct_pct:.1f}% at 15 min)")
        return True
    else:
        print(f"❌ Interval consistency poor ({correct_pct:.1f}% at 15 min)")
        return False


def detect_and_report_gaps(db: DatabaseConnection, building_config: dict,
                           table_name: str = 'values_demo', hours_back: int = 48) -> bool:
    """Detect and report all gaps in specified time range."""
    print(f"\n=== Detecting All Gaps (last {hours_back} hours) ===")

    entity_map = load_entity_map(db)

    if not entity_map:
        print("ℹ️  No entities found in database")
        return True

    gap_filler = GapFiller(db, building_config, entity_map, table_name)

    end_time = datetime.now().replace(second=0, microsecond=0)
    start_time = end_time - timedelta(hours=hours_back)

    gaps = gap_filler.detect_gaps(start_time, end_time, interval_minutes=15)

    if not gaps:
        print("✅ No gaps detected in specified time range")
        return True
    else:
        print(f"❌ Found {len(gaps)} gap(s):")

        total_missing_intervals = 0
        for i, gap in enumerate(gaps[:10], 1):  # Show first 10
            duration = gap['end'] - gap['start']
            intervals = gap.get('missing_intervals', duration.total_seconds() / 900)
            total_missing_intervals += intervals

            print(f"\n   Gap {i}:")
            print(f"      Start: {gap['start']}")
            print(f"      End: {gap['end']}")
            print(f"      Duration: {duration}")
            print(f"      Missing intervals: {int(intervals)}")

        if len(gaps) > 10:
            print(f"\n   ... and {len(gaps) - 10} more gaps")

        print(f"\n   Total missing intervals: {int(total_missing_intervals)}")
        total_hours = total_missing_intervals * 15 / 60
        print(f"   Total missing data: {total_hours:.1f} hours")

        return False


def validate_data_summary(db: DatabaseConnection, building_config: dict,
                          table_name: str = 'values_demo') -> bool:
    """Display data summary for validation."""
    print("\n=== Data Summary ===")

    entity_map = load_entity_map(db)

    if not entity_map:
        print("ℹ️  No entities found in database")
        return True

    gap_filler = GapFiller(db, building_config, entity_map, table_name)

    # Get summary for last 24 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)

    summary = gap_filler.get_data_summary(start_time, end_time)

    if summary:
        print(f"   Time range: Last 24 hours")
        print(f"   Total records: {summary.get('total_records', 0):,}")
        print(f"   Unique points: {summary.get('unique_points', 0)}")
        print(f"   Unique timestamps: {summary.get('unique_timestamps', 0)}")
        print(f"   Earliest: {summary.get('earliest')}")
        print(f"   Latest: {summary.get('latest')}")

        # Calculate expected records
        expected_timestamps = 24 * 4  # 4 intervals per hour
        unique_points = summary.get('unique_points', 0)
        expected_records = expected_timestamps * unique_points

        actual_records = summary.get('total_records', 0)

        if expected_records > 0:
            coverage_pct = (actual_records / expected_records * 100)
            print(f"\n   Expected records: {expected_records:,}")
            print(f"   Actual records: {actual_records:,}")
            print(f"   Coverage: {coverage_pct:.1f}%")

            if coverage_pct >= 95:
                print("   ✅ Good data coverage")
                return True
            else:
                print("   ⚠️  Low data coverage")
                return False
    else:
        print("ℹ️  No data in specified range")
        return True

    return True


def main():
    """Run all gap validations."""
    print("=" * 60)
    print("DATA GAP VALIDATION")
    print("=" * 60)

    try:
        db_config, building_config = load_config()
        db = DatabaseConnection(db_config['database'])
        table_name = db_config['tables']['value_table']

        results = []

        # Run all validations
        results.append(("No Current Gaps", validate_no_current_gaps(db, table_name)))
        results.append(("Historical Continuity", validate_historical_continuity(db, table_name, hours_back=24)))
        results.append(("All Points Have Data", validate_all_points_have_data(db, table_name)))
        results.append(("Interval Consistency", validate_interval_consistency(db, table_name)))
        results.append(("Data Summary", validate_data_summary(db, building_config, table_name)))

        # Report gaps (informational, doesn't affect pass/fail)
        print("\n" + "=" * 60)
        detect_and_report_gaps(db, building_config, table_name, hours_back=48)

        db.close()

        # Summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {name}")

        print(f"\nTotal: {passed}/{total} validations passed")

        if passed == total:
            print("\n✅ ALL GAP VALIDATIONS PASSED")
            sys.exit(0)
        else:
            print(f"\n⚠️  {total - passed} VALIDATION(S) FAILED")
            print("\nTo fill gaps, run:")
            print("   python src/main.py --catchup")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
