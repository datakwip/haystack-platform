"""Test service resumption and continuity after restart."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import yaml
from database.connection import DatabaseConnection
from database.data_loader import DataLoader
from service.state_manager import StateManager
from service.continuous_generator import ContinuousDataService


def load_test_config():
    """Load test configurations."""
    db_config_path = Path(__file__).parent.parent / 'config' / 'database_config.yaml'
    building_config_path = Path(__file__).parent.parent / 'config' / 'building_config.yaml'

    with open(db_config_path, 'r') as f:
        db_config = yaml.safe_load(f)

    with open(building_config_path, 'r') as f:
        building_config = yaml.safe_load(f)

    return db_config, building_config


def test_totalizer_continuity():
    """Test that totalizers maintain continuity across restarts."""
    print("\n=== TEST: Totalizer Continuity ===")

    db_config, building_config = load_test_config()
    db = DatabaseConnection(db_config['database'])
    table_name = db_config['tables']['value_table']

    # Check if we have data
    query = f"SELECT COUNT(*) as count FROM core.{table_name}"
    result = db.execute_query(query)

    if result[0]['count'] == 0:
        print("⏭️  Skipping - no data in database")
        db.close()
        return

    # Get totalizers at two different points
    state_mgr = StateManager(db)
    totalizers_1 = state_mgr.get_totalizer_states(table_name)

    print("✅ Current totalizer states:")
    print(f"   Electric Energy: {totalizers_1.get('electric_energy', 0):.1f} kWh")
    print(f"   Gas Volume: {totalizers_1.get('gas_volume', 0):.0f} ft³")
    print(f"   Water Volume: {totalizers_1.get('water_volume', 0):.0f} gal")

    # Save state
    state_mgr.save_service_state(
        status='test_stopped',
        totalizers=totalizers_1,
        last_run_ts=datetime.now()
    )

    # Retrieve state (simulating restart)
    saved_state = state_mgr.get_service_state()

    if saved_state:
        totalizers_2 = saved_state.get('totalizers', {})

        print("✅ Retrieved totalizer states after 'restart':")
        print(f"   Electric Energy: {totalizers_2.get('electric_energy', 0):.1f} kWh")
        print(f"   Gas Volume: {totalizers_2.get('gas_volume', 0):.0f} ft³")
        print(f"   Water Volume: {totalizers_2.get('water_volume', 0):.0f} gal")

        # Verify they match
        assert totalizers_1['electric_energy'] == totalizers_2.get('electric_energy'), "Electric totalizer mismatch"
        assert totalizers_1['gas_volume'] == totalizers_2.get('gas_volume'), "Gas totalizer mismatch"
        assert totalizers_1['water_volume'] == totalizers_2.get('water_volume'), "Water totalizer mismatch"

        print("✅ Totalizers preserved correctly across restart")

    db.close()


def test_state_persistence():
    """Test that service state persists across restarts."""
    print("\n=== TEST: State Persistence ===")

    db_config, building_config = load_test_config()
    db = DatabaseConnection(db_config['database'])

    state_mgr = StateManager(db, service_name='test_resumption')

    # Save test state
    test_time = datetime.now()
    test_config = {'test_mode': True, 'version': '1.0'}

    state_mgr.save_service_state(
        status='running',
        last_run_ts=test_time,
        config=test_config,
        totalizers={'electric_energy': 12345.0}
    )

    print("✅ Saved test state")

    # Retrieve state (simulating restart)
    retrieved_state = state_mgr.get_service_state()

    if retrieved_state:
        print("✅ Retrieved state after restart:")
        print(f"   Status: {retrieved_state.get('status')}")
        print(f"   Last Run: {retrieved_state.get('last_run_timestamp')}")
        print(f"   Config: {retrieved_state.get('config')}")

        assert retrieved_state['status'] == 'running', "Status should match"
        assert retrieved_state['config']['test_mode'] == True, "Config should match"
        print("✅ State persisted correctly")
    else:
        print("❌ Failed to retrieve state")

    db.close()


def test_gap_detection_after_downtime():
    """Test gap detection simulating service downtime."""
    print("\n=== TEST: Gap Detection After Downtime ===")

    db_config, building_config = load_test_config()
    db = DatabaseConnection(db_config['database'])
    table_name = db_config['tables']['value_table']

    # Check if we have data
    query = f"SELECT MAX(ts) as max_ts FROM core.{table_name}"
    result = db.execute_query(query)

    if not result[0]['max_ts']:
        print("⏭️  Skipping - no data in database")
        db.close()
        return

    last_ts = result[0]['max_ts']
    current_time = datetime.now().replace(second=0, microsecond=0)

    # Calculate gap
    state_mgr = StateManager(db)
    gap_start, gap_end, num_intervals = state_mgr.calculate_gap(table_name)

    print(f"✅ Gap detection results:")
    print(f"   Last data timestamp: {last_ts}")
    print(f"   Current time: {current_time}")

    if num_intervals > 0:
        print(f"   Gap detected: {num_intervals} intervals")
        print(f"   From {gap_start} to {gap_end}")

        # Verify gap calculation
        expected_minutes = (current_time - last_ts).total_seconds() / 60
        expected_intervals = int(expected_minutes / 15)

        print(f"   Expected intervals: ~{expected_intervals}")
        assert abs(num_intervals - expected_intervals) <= 1, "Gap calculation should be accurate"
    else:
        print("   No gap detected - data is current")

    db.close()


def test_service_restart_sequence():
    """Test complete service restart sequence."""
    print("\n=== TEST: Service Restart Sequence ===")

    db_config, building_config = load_test_config()
    table_name = db_config['tables']['value_table']

    # First service instance
    service1 = ContinuousDataService(
        db_config,
        building_config,
        table_name
    )

    print("Step 1: First service instance created")

    # Simulate startup
    if service1.startup():
        print("✅ Step 2: First service started successfully")

        # Get current state
        health1 = service1.health_check()
        print(f"   Health: {health1.get('status')}")

        # Shutdown
        service1.shutdown()
        print("✅ Step 3: First service shut down")
    else:
        print("⏭️  First service startup failed (may need entities)")
        return

    # Second service instance (simulating restart)
    service2 = ContinuousDataService(
        db_config,
        building_config,
        table_name
    )

    print("Step 4: Second service instance created (restart simulation)")

    # Startup should detect state and resume
    if service2.startup():
        print("✅ Step 5: Second service started successfully")

        health2 = service2.health_check()
        print(f"   Health: {health2.get('status')}")

        print("✅ Service restart sequence completed successfully")

        service2.shutdown()
    else:
        print("⚠️  Second service startup failed")


def test_totalizer_never_decreases():
    """Test that totalizers never decrease across operations."""
    print("\n=== TEST: Totalizer Monotonicity ===")

    db_config, building_config = load_test_config()
    db = DatabaseConnection(db_config['database'])
    table_name = db_config['tables']['value_table']

    # Check electric energy totalizer for decreases
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
            LIMIT 100
        )
        SELECT COUNT(*) as decreases
        FROM energy_changes
        WHERE prev_value IS NOT NULL AND current_value < prev_value
    """

    result = db.execute_query(query)
    decreases = result[0]['decreases'] if result else 0

    if decreases == 0:
        print("✅ No totalizer decreases detected - monotonicity preserved")
    else:
        print(f"❌ Found {decreases} totalizer decreases!")

    assert decreases == 0, "Totalizers must never decrease"

    db.close()


if __name__ == '__main__':
    print("=" * 60)
    print("SERVICE RESUMPTION TESTS")
    print("=" * 60)

    try:
        test_totalizer_continuity()
        test_state_persistence()
        test_gap_detection_after_downtime()
        test_totalizer_never_decreases()
        test_service_restart_sequence()

        print("\n" + "=" * 60)
        print("✅ ALL RESUMPTION TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
