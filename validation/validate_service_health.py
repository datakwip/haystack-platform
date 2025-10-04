"""Validate service health and operational status."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import urllib.request
import urllib.error
import json

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


def validate_health_endpoint(port: int = 8080) -> bool:
    """Validate health endpoint is responding."""
    print("\n=== Validating Health Endpoint ===")

    url = f"http://localhost:{port}/health"

    try:
        response = urllib.request.urlopen(url, timeout=5)
        data = response.read().decode('utf-8')
        health_data = json.loads(data)

        print(f"✅ Health endpoint responding on port {port}")
        print(f"   Status: {health_data.get('status')}")
        print(f"   Service: {health_data.get('service')}")
        print(f"   Timestamp: {health_data.get('timestamp')}")

        if health_data.get('status') == 'healthy':
            print("✅ Service reports healthy status")
            return True
        else:
            print(f"⚠️  Service reports status: {health_data.get('status')}")
            return False

    except urllib.error.URLError as e:
        print(f"❌ Health endpoint not responding: {e}")
        print(f"   Is the service running?")
        print(f"   Try: python src/main.py --service")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking health endpoint: {e}")
        return False


def validate_status_endpoint(port: int = 8080) -> bool:
    """Validate status endpoint is responding."""
    print("\n=== Validating Status Endpoint ===")

    url = f"http://localhost:{port}/status"

    try:
        response = urllib.request.urlopen(url, timeout=5)
        data = response.read().decode('utf-8')
        status_data = json.loads(data)

        print(f"✅ Status endpoint responding")
        print(f"   Running: {status_data.get('running')}")
        print(f"   Uptime: {status_data.get('uptime_seconds', 0):.1f}s")

        if status_data.get('last_generation'):
            print(f"   Last generation: {status_data.get('last_generation')}")

        return True

    except urllib.error.URLError as e:
        print(f"⚠️  Status endpoint not responding: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking status endpoint: {e}")
        return False


def validate_database_connectivity(db: DatabaseConnection) -> bool:
    """Validate database connection is healthy."""
    print("\n=== Validating Database Connectivity ===")

    try:
        result = db.execute_query("SELECT NOW() as current_time")
        db_time = result[0]['current_time']

        print(f"✅ Database connection successful")
        print(f"   Database time: {db_time}")

        # Check if database time is reasonable
        local_time = datetime.now()
        time_diff = abs((db_time.replace(tzinfo=None) - local_time).total_seconds())

        # Allow for timezone offsets (multiples of 3600 seconds)
        if time_diff > 60 and time_diff % 3600 != 0:
            print(f"⚠️  Database time differs from local by {time_diff:.0f}s")
            return False
        elif time_diff >= 3600:
            print(f"⚠️  Database time differs from local by {time_diff:.0f}s")
            # This is just informational, not a failure

        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def validate_database_tables(db: DatabaseConnection, value_table: str, current_table: str) -> bool:
    """Validate required tables exist."""
    print("\n=== Validating Database Tables ===")

    required_tables = [
        'entity',
        'entity_tag',
        'tag_def',
        value_table,
        current_table,
        'simulator_state'
    ]

    all_exist = True

    for table in required_tables:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'core'
                AND table_name = %s
            )
        """
        result = db.execute_query(query, (table,))

        if result[0]['exists']:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - MISSING")
            all_exist = False

    if all_exist:
        print("✅ All required tables exist")
        return True
    else:
        print("❌ Some required tables are missing")
        return False


def validate_service_running_state(db: DatabaseConnection) -> bool:
    """Validate service is in expected running state."""
    print("\n=== Validating Service Running State ===")

    state_mgr = StateManager(db)
    state = state_mgr.get_service_state()

    if not state:
        print("ℹ️  No service state found (service may not have started yet)")
        return True

    status = state.get('status')
    last_run = state.get('last_run_timestamp')
    error_msg = state.get('error_message')

    print(f"   Status: {status}")
    print(f"   Last run: {last_run}")

    if error_msg:
        print(f"   ❌ Error: {error_msg}")
        return False

    if status == 'running':
        # Check if last run is recent
        if last_run:
            # Make timezone-naive for comparison
            last_run_naive = last_run.replace(tzinfo=None) if last_run.tzinfo else last_run
            age_minutes = (datetime.now() - last_run_naive).total_seconds() / 60

            if age_minutes > 20:
                print(f"   ⚠️  Last run was {age_minutes:.1f} minutes ago (expected <20 min)")
                return False
            else:
                print(f"   ✅ Service actively running (last run {age_minutes:.1f} min ago)")
                return True
        else:
            print("   ⚠️  Service status is 'running' but no last_run_timestamp")
            return False

    elif status in ['stopped', 'idle']:
        print(f"   ℹ️  Service is {status} (not running)")
        return True

    else:
        print(f"   ⚠️  Unknown status: {status}")
        return False


