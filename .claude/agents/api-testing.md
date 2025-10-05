# API Testing Agent

**Specialized agent for testing the FastAPI backend service.**

---

## Scope

**Work ONLY on:**
- `/api/test/` - All test files
- `/api/pytest.ini` - Pytest configuration
- `/api/.coverage` - Coverage reports (read-only)
- `/api/run_tests.py` - Test runner scripts

**READ for reference:**
- `/api/src/app/` - Application code being tested
- `/api/config.json` - Configuration

**DO NOT modify:**
- Application code in `/api/src/` (API Development Agent)
- Other services (`/simulator`, `/webapp`)
- `docker-compose.yaml` (Docker Testing Agent)

---

## Testing Overview

**Goal**: Ensure API reliability, correctness, and security through comprehensive test coverage.

### Test Types
1. **Unit Tests**: Individual functions and services
2. **Integration Tests**: API endpoints end-to-end
3. **Authentication Tests**: JWT validation, permissions
4. **Database Tests**: ORM operations, queries
5. **Performance Tests**: Load testing, query optimization

### Tech Stack
- **Framework**: pytest
- **Async**: pytest-asyncio
- **HTTP Client**: httpx (for FastAPI testing)
- **Database**: SQLAlchemy with test fixtures
- **Coverage**: pytest-cov

---

## Test Structure

```
api/test/
├── conftest.py              # Shared fixtures
├── test_entities.py         # Entity CRUD operations
├── test_tags.py             # Tag definitions
├── test_entity_tags.py      # Entity-tag associations
├── test_values.py           # Time-series data
├── test_auth.py             # Authentication flows
├── test_permissions.py      # Authorization checks
├── test_health.py           # Health endpoints
├── test_bulk_operations.py  # Bulk insert/update
├── integration/             # Integration tests
│   ├── test_entity_flow.py
│   └── test_value_ingestion.py
└── fixtures/                # Test data
    └── sample_data.json
```

---

## Testing Patterns

### 1. Fixture Setup (conftest.py)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client with DB override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_org(db):
    """Create test organization"""
    from app.model.sqlalchemy.org import Org
    org = Org(name="Test Org", key="test", value_table="values_test")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

@pytest.fixture
def test_user(db, test_org):
    """Create test user"""
    from app.model.sqlalchemy.user import User
    from app.model.sqlalchemy.org_user import OrgUser

    user = User(email="test@datakwip.local")
    db.add(user)
    db.commit()
    db.refresh(user)

    org_user = OrgUser(org_id=test_org.id, user_id=user.id)
    db.add(org_user)
    db.commit()

    return user

@pytest.fixture
def auth_headers(test_user):
    """Mock authentication headers"""
    # For local dev with defaultUser
    return {}  # No headers needed if defaultUser is set

    # For production JWT testing:
    # token = generate_test_jwt(test_user.email)
    # return {"Authorization": f"Bearer {token}"}
```

### 2. Entity CRUD Tests (test_entities.py)

```python
import pytest
from fastapi import status

