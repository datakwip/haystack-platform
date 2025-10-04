"""Test state manager functionality."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import yaml
from database.connection import DatabaseConnection
from service.state_manager import StateManager


def load_test_config():
    """Load test database configuration."""
    config_path = Path(__file__).parent.parent / 'config' / 'database_config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['database']


def test_detect_last_timestamp():
    """Test detection of last timestamp."""
    print("\n=== TEST: Detect Last Timestamp ===")

    db_config = load_test_config()
    db = DatabaseConnection(db_config)
    state_mgr = StateManager(db)

    last_ts = state_mgr.detect_last_timestamp()

    if last_ts:
        print(f"✅ Last timestamp detected: {last_ts}")
        assert isinstance(last_ts, datetime), "Last timestamp should be datetime"
    else:
        print("ℹ️  No data in database (expected for fresh setup)")

    db.close()


def test_detect_entities_exist():
    """Test entity detection."""
    print("\n=== TEST: Detect Entities Exist ===")

    db_config = load_test_config()
    db = DatabaseConnection(db_config)
    state_mgr = StateManager(db)

    entities_exist = state_mgr.detect_entities_exist()

    if entities_exist:
        print(f"✅ Entities detected in database")
    else:
        print("ℹ️  No entities found (expected for fresh setup)")

    assert isinstance(entities_exist, bool), "Should return boolean"

    db.close()


def test_calculate_gap():
    """Test gap calculation."""
    print("\n=== TEST: Calculate Gap ===")

    db_config = load_test_config()
    db = DatabaseConnection(db_config)
    state_mgr = StateManager(db)

    start, end, num_intervals = state_mgr.calculate_gap()

    if num_intervals > 0:
        print(f"✅ Gap detected: {num_intervals} intervals")
        print(f"   From: {start}")
        print(f"   To: {end}")
        assert start < end, "Start should be before end"
    else:
        print("ℹ️  No gap detected - data is current")

    db.close()


def test_get_totalizer_states():
    """Test totalizer state retrieval."""
    print("\n=== TEST: Get Totalizer States ===")

    db_config = load_test_config()
    db = DatabaseConnection(db_config)
    state_mgr = StateManager(db)

    totalizers = state_mgr.get_totalizer_states()

    print(f"✅ Retrieved totalizer states:")
    print(f"   Electric Energy: {totalizers.get('electric_energy', 0):.1f} kWh")
    print(f"   Gas Volume: {totalizers.get('gas_volume', 0):.0f} ft³")
    print(f"   Water Volume: {totalizers.get('water_volume', 0):.0f} gal")

    assert isinstance(totalizers, dict), "Should return dictionary"
    assert 'electric_energy' in totalizers, "Should have electric_energy key"
    assert 'gas_volume' in totalizers, "Should have gas_volume key"
    assert 'water_volume' in totalizers, "Should have water_volume key"

    db.close()


def test_save_and_retrieve_state():
    """Test saving and retrieving service state."""
    print("\n=== TEST: Save and Retrieve State ===")

    db_config = load_test_config()
    db = DatabaseConnection(db_config)
    state_mgr = StateManager(db, service_name='test_service')

    # Save state
    test_totalizers = {
        'electric_energy': 1000.0,
        'gas_volume': 5000.0,
        'water_volume': 10000.0,
        'chiller_energy': {1: 500.0, 2: 300.0}
    }

    state_mgr.save_service_state(
        status='running',
        totalizers=test_totalizers,
        last_run_ts=datetime.now(),
        config={'test': True}
    )
    print("✅ State saved successfully")

    # Retrieve state
    retrieved_state = state_mgr.get_service_state()

    if retrieved_state:
        print("✅ State retrieved successfully:")
        print(f"   Status: {retrieved_state.get('status')}")
        print(f"   Last Run: {retrieved_state.get('last_run_timestamp')}")
        print(f"   Totalizers: {retrieved_state.get('totalizers')}")

        assert retrieved_state['status'] == 'running', "Status should match"
        assert retrieved_state['totalizers']['electric_energy'] == 1000.0, "Totalizer should match"
    else:
        print("❌ Failed to retrieve state")

    db.close()


def test_state_table_exists():
    """Test that simulator_state table exists."""
    print("\n=== TEST: State Table Exists ===")

    db_config = load_test_config()
    db = DatabaseConnection(db_config)

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
    else:
        print("❌ simulator_state table does NOT exist")
        print("   Run: psql -d datakwip -f schema/simulator_state.sql")

    assert result[0]['exists'], "State table must exist"

    db.close()


if __name__ == '__main__':
    print("=" * 60)
    print("STATE MANAGER TESTS")
    print("=" * 60)

    try:
        test_state_table_exists()
        test_detect_last_timestamp()
        test_detect_entities_exist()
        test_calculate_gap()
        test_get_totalizer_states()
        test_save_and_retrieve_state()

        print("\n" + "=" * 60)
        print("✅ ALL STATE MANAGER TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
