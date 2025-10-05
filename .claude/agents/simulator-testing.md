# Simulator Testing Agent

**Specialized agent for testing the simulator service and validating data generation.**

---

## Scope

**Work ONLY on:**
- `/simulator/test/` - Unit and integration tests
- `/simulator/validation/` - Validation scripts
- Test utilities and fixtures

**READ for reference:**
- `/simulator/src/` - Application code being tested
- `/simulator/config/` - Configuration files

**DO NOT modify:**
- Application code in `/simulator/src/` (Simulator Development Agent)
- Other services (`/api`, `/webapp`)
- `docker-compose.yaml` (Docker Testing Agent)

---

## Testing Overview

**Goal**: Ensure simulator reliability, data coherency, state persistence, and continuous operation.

### Test Categories
1. **Unit Tests**: Individual service components
2. **Integration Tests**: Full generation flow
3. **State Tests**: Persistence and resumption
4. **Gap Tests**: Detection and backfilling
5. **Validation Scripts**: Data coherency checks
6. **Performance Tests**: Generation throughput

### Tech Stack
- **Framework**: pytest (or unittest)
- **Database**: PostgreSQL test instances
- **Assertions**: Custom validators for Haystack data
- **Fixtures**: Test configurations and sample data

---

## Test Structure

```
simulator/test/
├── test_state_manager.py         # State persistence
├── test_gap_filler.py             # Gap detection/filling
├── test_continuous_service.py     # Main generation service
├── test_resumption.py             # Resume after stop
├── test_generators.py             # Entity/time-series generators
├── test_activity_logger.py        # Event logging
├── test_scheduler.py              # APScheduler integration
├── conftest.py                    # Shared fixtures
└── fixtures/
    ├── test_building_config.yaml
    └── sample_entities.json

simulator/validation/
├── validate_service_state.py     # State consistency
├── validate_gaps.py               # Gap detection
├── validate_service_health.py    # Health checks
├── validate_data_coherency.py    # Equipment relationships
└── validate_totalizers.py        # Monotonic increase
```

---

## Testing Patterns

### 1. Fixtures (conftest.py)

```python
import pytest
from sqlalchemy import create_engine
from simulator.src.database.db_operations import DatabaseOperations
from simulator.src.service.state_manager import StateManager
from simulator.src.service.activity_logger import ActivityLogger
from simulator.src.service.gap_filler import GapFiller
from simulator.src.service.continuous_generator import ContinuousGenerator

# Test database URLs
TEST_TIMESCALE_URL = "postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip_test"
TEST_STATE_URL = "postgresql://simulator_user:simulator_password@localhost:5433/simulator_state_test"

@pytest.fixture(scope="session")
def test_db_config():
    """Test database configuration"""
    return {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'datakwip_test',
            'user': 'datakwip_user',
            'password': 'datakwip_password',
            'schema': 'core'
        },
        'state_database': {
            'url': TEST_STATE_URL
        },
        'tables': {
            'entity_table': 'entity',
            'entity_tag_table': 'entity_tag',
            'value_table': 'values_test',
            'current_table': 'values_test_current'
        }
    }

@pytest.fixture(scope="function")
def db_ops(test_db_config):
    """Database operations with cleanup"""
    db = DatabaseOperations(test_db_config)

    yield db

    # Cleanup
    db.reset_all_data(
        value_table=test_db_config['tables']['value_table'],
        current_table=test_db_config['tables']['current_table']
    )

@pytest.fixture(scope="function")
def state_manager():
    """State manager with test database"""
    manager = StateManager(TEST_STATE_URL)

    yield manager

    # Cleanup
    manager.reset_state()

@pytest.fixture(scope="function")
def activity_logger():
    """Activity logger with test database"""
    logger = ActivityLogger(TEST_STATE_URL)

    yield logger

    # Cleanup (optional - can keep logs for debugging)
    with logger.engine.connect() as conn:
        conn.execute("DELETE FROM simulator_activity_log WHERE event_type LIKE 'test_%'")
        conn.commit()

@pytest.fixture
def test_building_config():
    """Minimal building config for testing"""
    return {
        'organization': {'name': 'Test Org', 'key': 'test'},
        'building': {'name': 'Test Building', 'area': 10000, 'floors': 2},
        'equipment': {'chillers': 1, 'ahus': 2, 'vavs_per_ahu': 5},
        'weather': {'simulate': False},
        'generation': {'interval_minutes': 15, 'start_date': '2025-01-01T00:00:00Z'}
    }

@pytest.fixture
def continuous_generator(db_ops, state_manager, activity_logger, test_building_config):
    """Full generator service"""
    gap_filler = GapFiller(db_ops, state_manager, test_building_config)
    generator = ContinuousGenerator(
        db_ops, state_manager, gap_filler, activity_logger, test_building_config
    )

    return generator
```