def test_create_entity(client, test_org, auth_headers):
    """Test entity creation"""
    response = client.post(
        "/entity",
        json={
            "org_id": test_org.id,
            "tags": [
                {"tag_def_id": "site", "value": "Building-A"},
                {"tag_def_id": "area", "value": "50000"}
            ]
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert len(data["tags"]) == 2

def test_get_entities(client, test_org, auth_headers):
    """Test entity listing"""
    # Create test entity first
    client.post("/entity", json={...}, headers=auth_headers)

    response = client.get(
        f"/entity?org_id={test_org.id}&limit=10",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    entities = response.json()
    assert len(entities) >= 1

def test_get_entity_by_id(client, test_org, auth_headers):
    """Test entity retrieval by ID"""
    # Create entity
    create_response = client.post("/entity", json={...}, headers=auth_headers)
    entity_id = create_response.json()["id"]

    # Get entity
    response = client.get(
        f"/entity/{entity_id}?org_id={test_org.id}",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == entity_id

def test_delete_entity(client, test_org, auth_headers):
    """Test entity deletion"""
    # Create entity
    create_response = client.post("/entity", json={...}, headers=auth_headers)
    entity_id = create_response.json()["id"]

    # Delete entity
    response = client.delete(
        f"/entity/{entity_id}",
        json={"org_id": test_org.id},
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify deletion
    get_response = client.get(
        f"/entity/{entity_id}?org_id={test_org.id}",
        headers=auth_headers
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND
```

### 3. Value Tests (test_values.py)

```python
import pytest
from datetime import datetime, timezone

def test_create_value(client, test_org, test_entity, auth_headers):
    """Test single value creation"""
    response = client.post(
        "/value",
        json={
            "entity_id": test_entity.id,
            "org_id": test_org.id,
            "timestamp": "2025-01-04T12:00:00Z",
            "value": 72.5
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["value"] == 72.5
    assert data["entity_id"] == test_entity.id

def test_bulk_value_insert(client, test_org, test_entity, auth_headers):
    """Test bulk value insertion"""
    values = [
        {
            "entity_id": test_entity.id,
            "timestamp": f"2025-01-04T{hour:02d}:00:00Z",
            "value": 70 + hour
        }
        for hour in range(24)
    ]

    response = client.post(
        "/bulk/value",
        json={
            "org_id": test_org.id,
            "values": values
        },
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 24

def test_get_entity_values(client, test_org, test_entity, auth_headers):
    """Test value retrieval for entity"""
    # Insert test values
    client.post("/bulk/value", json={...}, headers=auth_headers)

    # Get values
    response = client.get(
        f"/value/{test_entity.id}?org_id={test_org.id}&limit=10",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    values = response.json()
    assert len(values) > 0
```

### 4. Authentication Tests (test_auth.py)

```python
import pytest
from fastapi import status

def test_missing_auth_header(client, test_org):
    """Test request without Authorization header"""
    # Only fails if defaultUser is NOT set in config
    response = client.get(f"/entity?org_id={test_org.id}")

    # If defaultUser is set: 200 OK
    # If defaultUser not set: 401 Unauthorized
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

def test_invalid_jwt_token(client, test_org):
    """Test request with invalid JWT"""
    response = client.get(
        f"/entity?org_id={test_org.id}",
        headers={"Authorization": "Bearer invalid_token"}
    )

    # If defaultUser is set: ignored, 200 OK
    # If defaultUser not set: 403 Forbidden
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

def test_user_not_found(client, test_org):
    """Test JWT with email not in database"""
    # Create valid JWT for non-existent user
    token = generate_test_jwt("nonexistent@example.com")

    response = client.get(
        f"/entity?org_id={test_org.id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not authorized" in response.json()["detail"].lower()
```

### 5. Permission Tests (test_permissions.py)

```python
import pytest
from fastapi import status

def test_org_isolation(client, test_org, other_org, test_user, auth_headers):
    """Test users can't access other org's data"""
    # Create entity in test_org
    response = client.post("/entity", json={
        "org_id": test_org.id,
        "tags": [{"tag_def_id": "site", "value": "Test"}]
    }, headers=auth_headers)
    entity_id = response.json()["id"]

    # Try to access with other_org.id (user not member)
    response = client.get(
        f"/entity/{entity_id}?org_id={other_org.id}",
        headers=auth_headers
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
```

---

## Running Tests

### Local Testing

```bash
# Start test database
docker-compose up timescaledb

# Install test dependencies
cd api
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx pytest-cov

# Run all tests
pytest

# Run specific test file
pytest test/test_entities.py -v

# Run with coverage
pytest --cov=src/app --cov-report=html test/

# Run specific test
pytest test/test_entities.py::test_create_entity -v

# Run with output
pytest -s test/test_values.py
```

### Coverage Requirements

**Minimum Coverage Targets:**
- Overall: 80%
- Core endpoints: 90%
- Authentication: 95%
- DTOs: 85%

```bash
# Generate coverage report
pytest --cov=src/app --cov-report=term-missing test/

# HTML report
pytest --cov=src/app --cov-report=html test/
# Open htmlcov/index.html
```

---

## Test Database Management

### Option 1: Separate Test Database

```python
# conftest.py
SQLALCHEMY_DATABASE_URL = "postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip_test"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database once per session"""
    # Create database
    engine = create_engine("postgresql://datakwip_user:datakwip_password@localhost:5432/postgres")
    conn = engine.connect()
    conn.execute("commit")
    conn.execute("CREATE DATABASE datakwip_test")
    conn.close()

    yield

    # Drop database
    conn = engine.connect()
    conn.execute("commit")
    conn.execute("DROP DATABASE datakwip_test")
    conn.close()
```

### Option 2: Transaction Rollback

```python
@pytest.fixture(scope="function")
def db():
    """Each test runs in transaction, rollback after"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

---

## Integration Testing

### Full Flow Test

```python
# test/integration/test_entity_value_flow.py

def test_complete_entity_value_flow(client, test_org, auth_headers):
    """Test complete flow: create entity → add tags → insert values"""

    # 1. Create entity
    entity_response = client.post("/entity", json={
        "org_id": test_org.id,
        "tags": [
            {"tag_def_id": "site", "value": "Building-A"},
            {"tag_def_id": "equip", "value": None},
            {"tag_def_id": "ahu", "value": None}
        ]
    }, headers=auth_headers)

    assert entity_response.status_code == 200
    entity_id = entity_response.json()["id"]

    # 2. Add point tags
    point_response = client.post("/entity", json={
        "org_id": test_org.id,
        "tags": [
            {"tag_def_id": "point", "value": None},
            {"tag_def_id": "temp", "value": None},
            {"tag_def_id": "equipRef", "value": entity_id}
        ]
    }, headers=auth_headers)

    point_id = point_response.json()["id"]

    # 3. Insert time-series values
    values_response = client.post("/bulk/value", json={
        "org_id": test_org.id,
        "values": [
            {
                "entity_id": point_id,
                "timestamp": "2025-01-04T12:00:00Z",
                "value": 72.5
            },
            {
                "entity_id": point_id,
                "timestamp": "2025-01-04T12:15:00Z",
                "value": 73.0
            }
        ]
    }, headers=auth_headers)

    assert values_response.status_code == 200
    assert len(values_response.json()) == 2

    # 4. Query values
    query_response = client.get(
        f"/value/{point_id}?org_id={test_org.id}",
        headers=auth_headers
    )

    assert query_response.status_code == 200
    values = query_response.json()
    assert len(values) == 2
    assert values[0]["value"] == 72.5
```

---

## Performance Testing

### Load Testing

```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

def test_bulk_insert_performance(client, test_org, test_entity, auth_headers):
    """Test bulk insert performance"""

    # Generate 10,000 values
    values = [
        {
            "entity_id": test_entity.id,
            "timestamp": f"2025-01-{day:02d}T{hour:02d}:{minute:02d}:00Z",
            "value": 70 + (hour % 24)
        }
        for day in range(1, 11)
        for hour in range(24)
        for minute in [0, 15, 30, 45]
    ]

    start = time.time()
    response = client.post("/bulk/value", json={
        "org_id": test_org.id,
        "values": values
    }, headers=auth_headers)
    duration = time.time() - start

    assert response.status_code == 200
    assert len(response.json()) == len(values)
    print(f"Inserted {len(values)} values in {duration:.2f}s ({len(values)/duration:.0f} values/sec)")

def test_concurrent_requests(client, test_org, auth_headers):
    """Test concurrent API requests"""

    def make_request():
        return client.get(f"/entity?org_id={test_org.id}", headers=auth_headers)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in results)
```

---

## Mocking External Services

### Cognito JWT Mocking

```python
# test/mocks/jwt_mock.py

import jwt
import time
from datetime import datetime, timedelta

def generate_test_jwt(email: str, user_pool_id: str = "us-east-1_TEST") -> str:
    """Generate test JWT token"""

    payload = {
        "sub": "test-user-id",
        "email": email,
        "username": email.split("@")[0],
        "iss": f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}",
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now().timestamp())
    }

    # Sign with test key (mock JWKS)
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token
```

---

## Continuous Integration

### pytest.ini Configuration

```ini
[pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=src/app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### GitHub Actions Workflow

```yaml
# .github/workflows/api-tests.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: timescale/timescaledb:latest-pg15
        env:
          POSTGRES_DB: datakwip_test
          POSTGRES_USER: datakwip_user
          POSTGRES_PASSWORD: datakwip_password
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd api
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov

      - name: Run tests
        run: |
          cd api
          pytest --cov=src/app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./api/coverage.xml
```

---

## Handoff Points

**From API Development Agent:**
- New endpoint created → write test coverage
- Endpoint modified → update regression tests
- Bug fix → add test case to prevent regression

**To Docker Testing Agent:**
- When integration testing needs full docker-compose stack
- When testing cross-service interactions

**To Haystack Database Agent:**
- When test data needs specific schema setup
- When testing complex queries

---

## Related Documentation

- [API README](../../api/README.md)
- [API Test Documentation](../../api/test/README.md)
- [pytest documentation](https://docs.pytest.org/)

---

## Agent Boundaries

**✅ CAN:**
- Write and modify all test files
- Create test fixtures and utilities
- Run tests locally
- Generate coverage reports
- Request test data from Haystack Database Agent
- Coordinate with API Development Agent on test requirements

**❌ CANNOT:**
- Modify application code (API Development Agent)
- Modify other services
- Run docker-compose (Docker Testing Agent)
- Change database schema (Haystack Database Agent)
