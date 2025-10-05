# API Testing Guide

Comprehensive testing documentation for the Haystack Building Data API.

## Test Coverage Status

### Coverage Legend

- ✅ **Tested** - Tests written and passing
- ⚠️ **Partial** - Some tests written, may have failures
- ❌ **Missing** - No tests yet

### Endpoint Coverage Summary

| Category | Total Endpoints | Tested | Partial | Missing |
|----------|----------------|--------|---------|---------|
| System | 2 | 0 | 2 | 0 |
| Entity | 4 | 0 | 4 | 0 |
| Tag Definition | 6 | 0 | 6 | 0 |
| Tag Metadata | 5 | 0 | 5 | 0 |
| Entity-Tag | 5 | 0 | 5 | 0 |
| Value | 4 | 0 | 4 | 0 |
| Filter | 1 | 0 | 0 | 1 |
| Organization | 5 | 0 | 0 | 5 |
| User | 5 | 0 | 0 | 5 |
| Permissions | ~10 | 0 | 0 | ~10 |
| Export | 1 | 0 | 0 | 1 |
| **TOTAL** | **~48** | **0** | **26** | **~22** |

### Detailed Endpoint Coverage

#### System Endpoints

| Endpoint | Method | Status | Test File | Notes |
|----------|--------|--------|-----------|-------|
| `/health` | GET | ⚠️ | `test_system.py` | Basic test written |
| `/health/databases` | GET | ⚠️ | `test_system.py` | Basic test written |

#### Entity Endpoints

| Endpoint | Method | Status | Test File | Notes |
|----------|--------|--------|-----------|-------|
| `/entity` | POST | ⚠️ | `test_entities.py` | Create entity |
| `/entity` | GET | ⚠️ | `test_entities.py` | List entities |
| `/entity/{id}` | GET | ⚠️ | `test_entities.py` | Get by ID |
| `/entity/{id}` | DELETE | ⚠️ | `test_entities.py` | Delete entity |

#### Tag Definition Endpoints

| Endpoint | Method | Status | Test File | Notes |
|----------|--------|--------|-----------|-------|
| `/tagdef` | POST | ⚠️ | `test_tag_defs.py` | Create tag def |
| `/tagdef` | GET | ⚠️ | `test_tag_defs.py` | List tag defs |
| `/tagdef/{id}` | GET | ⚠️ | `test_tag_defs.py` | Get by ID |
| `/tagdef/{id}` | PUT | ⚠️ | `test_tag_defs.py` | Update tag def |
| `/tagdef/{id}` | DELETE | ⚠️ | `test_tag_defs.py` | Delete tag def |
| `/tagdef/{id}/enum/{value}` | GET | ⚠️ | `test_tag_defs.py` | Get enum value |

#### Tag Metadata Endpoints

| Endpoint | Method | Status | Test File | Notes |
|----------|--------|--------|-----------|-------|
| `/tagmeta` | POST | ⚠️ | `test_tag_meta.py` | Create meta |
| `/tagmeta` | GET | ⚠️ | `test_tag_meta.py` | List meta |
| `/tagmeta/{id}` | GET | ⚠️ | `test_tag_meta.py` | Get by ID |
| `/tagmeta/{id}` | PUT | ⚠️ | `test_tag_meta.py` | Update meta |
| `/tagmeta/{id}` | DELETE | ⚠️ | `test_tag_meta.py` | Delete meta |

#### Entity-Tag Relationship Endpoints

| Endpoint | Method | Status | Test File | Notes |
|----------|--------|--------|-----------|-------|
| `/entitytag` | POST | ⚠️ | `test_entity_tags.py` | Create relationship |
| `/entitytag` | GET | ⚠️ | `test_entity_tags.py` | List relationships |
| `/entitytag/{id}` | GET | ⚠️ | `test_entity_tags.py` | Get by ID |
| `/entitytag/{id}` | PUT | ⚠️ | `test_entity_tags.py` | Update relationship |
| `/entitytag/{id}` | DELETE | ⚠️ | `test_entity_tags.py` | Delete relationship |

#### Value Endpoints

| Endpoint | Method | Status | Test File | Notes |
|----------|--------|--------|-----------|-------|
| `/value` | POST | ⚠️ | `test_values.py` | Add single value |
| `/bulk/value` | POST | ⚠️ | `test_values.py` | Bulk insert |
| `/value/{entity_id}` | GET | ⚠️ | `test_values.py` | Get values for entity |
| `/point/value` | POST | ⚠️ | `test_values.py` | Query values for points |

#### Missing Coverage

**Filter Endpoints:**
- `/filter` (POST) - DQQL query execution ❌

**Organization (ACL) Endpoints:**
- `/org` (POST, GET, GET/{id}, PUT/{id}, DELETE/{id}) ❌

**User (ACL) Endpoints:**
- `/user` (POST, GET, GET/{id}, PUT/{id}, DELETE/{id}) ❌

**Permission Endpoints:**
- Organization entity permissions ❌
- Organization tag permissions ❌
- User entity permissions ❌
- User tag permissions ❌