### 2. State Manager Tests (test_state_manager.py)

```python
import pytest
from datetime import datetime, timezone

def test_create_initial_state(state_manager):
    """Test creating initial state"""
    state_manager.update_state(
        is_running=False,
        last_run_time=datetime.now(timezone.utc),
        generated_count=0,
        totalizers={}
    )

    state = state_manager.get_state()
    assert state is not None
    assert state.is_running == False
    assert state.generated_count == 0

def test_update_state(state_manager):
    """Test updating state fields"""
    # Create initial
    state_manager.update_state(is_running=False, generated_count=0)

    # Update
    state_manager.update_state(is_running=True, generated_count=100)

    state = state_manager.get_state()
    assert state.is_running == True
    assert state.generated_count == 100

def test_totalizer_persistence(state_manager):
    """Test totalizer values persist"""
    totalizers = {123: 1500.5, 456: 2400.0}

    state_manager.update_state(totalizers=totalizers)

    state = state_manager.get_state()
    assert state.totalizers == totalizers

def test_reset_state(state_manager):
    """Test state deletion"""
    state_manager.update_state(is_running=True)
    state_manager.reset_state()

    state = state_manager.get_state()
    assert state is None

def test_state_survives_restart(state_manager):
    """Test state persists across manager instances"""
    # Create state
    state_manager.update_state(is_running=True, generated_count=500)

    # Simulate restart - new manager instance
    new_manager = StateManager(state_manager.engine.url)
    state = new_manager.get_state()

    assert state.is_running == True
    assert state.generated_count == 500
```

### 3. Gap Filler Tests (test_gap_filler.py)

```python
import pytest
from datetime import datetime, timezone, timedelta

def test_detect_no_gaps(db_ops, state_manager, gap_filler):
    """Test no gaps when data is continuous"""
    # Create entities
    entity_id = db_ops.insert_entity([{'tag': 'site'}, {'tag': 'point'}])

    # Insert continuous data
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    for i in range(10):
        ts = start + timedelta(minutes=i * 15)
        db_ops.insert_value(entity_id, ts, 70 + i, 'values_test')

    # Update state
    state_manager.update_state(last_run_time=start + timedelta(minutes=9 * 15))

    gaps = gap_filler.detect_gaps()
    assert len(gaps) == 0

def test_detect_gaps(db_ops, state_manager, gap_filler):
    """Test gap detection"""
    entity_id = db_ops.insert_entity([{'tag': 'site'}, {'tag': 'point'}])

    # Insert data with gaps
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    db_ops.insert_value(entity_id, start, 70, 'values_test')
    db_ops.insert_value(entity_id, start + timedelta(minutes=15), 71, 'values_test')
    # GAP: missing 30 minutes
    db_ops.insert_value(entity_id, start + timedelta(minutes=45), 72, 'values_test')

    state_manager.update_state(last_run_time=start)

    gaps = gap_filler.detect_gaps()
    assert len(gaps) == 1
    assert gaps[0][0] == start + timedelta(minutes=30)

def test_fill_gaps(db_ops, state_manager, gap_filler):
    """Test gap filling"""
    entity_id = db_ops.insert_entity([{'tag': 'site'}, {'tag': 'point'}])

    # Create gap
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    db_ops.insert_value(entity_id, start, 70, 'values_test')
    # GAP at start + 15 minutes
    db_ops.insert_value(entity_id, start + timedelta(minutes=30), 72, 'values_test')

    state_manager.update_state(last_run_time=start)

    # Detect and fill
    gaps = gap_filler.detect_gaps()
    gap_filler.fill_gaps(gaps)

    # Verify filled
    values = db_ops.get_entity_values(entity_id, 'values_test')
    assert len(values) == 3  # Original 2 + 1 filled

def test_totalizers_updated_during_fill(db_ops, state_manager, gap_filler):
    """Test totalizer continuity during gap fill"""
    # Create totalizer entity
    entity_id = db_ops.insert_entity([
        {'tag': 'site'}, {'tag': 'point'}, {'tag': 'energy'}, {'tag': 'his'}
    ])

    # Initial state with totalizer
    state_manager.update_state(totalizers={entity_id: 1000.0})

    # Create gap
    start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    db_ops.insert_value(entity_id, start, 1000.0, 'values_test')
    # GAP
    db_ops.insert_value(entity_id, start + timedelta(minutes=30), 1002.0, 'values_test')

    # Fill gap
    gaps = gap_filler.detect_gaps()
    gap_filler.fill_gaps(gaps)

    # Check totalizer continuity
    values = db_ops.get_entity_values(entity_id, 'values_test')
    assert values[0]['value'] == 1000.0
    assert values[1]['value'] > 1000.0  # Filled value
    assert values[1]['value'] < 1002.0  # Between original values
    assert values[2]['value'] == 1002.0
```

