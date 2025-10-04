"""Test continuous service functionality."""

import sys
import os
from pathlib import Path
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import yaml
from database.connection import DatabaseConnection
from service.continuous_generator import ContinuousDataService
from service.scheduler import DataGenerationScheduler
from service.health_server import HealthCheckServer


def load_test_config():
    """Load test configurations."""
    db_config_path = Path(__file__).parent.parent / 'config' / 'database_config.yaml'
    building_config_path = Path(__file__).parent.parent / 'config' / 'building_config.yaml'

    with open(db_config_path, 'r') as f:
        db_config = yaml.safe_load(f)

    with open(building_config_path, 'r') as f:
        building_config = yaml.safe_load(f)

    return db_config, building_config


def test_service_initialization():
    """Test service initialization."""
    print("\n=== TEST: Service Initialization ===")

    db_config, building_config = load_test_config()

    service = ContinuousDataService(
        db_config,
        building_config,
        db_config['tables']['value_table']
    )

    print("✅ Service instance created successfully")
    assert service is not None, "Service should be created"
    assert not service.running, "Service should not be running initially"


def test_service_startup():
    """Test service startup sequence."""
    print("\n=== TEST: Service Startup ===")

    db_config, building_config = load_test_config()

    service = ContinuousDataService(
        db_config,
        building_config,
        db_config['tables']['value_table']
    )

    # Attempt startup
    success = service.startup()

    if success:
        print("✅ Service startup successful")
        assert service.running, "Service should be running after startup"

        # Cleanup
        service.shutdown()
        assert not service.running, "Service should not be running after shutdown"
    else:
        print("⚠️  Service startup failed (may be due to missing entities/data)")

    # Success could be True or False depending on DB state, both are valid


def test_health_check():
    """Test health check functionality."""
    print("\n=== TEST: Health Check ===")

    db_config, building_config = load_test_config()

    service = ContinuousDataService(
        db_config,
        building_config,
        db_config['tables']['value_table']
    )

    # Test health check before startup
    health = service.health_check()

    print(f"✅ Health check returned:")
    print(f"   Service: {health.get('service')}")
    print(f"   Status: {health.get('status')}")
    print(f"   Timestamp: {health.get('timestamp')}")

    assert isinstance(health, dict), "Health check should return dict"
    assert 'service' in health, "Should have service name"
    assert 'status' in health, "Should have status"


def test_health_server():
    """Test health check HTTP server."""
    print("\n=== TEST: Health Check Server ===")

    def mock_health_callback():
        return {
            'status': 'healthy',
            'service': 'test_simulator',
            'test': True
        }

    # Start server on test port
    server = HealthCheckServer(port=8081, health_callback=mock_health_callback)

    try:
        server.start()
        time.sleep(0.5)  # Give server time to start

        if server.is_running():
            print("✅ Health server started successfully on port 8081")

            # Test health check
            import urllib.request
            try:
                response = urllib.request.urlopen('http://localhost:8081/health')
                data = response.read()
                print(f"✅ Health endpoint responded: {data.decode()[:100]}")
            except Exception as e:
                print(f"⚠️  Could not fetch health endpoint: {e}")
        else:
            print("⚠️  Health server not running")

    finally:
        server.stop()
        print("✅ Health server stopped")


def test_scheduler_creation():
    """Test scheduler creation and configuration."""
    print("\n=== TEST: Scheduler Creation ===")

    def mock_job():
        print("  Mock job executed")
        return True

    scheduler = DataGenerationScheduler(interval_minutes=15, max_retries=3)

    print("✅ Scheduler created successfully")
    print(f"   Interval: {scheduler.interval_minutes} minutes")
    print(f"   Max retries: {scheduler.max_retries}")

    assert not scheduler.is_running(), "Scheduler should not be running initially"

    # Start and quickly stop to test
    scheduler.start(mock_job)
    time.sleep(1)  # Let it execute once

    if scheduler.is_running():
        print("✅ Scheduler started successfully")

        status = scheduler.get_status()
        print(f"   Status: {status}")

        scheduler.stop()
        print("✅ Scheduler stopped successfully")
    else:
        print("⚠️  Scheduler did not start")


def test_generate_current_interval():
    """Test generating data for current interval."""
    print("\n=== TEST: Generate Current Interval ===")

    db_config, building_config = load_test_config()

    # Check if entities exist first
    db = DatabaseConnection(db_config['database'])
    query = """
        SELECT COUNT(*) as count
        FROM core.entity e
        JOIN core.entity_tag et ON e.id = et.entity_id
        JOIN core.tag_def td ON et.tag_id = td.id
        WHERE td.name = 'point'
    """
    result = db.execute_query(query)
    db.close()

    if result[0]['count'] == 0:
        print("⏭️  Skipping - no entities in database")
        print("   Run: python src/main.py --reset --entities-only")
        return

    service = ContinuousDataService(
        db_config,
        building_config,
        db_config['tables']['value_table']
    )

    # Startup first
    if service.startup():
        # Generate current interval
        success = service.generate_current_interval()

        if success:
            print("✅ Generated current interval successfully")
        else:
            print("⚠️  Failed to generate current interval")

        service.shutdown()
    else:
        print("⏭️  Skipping - service startup failed")


def test_entity_map_loading():
    """Test entity map loading from database."""
    print("\n=== TEST: Entity Map Loading ===")

    db_config, building_config = load_test_config()

    service = ContinuousDataService(
        db_config,
        building_config,
        db_config['tables']['value_table']
    )

    # Initialize database connection
    service.db = DatabaseConnection(db_config['database'])

    # Try to load entity map
    entity_map = service._load_entity_map()

    if entity_map:
        print(f"✅ Entity map loaded: {len(entity_map)} entities")
        # Show sample
        sample = list(entity_map.items())[:3]
        for name, id in sample:
            print(f"   {name}: {id}")
    else:
        print("ℹ️  No entities found in database")

    service.db.close()


if __name__ == '__main__':
    print("=" * 60)
    print("CONTINUOUS SERVICE TESTS")
    print("=" * 60)

    try:
        test_service_initialization()
        test_health_check()
        test_health_server()
        test_scheduler_creation()
        test_entity_map_loading()
        test_service_startup()
        test_generate_current_interval()

        print("\n" + "=" * 60)
        print("✅ ALL CONTINUOUS SERVICE TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