**Export Endpoints:**
- `/export` (POST) - Data export ❌

**Report Endpoints:**
- Various report endpoints ❌

### Test Counts

| Category | Count | Status |
|----------|-------|--------|
| Integration Tests | 52 | ⚠️ Partial coverage |
| Unit Tests (ANTLR) | 15 | ✅ Complete |
| **Total Tests** | **67** | **Mix of tested/untested endpoints** |

---

## Quick Start

```bash
# Install test dependencies
cd api
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test suites
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m slow              # Slow tests (E2E, performance)

# Run with coverage
pytest --cov=src/app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## Test Structure

```
test/
├── conftest.py              # Shared fixtures
├── test_utils.py            # Test utilities
├── unit/                    # Unit tests (business logic)
│   └── filter/antlr/        # ANTLR filter tests (15 tests)
├── integration/             # Integration tests (52 tests)
│   ├── test_system.py       # Health endpoints
│   ├── test_entities.py     # Entity CRUD
│   ├── test_tag_defs.py     # Tag definitions
│   ├── test_tag_meta.py     # Tag metadata
│   ├── test_entity_tags.py  # Entity-tag associations
│   └── test_values.py       # Value operations
├── e2e/                     # End-to-end tests
├── performance/             # Performance tests
└── security/                # Security tests
```

## Running Tests

### Using Pytest Directly

```bash
# All tests
pytest

# Specific markers
pytest -m unit              # Unit tests
pytest -m integration       # Integration tests
pytest -m slow              # Slow tests
pytest -m security          # Security tests

# Specific file
pytest test/integration/test_entities.py

# Specific test
pytest test/integration/test_entities.py::test_create_entity

# With verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s

# Coverage report
pytest --cov=src/app --cov-report=html
```

## Test Fixtures

Common fixtures available in `conftest.py`:

- `client` - FastAPI test client
- `test_db` - Database session (auto-rollback)
- `test_org` - Test organization
- `test_user` - Test user
- `test_entity` - Test entity
- `test_tag_def` - Test tag definition
- `auth_headers` - Authentication headers

### Example Usage

```python
import pytest

@pytest.mark.integration
def test_example(client, test_org, auth_headers):
    """Test using fixtures"""
    response = client.get(
        f"/entity?org_id={test_org.id}",
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Test Utilities

Helper functions in `test_utils.py`:

```python
from test_utils import (
    create_test_entity_payload,
    create_test_value_payload,
    create_test_values_bulk,
    assert_valid_entity_response,
    assert_valid_value_response
)

# Generate test data
payload = create_test_entity_payload(org_id=1)
values = create_test_values_bulk(entity_id=1, org_id=1, count=100)

# Validate responses
assert_valid_entity_response(response_data)
```

## Writing Tests

### Unit Test Example

```python
import pytest

@pytest.mark.unit
def test_business_logic():
    """Test business logic without database"""
    # Test pure functions, validation, etc.
    assert 1 + 1 == 2
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_api_endpoint(client, test_org, auth_headers):
    """Test API endpoint with database"""
    response = client.post("/entity", json={
        "org_id": test_org.id,
        "tags": [{"tag_def_id": "site", "value": "Test"}]
    }, headers=auth_headers)

    assert response.status_code == 200
```

### Performance Test Example

```python
import pytest
import time

@pytest.mark.performance
@pytest.mark.slow
def test_bulk_insert_performance(client, test_org, auth_headers):
    """Test bulk insert performance"""
    values = create_test_values_bulk(1, test_org.id, count=1000)

    start = time.time()
    response = client.post("/bulk/value", json={
        "org_id": test_org.id,
        "values": values
    }, headers=auth_headers)
    duration = time.time() - start

    assert response.status_code == 200
    assert duration < 5.0  # Should complete in < 5s
```

## Coverage

Generate coverage report:

```bash
pytest --cov=src/app --cov-report=html
```

View report:
```bash
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

## CI/CD Integration

Tests run automatically in GitHub Actions on:
- Push to main/develop
- Pull requests

See `.github/workflows/api-tests.yml` for configuration.

## Debugging Tests

```bash
# Verbose output
pytest -v

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Run only failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Fixtures handle cleanup automatically
3. **Fast**: Unit tests should be fast (< 1s total)
4. **Clear**: Use descriptive test names
5. **Markers**: Tag tests with appropriate markers
6. **Fixtures**: Reuse setup code via fixtures
7. **Assertions**: Use clear assertion messages

## Troubleshooting

### Database Connection Errors

Make sure database is running:
```bash
docker-compose up timescaledb
```

### Import Errors

Make sure you're in the api directory:
```bash
cd api
pytest
```

### Authentication Errors

Tests use local auth bypass. Ensure `CONFIG_KEY=local` in config.

## Further Reading

- [API Documentation](../README.md) - Main API documentation with testing section
- [Pytest Documentation](https://docs.pytest.org/) - Official pytest docs
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/) - FastAPI testing guide