### 4. Continuous Service Tests (test_continuous_service.py)

```python
import pytest
from datetime import datetime, timezone, timedelta

def test_initialize_service(continuous_generator):
    """Test service initialization"""
    continuous_generator.start()

    state = continuous_generator.state_manager.get_state()
    assert state.is_running == True

def test_generate_single_interval(continuous_generator):
    """Test single interval generation"""
    continuous_generator.start()
    continuous_generator.generate_interval()

    state = continuous_generator.state_manager.get_state()
    assert state.generated_count > 0

def test_stop_service(continuous_generator):
    """Test stopping service"""
    continuous_generator.start()
    continuous_generator.stop()

    state = continuous_generator.state_manager.get_state()
    assert state.is_running == False

def test_reset_service(continuous_generator):
    """Test reset clears all data"""
    continuous_generator.start()
    continuous_generator.generate_interval()

    # Verify data exists
    entities = continuous_generator.db.get_all_entities()
    assert len(entities) > 0

    # Reset
    continuous_generator.reset()

    # Verify cleared
    entities = continuous_generator.db.get_all_entities()
    assert len(entities) == 0

    state = continuous_generator.state_manager.get_state()
    assert state is None

def test_activity_logging(continuous_generator):
    """Test events are logged"""
    continuous_generator.start()
    continuous_generator.generate_interval()
    continuous_generator.stop()

    activities = continuous_generator.activity_logger.get_recent(limit=10)

    event_types = [a['event_type'] for a in activities]
    assert 'started' in event_types
    assert 'data_generated' in event_types
    assert 'stopped' in event_types
```

### 5. Resumption Tests (test_resumption.py)

```python
import pytest
from datetime import datetime, timezone, timedelta

def test_resume_after_stop(continuous_generator):
    """Test resuming generation after stop"""
    # Start and generate
    continuous_generator.start()
    continuous_generator.generate_interval()

    state1 = continuous_generator.state_manager.get_state()
    last_run_1 = state1.last_run_time
    count_1 = state1.generated_count

    # Stop
    continuous_generator.stop()

    # Resume
    continuous_generator.start()
    continuous_generator.generate_interval()

    state2 = continuous_generator.state_manager.get_state()
    assert state2.last_run_time > last_run_1
    assert state2.generated_count > count_1

def test_gap_filling_on_resume(continuous_generator):
    """Test gaps are filled when resuming after long stop"""
    # Generate initial data
    continuous_generator.start()
    continuous_generator.generate_interval()

    state = continuous_generator.state_manager.get_state()
    last_run = state.last_run_time

    # Stop
    continuous_generator.stop()

    # Simulate time passing (4 intervals missed)
    continuous_generator.state_manager.update_state(
        last_run_time=last_run - timedelta(minutes=60)  # 4 x 15min intervals
    )

    # Resume - should detect and fill gaps
    continuous_generator.start()

    # Check gap fill happened
    activities = continuous_generator.activity_logger.get_recent(limit=10)
    gap_events = [a for a in activities if a['event_type'] == 'gaps_filled']
    assert len(gap_events) > 0
```

---

## Validation Scripts

### 1. Service State Validation (validation/validate_service_state.py)

```python
#!/usr/bin/env python3
"""Validate simulator service state consistency"""

import sys
from datetime import datetime, timezone
from simulator.src.service.state_manager import StateManager

def validate_state():
    """Check state consistency"""
    manager = StateManager(os.getenv('STATE_DB_URL'))
    state = manager.get_state()

    if not state:
        print("✅ No state found (fresh start)")
        return True

    errors = []

    # Check timestamps
    if state.last_run_time and state.last_run_time > datetime.now(timezone.utc):
        errors.append("❌ last_run_time is in the future")

    # Check counts
    if state.generated_count < 0:
        errors.append("❌ generated_count is negative")

    if state.error_count < 0:
        errors.append("❌ error_count is negative")

    # Check totalizers
    if state.totalizers:
        for entity_id, value in state.totalizers.items():
            if value < 0:
                errors.append(f"❌ Totalizer for entity {entity_id} is negative: {value}")

    if errors:
        print("\n".join(errors))
        return False

    print("✅ State validation passed")
    print(f"  - Running: {state.is_running}")
    print(f"  - Last run: {state.last_run_time}")
    print(f"  - Generated: {state.generated_count}")
    print(f"  - Totalizers: {len(state.totalizers)}")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate_state() else 1)
```

### 2. Gap Validation (validation/validate_gaps.py)