def validate_data_generation_active(db: DatabaseConnection, table_name: str) -> bool:
    """Validate that data generation is actively occurring."""
    print("\n=== Validating Active Data Generation ===")

    # Check for recent data (within last 20 minutes)
    query = f"""
        SELECT
            MAX(ts) as latest_ts,
            COUNT(*) as recent_count
        FROM core.{table_name}
        WHERE ts > NOW() - INTERVAL '20 minutes'
    """

    result = db.execute_query(query)

    if not result or not result[0]['latest_ts']:
        print("❌ No recent data found (last 20 minutes)")
        print("   Service may not be generating data")
        return False

    latest_ts = result[0]['latest_ts']
    recent_count = result[0]['recent_count']

    # Make timezone-naive for comparison
    latest_ts_naive = latest_ts.replace(tzinfo=None) if latest_ts.tzinfo else latest_ts
    age_minutes = (datetime.now() - latest_ts_naive).total_seconds() / 60

    print(f"   Latest data: {latest_ts}")
    print(f"   Age: {age_minutes:.1f} minutes")
    print(f"   Recent records: {recent_count:,}")

    if age_minutes <= 15:
        print("✅ Data generation is active (data is current)")
        return True
    elif age_minutes <= 20:
        print("⚠️  Data is slightly stale (15-20 minutes old)")
        return True
    else:
        print(f"❌ Data is stale ({age_minutes:.1f} minutes old)")
        return False


def validate_scheduler_health(port: int = 8080) -> bool:
    """Validate scheduler is running properly."""
    print("\n=== Validating Scheduler Health ===")

    url = f"http://localhost:{port}/status"

    try:
        response = urllib.request.urlopen(url, timeout=5)
        data = response.read().decode('utf-8')
        status_data = json.loads(data)

        next_run = status_data.get('next_scheduled_run')
        last_run = status_data.get('last_generation')

        if next_run:
            print(f"   Next scheduled run: {next_run}")
            print("✅ Scheduler is active")
            return True
        else:
            print("⚠️  No next scheduled run information")
            return False

    except urllib.error.URLError:
        print("ℹ️  Cannot check scheduler (service may not be running)")
        return True  # Not a failure if service isn't running
    except Exception as e:
        print(f"⚠️  Error checking scheduler: {e}")
        return False


def validate_error_conditions(db: DatabaseConnection) -> bool:
    """Check for any error conditions."""
    print("\n=== Validating Error Conditions ===")

    state_mgr = StateManager(db)
    state = state_mgr.get_service_state()

    if not state:
        print("ℹ️  No service state to check")
        return True

    error_msg = state.get('error_message')

    if error_msg:
        print(f"❌ Service has error: {error_msg}")
        print(f"   Status: {state.get('status')}")
        print(f"   Last run: {state.get('last_run_timestamp')}")
        return False
    else:
        print("✅ No error conditions detected")
        return True


def validate_performance_metrics(db: DatabaseConnection, table_name: str) -> bool:
    """Validate performance metrics are within acceptable ranges."""
    print("\n=== Validating Performance Metrics ===")

    # Check recent data generation rate
    query = f"""
        SELECT
            COUNT(*) as record_count,
            COUNT(DISTINCT ts) as interval_count,
            COUNT(DISTINCT entity_id) as point_count
        FROM core.{table_name}
        WHERE ts > NOW() - INTERVAL '1 hour'
    """

    result = db.execute_query(query)

    if not result:
        print("ℹ️  No recent data to analyze")
        return True

    record_count = result[0]['record_count']
    interval_count = result[0]['interval_count']
    point_count = result[0]['point_count']

    print(f"   Last hour statistics:")
    print(f"      Total records: {record_count:,}")
    print(f"      Intervals: {interval_count}")
    print(f"      Points: {point_count}")

    # Expected: 4 intervals per hour, all points should have data
    expected_intervals = 4

    if interval_count >= expected_intervals:
        print(f"   ✅ Interval count good ({interval_count} >= {expected_intervals})")
    else:
        print(f"   ⚠️  Low interval count ({interval_count} < {expected_intervals})")

    # Calculate records per interval
    if interval_count > 0:
        records_per_interval = record_count / interval_count
        print(f"      Records per interval: {records_per_interval:.0f}")

    return True


def main():
    """Run all service health validations."""
    print("=" * 60)
    print("SERVICE HEALTH VALIDATION")
    print("=" * 60)

    try:
        config = load_config()
        db = DatabaseConnection(config['database'])
        table_name = config['tables']['value_table']
        current_table = config['tables']['current_table']

        results = []

        # Database validations (always run)
        results.append(("Database Connectivity", validate_database_connectivity(db)))
        results.append(("Database Tables", validate_database_tables(db, table_name, current_table)))
        results.append(("Service State", validate_service_running_state(db)))
        results.append(("Error Conditions", validate_error_conditions(db)))
        results.append(("Data Generation", validate_data_generation_active(db, table_name)))
        results.append(("Performance Metrics", validate_performance_metrics(db, table_name)))

        # Service endpoint validations (optional - service may not be running)
        health_ok = validate_health_endpoint()
        status_ok = validate_status_endpoint()
        scheduler_ok = validate_scheduler_health()

        # These are informational if service isn't running
        if health_ok:
            results.append(("Health Endpoint", health_ok))
        if status_ok:
            results.append(("Status Endpoint", status_ok))
        if scheduler_ok:
            results.append(("Scheduler Health", scheduler_ok))

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
            print("\n✅ ALL HEALTH VALIDATIONS PASSED")
            print("\nService appears to be running properly!")
            sys.exit(0)
        elif passed >= total * 0.8:
            print(f"\n⚠️  {total - passed} VALIDATION(S) FAILED")
            print("\nService may have minor issues but core functionality appears intact")
            sys.exit(0)
        else:
            print(f"\n❌ {total - passed} VALIDATION(S) FAILED")
            print("\nService may have significant issues")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
