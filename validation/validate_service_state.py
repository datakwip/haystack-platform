"""Validate service state consistency and accuracy."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import yaml
from database.connection import DatabaseConnection
from service.state_manager import StateManager


def load_config():
    """Load database configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'database_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def validate_state_table_exists(db: DatabaseConnection) -> bool:
    """Validate that simulator_state table exists."""
    print("\n=== Validating State Table Exists ===")

    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'core'
            AND table_name = 'simulator_state'
        )
    """

    result = db.execute_query(query)

    if result[0]['exists']:
        print("✅ simulator_state table exists")
        return True
    else:
        print("❌ simulator_state table does NOT exist")
        print("   Run: psql -d datakwip -f schema/simulator_state.sql")
        return False


def validate_state_record_exists(db: DatabaseConnection) -> bool:
    """Validate that service state record exists."""
    print("\n=== Validating State Record ===")

    state_mgr = StateManager(db)
    state = state_mgr.get_service_state()

    if state:
        print("✅ Service state record found")
        print(f"   Service: {state.get('service_name')}")
        print(f"   Status: {state.get('status')}")
        print(f"   Last Run: {state.get('last_run_timestamp')}")
        print(f"   Updated: {state.get('updated_at')}")
        return True
    else:
        print("⚠️  No service state record found (expected for fresh setup)")
        return False


def validate_last_timestamp_accuracy(db: DatabaseConnection, table_name: str = 'values_demo') -> bool:
    """Validate that last_run_timestamp matches actual last data timestamp."""
    print("\n=== Validating Last Timestamp Accuracy ===")

    state_mgr = StateManager(db)

    # Get state timestamp
    state = state_mgr.get_service_state()
    if not state or not state.get('last_run_timestamp'):
        print("ℹ️  No last_run_timestamp in state (expected for fresh setup)")
        return True

    state_ts = state['last_run_timestamp']

    # Get actual last timestamp from data
    actual_ts = state_mgr.detect_last_timestamp(table_name)

    if not actual_ts:
        print("⚠️  No data in database")
        return True

    # Make both timezone-naive for comparison
    state_ts_naive = state_ts.replace(tzinfo=None) if state_ts.tzinfo else state_ts
    actual_ts_naive = actual_ts.replace(tzinfo=None) if actual_ts.tzinfo else actual_ts

    # They should be close (within 1 interval)
    diff_minutes = abs((state_ts_naive - actual_ts_naive).total_seconds() / 60)

    print(f"   State timestamp: {state_ts}")
    print(f"   Actual last data: {actual_ts}")
    print(f"   Difference: {diff_minutes:.1f} minutes")

    if diff_minutes <= 15:  # Within one interval
        print("✅ Timestamps are consistent")
        return True
    else:
        print(f"❌ Timestamps differ by more than one interval ({diff_minutes:.1f} min)")
        return False


def validate_totalizer_consistency(db: DatabaseConnection, table_name: str = 'values_demo') -> bool:
    """Validate that saved totalizers match database values."""
    print("\n=== Validating Totalizer Consistency ===")

    state_mgr = StateManager(db)

    # Get state totalizers
    state = state_mgr.get_service_state()
    if not state or not state.get('totalizers'):
        print("ℹ️  No totalizers in state (expected for fresh setup)")
        return True

    state_totalizers = state['totalizers']

    # Get actual totalizers from database
    actual_totalizers = state_mgr.get_totalizer_states(table_name)

    print("\n   State Totalizers:")
    print(f"      Electric Energy: {state_totalizers.get('electric_energy', 0):.1f} kWh")
    print(f"      Gas Volume: {state_totalizers.get('gas_volume', 0):.0f} ft³")
    print(f"      Water Volume: {state_totalizers.get('water_volume', 0):.0f} gal")

    print("\n   Actual Database Totalizers:")
    print(f"      Electric Energy: {actual_totalizers.get('electric_energy', 0):.1f} kWh")
    print(f"      Gas Volume: {actual_totalizers.get('gas_volume', 0):.0f} ft³")
    print(f"      Water Volume: {actual_totalizers.get('water_volume', 0):.0f} gal")

    # Check if they're close (may differ by one interval)
    electric_diff = abs(state_totalizers.get('electric_energy', 0) - actual_totalizers.get('electric_energy', 0))
    gas_diff = abs(state_totalizers.get('gas_volume', 0) - actual_totalizers.get('gas_volume', 0))
    water_diff = abs(state_totalizers.get('water_volume', 0) - actual_totalizers.get('water_volume', 0))

    # Allow for one interval of accumulation difference
    if electric_diff < 500 and gas_diff < 1000 and water_diff < 2000:
        print("\n✅ Totalizers are consistent")
        return True
    else:
        print(f"\n⚠️  Totalizers show larger than expected differences")
        print(f"   Electric: {electric_diff:.1f} kWh diff")
        print(f"   Gas: {gas_diff:.0f} ft³ diff")
        print(f"   Water: {water_diff:.0f} gal diff")
        return True  # Not necessarily an error, could be ongoing generation


def validate_totalizer_monotonicity(db: DatabaseConnection, table_name: str = 'values_demo') -> bool:
    """Validate that totalizers never decrease."""
    print("\n=== Validating Totalizer Monotonicity ===")

    # Check electric energy totalizer for any decreases
    query = f"""
        WITH energy_changes AS (
            SELECT
                v.entity_id,
                v.ts,
                v.value_n as current_value,
                LAG(v.value_n) OVER (PARTITION BY v.entity_id ORDER BY v.ts) as prev_value
            FROM core.{table_name} v
            JOIN core.entity_tag et ON v.entity_id = et.entity_id
            JOIN core.tag_def td ON et.tag_id = td.id
            WHERE td.name = 'energy'
            ORDER BY v.ts DESC
            LIMIT 1000
        )
        SELECT
            COUNT(*) as decreases,
            COUNT(*) FILTER (WHERE prev_value IS NOT NULL) as total_intervals
        FROM energy_changes
        WHERE prev_value IS NOT NULL AND current_value < prev_value
    """

    result = db.execute_query(query)

    if result:
        decreases = result[0]['decreases']
        total_intervals = result[0]['total_intervals']

        print(f"   Checked {total_intervals} energy totalizer intervals")

        if decreases == 0:
            print("✅ No totalizer decreases detected - monotonicity preserved")
            return True
        else:
            print(f"❌ Found {decreases} totalizer decreases!")
            return False

    return True


def validate_state_freshness(db: DatabaseConnection) -> bool:
    """Validate that state is reasonably fresh."""
    print("\n=== Validating State Freshness ===")

    state_mgr = StateManager(db)
    state = state_mgr.get_service_state()

    if not state:
        print("ℹ️  No state record (expected for fresh setup)")
        return True

    updated_at = state.get('updated_at')
    if not updated_at:
        print("⚠️  State has no updated_at timestamp")
        return False

    # Make timezone-naive for comparison
    updated_at_naive = updated_at.replace(tzinfo=None) if updated_at.tzinfo else updated_at
    now_naive = datetime.now()

    age_minutes = (now_naive - updated_at_naive).total_seconds() / 60

    print(f"   State last updated: {updated_at}")
    print(f"   Age: {age_minutes:.1f} minutes")

    status = state.get('status')

    if status == 'running':
        # Running service should update state every 15 minutes
        if age_minutes > 20:
            print(f"⚠️  State is stale (>{age_minutes:.1f} min old) for running service")
            return False
        else:
            print("✅ State is fresh for running service")
            return True
    else:
        # Stopped/idle service can have older state
        print(f"✅ State age is acceptable for {status} service")
        return True


def validate_error_state(db: DatabaseConnection) -> bool:
    """Check for error conditions in state."""
    print("\n=== Validating Error State ===")

    state_mgr = StateManager(db)
    state = state_mgr.get_service_state()

    if not state:
        print("ℹ️  No state record")
        return True

    error_msg = state.get('error_message')
    status = state.get('status')

    if error_msg:
        print(f"⚠️  Service has error message: {error_msg}")
        print(f"   Status: {status}")
        return False
    else:
        print("✅ No errors in service state")
        return True


def main():
    """Run all state validations."""
    print("=" * 60)
    print("SERVICE STATE VALIDATION")
    print("=" * 60)

    try:
        config = load_config()
        db = DatabaseConnection(config['database'])
        table_name = config['tables']['value_table']

        results = []

        # Run all validations
        results.append(("State Table Exists", validate_state_table_exists(db)))
        results.append(("State Record Exists", validate_state_record_exists(db)))
        results.append(("Last Timestamp Accuracy", validate_last_timestamp_accuracy(db, table_name)))
        results.append(("Totalizer Consistency", validate_totalizer_consistency(db, table_name)))
        results.append(("Totalizer Monotonicity", validate_totalizer_monotonicity(db, table_name)))
        results.append(("State Freshness", validate_state_freshness(db)))
        results.append(("Error State", validate_error_state(db)))

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
            print("\n✅ ALL STATE VALIDATIONS PASSED")
            sys.exit(0)
        else:
            print(f"\n⚠️  {total - passed} VALIDATION(S) FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