```python
#!/usr/bin/env python3
"""Detect and report any gaps in time-series data"""

import sys
from datetime import timedelta
from simulator.src.database.db_operations import DatabaseOperations
from simulator.src.service.state_manager import StateManager
from simulator.src.database.config_loader import load_config_with_env

def validate_gaps():
    """Check for gaps in generated data"""
    db_config = load_config_with_env('config/database_config.yaml')
    db = DatabaseOperations(db_config)

    state_manager = StateManager(os.getenv('STATE_DB_URL'))
    state = state_manager.get_state()

    if not state or not state.last_run_time:
        print("✅ No state - nothing to validate")
        return True

    # Get all timestamps
    timestamps = db.get_distinct_timestamps(db_config['tables']['value_table'])

    if not timestamps:
        print("⚠️  No data found")
        return True

    # Check for gaps
    timestamps.sort()
    interval = timedelta(minutes=state.config['generation']['interval_minutes'])

    gaps = []
    for i in range(len(timestamps) - 1):
        expected_next = timestamps[i] + interval
        actual_next = timestamps[i + 1]

        if actual_next > expected_next:
            gap_duration = (actual_next - expected_next).total_seconds() / 60
            gaps.append({
                'start': expected_next,
                'end': actual_next,
                'duration_minutes': gap_duration
            })

    if gaps:
        print(f"❌ Found {len(gaps)} gap(s):")
        for gap in gaps:
            print(f"  - {gap['start']} to {gap['end']} ({gap['duration_minutes']:.0f} min)")
        return False

    print(f"✅ No gaps found in {len(timestamps)} intervals")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate_gaps() else 1)
```

### 3. Data Coherency Validation (validation/validate_data_coherency.py)

```python
#!/usr/bin/env python3
"""Validate building equipment relationships are coherent"""

import sys
from simulator.src.database.db_operations import DatabaseOperations
from simulator.src.database.config_loader import load_config_with_env

def validate_coherency():
    """Check equipment relationships"""
    db_config = load_config_with_env('config/database_config.yaml')
    db = DatabaseOperations(db_config)

    errors = []

    # Get all entities
    entities = db.get_all_entities()

    # Check site exists
    sites = [e for e in entities if 'site' in [t['tag'] for t in e['tags']]]
    if len(sites) == 0:
        errors.append("❌ No site entity found")
    elif len(sites) > 1:
        errors.append(f"❌ Multiple site entities found: {len(sites)}")

    # Check equipment references
    ahus = [e for e in entities if 'ahu' in [t['tag'] for t in e['tags']]]
    vavs = [e for e in entities if 'vav' in [t['tag'] for t in e['tags']]]

    for vav in vavs:
        # VAV should have equipRef to AHU
        equip_ref = next((t['value'] for t in vav['tags'] if t['tag'] == 'equipRef'), None)
        if not equip_ref:
            errors.append(f"❌ VAV {vav['id']} missing equipRef")
        elif equip_ref not in [a['id'] for a in ahus]:
            errors.append(f"❌ VAV {vav['id']} references invalid AHU {equip_ref}")

    # Check points have equipRef
    points = [e for e in entities if 'point' in [t['tag'] for t in e['tags']]]
    for point in points:
        equip_ref = next((t['value'] for t in point['tags'] if t['tag'] == 'equipRef'), None)
        if not equip_ref:
            errors.append(f"❌ Point {point['id']} missing equipRef")

    if errors:
        print("\n".join(errors))
        return False

    print("✅ Data coherency validated")
    print(f"  - Sites: {len(sites)}")
    print(f"  - AHUs: {len(ahus)}")
    print(f"  - VAVs: {len(vavs)}")
    print(f"  - Points: {len(points)}")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate_coherency() else 1)
```

---

## Running Tests

### Local Testing

```bash
# Start test databases
docker-compose up timescaledb statedb

# Run all tests
cd simulator
python -m pytest test/

# Run specific test file
python test/test_state_manager.py

# Run validation scripts
python validation/validate_service_state.py
python validation/validate_gaps.py
python validation/validate_data_coherency.py

# Run with verbose output
python -m pytest test/ -v -s
```

### Coverage Requirements

**Minimum Coverage:**
- State management: 95%
- Gap filling: 90%
- Data generation: 85%
- Activity logging: 80%

---

## Handoff Points

**From Simulator Development Agent:**
- New feature → write tests
- Bug fix → add regression test
- State changes → update validation scripts

**To Docker Testing Agent:**
- Integration testing with full stack
- Testing docker-compose orchestration

---

## Agent Boundaries

**✅ CAN:**
- Write and modify test files
- Create validation scripts
- Run tests locally
- Generate test data
- Request test scenarios from Simulator Development Agent

**❌ CANNOT:**
- Modify application code (Simulator Development Agent)
- Modify other services
- Run docker-compose (Docker Testing Agent)
- Change database schema (Haystack Database Agent)
