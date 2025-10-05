# Haystack Building Data API

Enterprise-grade FastAPI backend for managing building automation data using Project Haystack v3 schema.

## 🏗️ Architecture

```
API Service
├── FastAPI REST API (:8000)
│   ├── Source Objects (entities, tags, values)
│   ├── Access Control (orgs, users, permissions)
│   ├── Filtering (DQQL query language)
│   └── System health & monitoring
├── TimescaleDB (:5432)
│   ├── Entity-Attribute-Value model
│   ├── Time-series data (hypertables)
│   └── Haystack v3 tag schema
└── Multi-database support
    └── Automatic failover & replication
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# From repository root
docker-compose up api timescaledb

# Access:
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
# - Database Health: http://localhost:8000/health/databases
```

### Option 2: Local Development

**Terminal 1: Start Database**
```bash
docker-compose up timescaledb
```

**Terminal 2: Start API**
```bash
cd api
pip install -r requirements.txt
python src/app/main.py
```

Then visit:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📁 Project Structure

```
api/
├── src/app/
│   ├── api/
│   │   ├── source_objects/         # Core data endpoints
│   │   │   ├── entity.py           # Building equipment/entities
│   │   │   ├── tag_def.py          # Tag definitions
│   │   │   ├── tag_meta.py         # Tag metadata
│   │   │   ├── entity_tag.py       # Entity-tag associations
│   │   │   └── value.py            # Time-series values
│   │   ├── acl/                    # Access control
│   │   │   ├── org/                # Organization management
│   │   │   └── user/               # User management
│   │   ├── filter/                 # DQQL filtering
│   │   │   └── antlr/              # ANTLR query parser
│   │   ├── views/                  # Database views
│   │   ├── exporter/               # Data export
│   │   └── system.py               # Health checks
│   ├── services/                   # Business logic
│   ├── dto/                        # Data transfer objects
│   ├── model/
│   │   ├── pydantic/               # Request/response models
│   │   └── sqlalchemy/             # Database models
│   ├── database/                   # Database utilities
│   └── main.py                     # Application entry point
├── config.json                     # Configuration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container definition
└── test/                          # Tests
```

## 🎯 API Endpoints

### Health & System

**Health Checks:**
- `GET /health` - Basic health check
- `GET /health/databases` - Database connection status

### Source Objects (Core Data)

**Entities** - Building equipment, spaces, systems

- `POST /entity` - Create new entity
  - **Request**: `EntityCreate` (org_id, tags[])
  - **Response**: `Entity` (id, tags[])
  - **Auth**: Requires user authentication

- `GET /entity` - List entities
  - **Params**: org_id (required), skip, limit
  - **Response**: `Entity[]`
  - **Pagination**: Default limit 100

- `GET /entity/{entity_id}` - Get specific entity
  - **Params**: entity_id, org_id
  - **Response**: `Entity`

- `DELETE /entity/{entity_id}` - Delete entity
  - **Request**: `EntityDelete` (org_id)
  - **Response**: `Entity`

**Tag Definitions** - Define available Haystack tags

- `POST /tagdef` - Create tag definition
  - **Request**: `TagDefCreate` (name, org_id, type, etc.)
  - **Response**: `TagDef`

- `GET /tagdef` - List tag definitions
  - **Params**: org_id (required), skip, limit, name (optional)
  - **Response**: `TagDef[]`

- `GET /tagdef/{tag_id}` - Get specific tag definition
  - **Params**: tag_id, org_id
  - **Response**: `TagDef`

- `PUT /tagdef/{tag_id}` - Update tag definition
  - **Request**: `TagDefUpdate`
  - **Response**: `TagDef`

- `DELETE /tagdef/{tag_id}` - Delete tag definition
  - **Request**: `TagDefDelete` (org_id)
  - **Response**: `TagDef`

- `GET /tagdef/{tag_id}/enum/{value}` - Get enum value
  - **Params**: tag_id, value, org_id
  - **Response**: `TagDefEnum`

**Tag Metadata** - Additional tag information

- `POST /tag-meta` - Create tag metadata
- `GET /tag-meta` - List tag metadata
- `GET /tag-meta/{meta_id}` - Get specific metadata
- `PUT /tag-meta/{meta_id}` - Update metadata
- `DELETE /tag-meta/{meta_id}` - Delete metadata

**Entity Tags** - Associate tags with entities

- `POST /entity-tag` - Add tag to entity
- `GET /entity-tag` - List entity tags
- `GET /entity-tag/{tag_id}` - Get specific entity tag
- `PUT /entity-tag/{tag_id}` - Update entity tag
- `DELETE /entity-tag/{tag_id}` - Delete entity tag

**Values** - Time-series data points

- `POST /value` - Add single value
  - **Request**: `ValueBaseCreate` (entity_id, org_id, timestamp, value)
  - **Response**: `ValueBase`
  - **Note**: Auto-routed to org-specific value table

- `POST /bulk/value` - Add multiple values (batch insert)
  - **Request**: `ValueBulkCreate` (org_id, values[])
  - **Response**: `ValueBase[]`
  - **Performance**: Optimized for high-throughput data ingestion

- `GET /value/{entity_id}` - Get values for entity
  - **Params**: entity_id, org_id, skip, limit
  - **Response**: `ValueBase[]`

- `POST /point/value` - Get values for multiple points
  - **Request**: `ValueForPoints` (point_ids[], start, end)
  - **Response**: `ValueBaseResponse[]`

### Filtering

**DQQL Filter** - Query language for data filtering

- `POST /filter` - Execute filter query
  - **Request**: DQQL query string
  - **Response**: Filtered results
  - **Example**: `site and equip and ahu`

### Access Control (ACL)

**Organizations:**
- `POST /org` - Create organization
- `GET /org` - List organizations
- `GET /org/{org_id}` - Get organization
- `PUT /org/{org_id}` - Update organization
- `DELETE /org/{org_id}` - Delete organization

**Users:**
- `POST /user` - Create user
- `GET /user` - List users
- `GET /user/{user_id}` - Get user
- `PUT /user/{user_id}` - Update user
- `DELETE /user/{user_id}` - Delete user

**Permissions:**
- Entity permissions (read, write, revoke)
- Tag permissions (add, revoke)
- Organization-level access control

### Data Export

- `POST /export` - Export data in various formats
  - Formats: CSV, Excel, JSON
  - Haystack-compliant exports

## 📊 Data Model

### Haystack v3 Schema

The API implements Project Haystack's entity-attribute-value model:

**Entity** - A thing (equipment, space, point)
```json
{
  "id": 123,
  "tags": [
    {"tag_def_id": "site", "value": "Building-A"},
    {"tag_def_id": "area", "value": "50000", "unit": "ft²"}
  ]
}
```

**Tag Definition** - Available tags
```json
{
  "id": "temp",
  "name": "temp",
  "type": "Number",
  "unit": "°F",
  "description": "Temperature measurement"
}
```

**Value** - Time-series measurement
```json
{
  "entity_id": 123,
  "timestamp": "2025-01-04T12:00:00Z",
  "value": 72.5,
  "org_id": 1
}
```

### Multi-Tenancy

- **Organization-level isolation**: Each org has separate value tables
- **Dynamic table creation**: `values_{org_key}` hypertables
- **Schema separation**: Core schema for shared data, org-specific for values

## ⚙️ Configuration

### Environment Variables

```bash
# Configuration file
CONFIG_PATH=config.json
CONFIG_KEY=local  # or 'production'

# Database (from config.json)
# dbUrl - Primary database connection
# dbUrlGrafanaConnector - Read replica for analytics
# dbScheme - Database schema (usually 'core')

# Authentication
# app_client_id - AWS Cognito app client ID
# user_pool_id - AWS Cognito user pool ID

# Application
# loadDataFromCsv - Load initial data (true/false)
# logLevel - Logging level (info, debug, error)
```

### config.json Structure

```json
{
  "local": {
    "dbUrl": "postgresql://user:pass@timescaledb:5432/datakwip",
    "loadDataFromCsv": false,
    "logLevel": "info",
    "dbScheme": "core",
    "dbUrlGrafanaConnector": "postgresql://user:pass@timescaledb:5432/datakwip",
    "app_client_id": "local-dev-no-auth",
    "user_pool_id": "local-dev-no-auth"
  },
  "production": {
    "dbUrl": "postgresql://user:pass@host:port/db?sslmode=require",
    "loadDataFromCsv": false,
    "logLevel": "info",
    "dbScheme": "core",
    "dbUrlGrafanaConnector": "postgresql://readonly:pass@replica:port/db",
    "app_client_id": "YOUR_COGNITO_APP_CLIENT_ID",
    "user_pool_id": "YOUR_COGNITO_USER_POOL_ID"
  }
}
```

## 🧪 Testing

API tests use simulator-generated data instead of complex fixtures. This approach ensures tests run against realistic building automation data.

### Prerequisites

**IMPORTANT**: Tests require the simulator to seed the database first.

```bash
# First time setup
cd api/test
./setup_test_env.sh

# Or manually:
docker-compose up -d timescaledb statedb
docker-compose up simulator
```

The simulator creates:
- Organization (demo)
- Tag definitions (site, equip, ahu, vav, point, temp, etc.)
- Building entities (sites, AHUs, VAVs, points)
- Time-series values

### Running Tests

```bash
cd api
pytest test/integration/ -v

# Run specific test file
pytest test/integration/test_entities.py -v

# Run with coverage
pytest test/integration/ --cov=src/app --cov-report=html
```

### Test Structure

```
test/
├── conftest.py              # Simulator fixtures (org, entities, tag_defs)
├── setup_test_env.sh        # Database setup script
└── integration/             # Integration tests
    ├── test_entities.py     # Entity CRUD (6 tests)
    ├── test_tag_defs.py     # Tag definitions (5 tests)
    ├── test_entity_tags.py  # Entity-tag associations (5 tests)
    ├── test_values.py       # Value operations (5 tests)
    └── test_tag_meta.py     # Tag metadata (4 tests)
```

### Test Fixtures

Fixtures use simulator data from `conftest.py`:

- `client` - FastAPI test client
- `db` - Database session
- `simulator_org` - Organization created by simulator
- `simulator_entities` - Sample entities from simulator
- `simulator_tag_defs` - Tag definitions from simulator
- `cleanup_entity` - Helper to cleanup test entities
- `auth_headers` - Authentication headers (bypassed in local mode)

### Writing Tests

Tests should use simulator-generated data and create minimal additional entities:

**Read Test Example:**
```python
import pytest

@pytest.mark.integration
def test_list_entities(client, simulator_org):
    """Test GET /entity - Use simulator data"""
    response = client.get(f"/entity?org_id={simulator_org['id']}&limit=10")

    assert response.status_code == 200
    entities = response.json()
    assert len(entities) > 0
```

**Create Test Example:**
```python
import pytest

@pytest.mark.integration
def test_create_entity(client, simulator_org, cleanup_entity):
    """Test POST /entity - Create and cleanup"""
    payload = {
        "org_id": simulator_org["id"],
        "tags": [{"tag_name": "site", "value_s": "Test Site"}]
    }

    response = client.post("/entity", json=payload)

    assert response.status_code == 200
    entity = response.json()

    # Register for cleanup
    cleanup_entity.append(entity["id"])
```

### CI/CD Integration

Tests run automatically in GitHub Actions on:
- Push to main/develop branches
- Pull requests

CI workflow validates:
- All tests pass
- Code coverage > 80%
- No security vulnerabilities

### Test Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = test
python_files = test_*.py
markers =
    unit: Unit tests (business logic, utilities)
    integration: Integration tests (API + database)
    slow: Slow-running tests
    security: Security-related tests
    performance: Performance tests
asyncio_mode = auto
```

### Debugging Tests

```bash
# Verbose output with full details
pytest -vv

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Run only failed tests from last run
pytest --lf

# Stop on first failure
pytest -x
```

### Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Fixtures handle cleanup automatically via rollback
3. **Fast**: Unit tests should run quickly (< 1s total)
4. **Clear**: Use descriptive test names
5. **Markers**: Tag tests with appropriate markers
6. **Fixtures**: Reuse setup code via pytest fixtures
7. **Assertions**: Use clear assertion messages

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/databases

# Create entity (requires auth)
curl -X POST http://localhost:8000/entity \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "org_id": 1,
    "tags": [
      {"tag_def_id": "site", "value": "Building-A"},
      {"tag_def_id": "area", "value": "50000"}
    ]
  }'

# Get entities
curl "http://localhost:8000/entity?org_id=1&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📖 API Documentation

Once running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Complete endpoint documentation
- Request/response schemas
- Interactive testing interface
- Authentication flows

## 🔧 Development

### Adding New Endpoints

1. **Define Pydantic schemas** in `src/app/model/pydantic/`
```python
class MyDataCreate(BaseModel):
    name: str
    value: float
```

2. **Create endpoint** in `src/app/api/`
```python
@app.post("/mydata", response_model=MyDataSchema)
def create_mydata(data: MyDataCreate, db: Session = Depends(get_db)):
    return mydata_dto.create(db, data)
```

3. **Implement business logic** in `src/app/services/`
4. **Add database access** in `src/app/dto/`
5. **Write tests** in `test/`

### Database Migrations

```bash
# Connect to database
docker exec -it timescaledb psql -U datakwip_user -d datakwip

# Run schema updates
\i schema/01_sql_schema_core_v2.sql

# Verify tables
\dt core.*
```

## 🐛 Troubleshooting

### API won't start

**Check database connection:**
```bash
docker-compose up timescaledb
docker-compose logs timescaledb
```

**Check config.json:**
- Verify `dbUrl` matches database credentials
- Ensure `dbScheme` is set to `core`
- Check `CONFIG_KEY` environment variable

**Check logs:**
```bash
docker-compose logs api
```

### Authentication errors

**Local development:**
- Set `app_client_id: "local-dev-no-auth"` in config.json
- Set `user_pool_id: "local-dev-no-auth"` in config.json

**Production:**
- Configure AWS Cognito user pool
- Set correct `app_client_id` and `user_pool_id`
- Ensure JWT tokens are valid

### Database connection errors

**SCRAM authentication failure:**
- Upgrade psycopg2-binary to >= 2.9.9
- PostgreSQL 15+ requires SCRAM-SHA-256 support

**Schema not found:**
- Verify schema exists: `SELECT schema_name FROM information_schema.schemata;`
- Run schema creation: `psql -d datakwip -f schema/01_sql_schema_core_v2.sql`

**Table not found:**
- Check `dbScheme` config matches actual schema
- Verify org table exists and has `value_table` column
- Run: `SELECT * FROM core.org;`

### Performance issues

**Slow value queries:**
- Ensure hypertables are configured: `SELECT * FROM timescaledb_information.hypertables;`
- Add indexes on frequently queried columns
- Use bulk endpoints (`/bulk/value`) for batch operations

**High memory usage:**
- Reduce pagination `limit` parameter
- Use database connection pooling
- Monitor with `/health/databases` endpoint

## 🔐 Security & Authentication

### Authentication Overview

The API supports two authentication modes:

1. **Production**: AWS Cognito JWT token validation (SSO)
2. **Local Development**: Default user bypass (no authentication required)

The authentication system is implemented in the middleware layer and validates users before any endpoint logic executes.

### How Authentication Works

**Request Flow:**

```
1. Client sends request with Authorization header
   └─> Header format: "Authorization: Bearer <JWT_TOKEN>"

2. Middleware extracts token (request_service.py)
   └─> Validates header exists and has "Bearer " prefix
   └─> Returns 401 if missing

3. Token validation (user_service.py)
   └─> Downloads Cognito JWKS (public keys)
   └─> Verifies JWT signature using RS256 algorithm
   └─> Validates issuer and audience claims
   └─> Extracts email/username from token
   └─> Returns 403 if invalid

4. User lookup (user_service.py)
   └─> Finds user in database by email
   └─> Returns user_id
   └─> Returns 403 if user not found

5. Request proceeds with user_id attached to request.state
```

**Code Implementation:**

The authentication flow is implemented across three files:

- `api/src/app/main.py` (lines 118, 122-128) - Middleware
- `api/src/app/services/request_service.py` (lines 13-28) - Header extraction
- `api/src/app/services/acl/user_service.py` (lines 16-103) - JWT validation & user lookup

### Production Setup (AWS Cognito)

**Prerequisites:**
- AWS Cognito User Pool configured
- User Pool ID (e.g., `us-east-1_XXXXXXXXX`)
- App Client ID (e.g., `1a2b3c4d5e6f7g8h9i0j1k2l3m`)

**Configuration (config.json):**

```json
{
  "production": {
    "app_client_id": "YOUR_COGNITO_APP_CLIENT_ID",
    "user_pool_id": "YOUR_COGNITO_USER_POOL_ID",
    "dbUrl": "postgresql://user:pass@host:port/db?sslmode=require",
    ...
  }
}
```

**Cognito JWT Validation Process:**

1. **Extract Key ID from JWT header**
   ```python
   headers = jwt.get_unverified_header(token)
   kid = headers['kid']  # Key ID
   ```

2. **Download JWKS (JSON Web Key Set)**
   ```
   URL: https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json
   ```

3. **Find matching public key by kid**
   ```python
   public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching_key)
   ```

4. **Verify JWT signature and claims**
   ```python
   decoded = jwt.decode(
       token,
       public_key,
       algorithms=['RS256'],
       issuer=f"https://cognito-idp.us-east-1.amazonaws.com/{user_pool_id}",
       audience=app_client_id  # Only if 'aud' claim present
   )
   ```

5. **Extract user email/username**
   ```python
   user_email = decoded.get("email") or decoded.get("username")
   ```

**Required User Database Entry:**

Users must exist in the `core.user` table before authentication will succeed:

```sql
-- Create user
INSERT INTO core."user" (email)
VALUES ('user@example.com')
RETURNING id, email;

-- Add user to organization
INSERT INTO core.org_user (org_id, user_id)
VALUES (1, <user_id>);
```

**Example Authenticated Request:**

```bash
# Get Cognito token (example using AWS CLI or Cognito SDK)
TOKEN=$(aws cognito-idp initiate-auth ...)

# Make authenticated request
curl -X GET "http://localhost:8000/entity?org_id=1&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Local Development Setup (Default User)

For local development without AWS Cognito, you can configure a default user that bypasses authentication.

**Configuration (config.json):**

```json
{
  "local": {
    "app_client_id": "local-dev-no-auth",
    "user_pool_id": "local-dev-no-auth",
    "defaultUser": "test@datakwip.local",
    ...
  }
}
```

**Create Test User:**

```bash
# Connect to database
docker exec -it timescaledb psql -U datakwip_user -d datakwip

# Create user
INSERT INTO core."user" (email)
VALUES ('test@datakwip.local')
RETURNING id, email;
-- Returns: id=1, email='test@datakwip.local'

# Add to organization
INSERT INTO core.org_user (org_id, user_id)
VALUES (1, 1);
```

**How Default User Works:**

When `defaultUser` is configured:
1. Middleware checks if `defaultUser` is set in config
2. If set, skips token validation entirely
3. Looks up user by email directly
4. Attaches user_id to request

This allows testing API endpoints without managing JWT tokens.

**Example Request (No Auth Header Required):**

```bash
# Works without Authorization header
curl -X GET "http://localhost:8000/entity?org_id=1&limit=10"

# Also works with any header (ignored when defaultUser is set)
curl -X GET "http://localhost:8000/entity?org_id=1&limit=10" \
  -H "Authorization: Bearer any-value-ignored"
```

### Authorization Model

After authentication, the API enforces fine-grained authorization:

**Organization-Level Access:**
- Users must be members of an organization to access its data
- Stored in `core.org_user` table

**Entity Permissions:**
- Organization-level: `core.org_entity_permission`
- User add permission: `core.user_entity_add_permission`
- User revoke permission: `core.user_entity_rev_permission`

**Tag Permissions:**
- Organization-level: `core.org_tag_permission`
- User add permission: `core.user_tag_add_permission`
- User revoke permission: `core.user_tag_rev_permission`

**Permission Check Examples:**

```python
# Check if user can see entity (user_service.py:244-281)
is_entity_visible_for_user(db, org_id, user_id, entity_id)

# Check if user can see tag (user_service.py:193-242)
is_tag_visible_for_user(db, org_id, user_id, tag_id)

# Check if user is org admin (user_service.py:133-144)
is_user_org_admin(org_id, user_id, db)
```

### HTTP Status Codes

**Authentication/Authorization Errors:**

- **401 Unauthorized**: Missing or malformed Authorization header
  ```json
  {"detail": "Authorization header required"}
  ```

- **403 Forbidden**: Invalid token, user not found, or insufficient permissions
  ```json
  {"detail": "Invalid token"}
  {"detail": "not authorized"}
  {"detail": "the client is not authorized to access the op"}
  ```

- **500 Internal Server Error**: Server-side error (e.g., Cognito service unavailable)
  ```json
  {"detail": "Token validation service unavailable"}
  ```

### Troubleshooting Authentication

**Problem: Getting 401 - Authorization header required**

```bash
# Check if Authorization header is present
curl -v http://localhost:8000/entity?org_id=1

# Solution: Add Authorization header
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/entity?org_id=1
```

**Problem: Getting 403 - Invalid token**

Possible causes:
1. Token expired (Cognito tokens typically expire in 1 hour)
2. Token signature invalid (wrong public key)
3. Token issuer doesn't match configured user pool
4. Token audience doesn't match app client ID

```bash
# Decode token to inspect claims (without verification)
python3 << 'EOF'
import jwt
token = "YOUR_TOKEN_HERE"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
EOF

# Check:
# - exp: Expiration timestamp (must be in future)
# - iss: Must match https://cognito-idp.{region}.amazonaws.com/{user_pool_id}
# - aud: Must match app_client_id (if present)
# - email: Must exist in core.user table
```

**Problem: Getting 403 - not authorized (valid token)**

Cause: User email from token doesn't exist in database

```bash
# Extract email from token
EMAIL=$(python3 -c "import jwt; print(jwt.decode('YOUR_TOKEN', options={'verify_signature': False})['email'])")

# Check if user exists
docker exec -it timescaledb psql -U datakwip_user -d datakwip -c \
  "SELECT id, email FROM core.\"user\" WHERE email = '$EMAIL';"

# If not found, create user
docker exec -it timescaledb psql -U datakwip_user -d datakwip -c \
  "INSERT INTO core.\"user\" (email) VALUES ('$EMAIL') RETURNING id, email;"

# Add to organization
docker exec -it timescaledb psql -U datakwip_user -d datakwip -c \
  "INSERT INTO core.org_user (org_id, user_id) VALUES (1, <user_id>);"
```

**Problem: Local dev - want to skip authentication**

```bash
# 1. Edit api/config.json
{
  "local": {
    "defaultUser": "test@datakwip.local",  // Add this line
    ...
  }
}

# 2. Create test user (if doesn't exist)
docker exec -it timescaledb psql -U datakwip_user -d datakwip -c \
  "INSERT INTO core.\"user\" (email) VALUES ('test@datakwip.local') ON CONFLICT DO NOTHING RETURNING id;"

# 3. Add to org (if not already)
docker exec -it timescaledb psql -U datakwip_user -d datakwip -c \
  "INSERT INTO core.org_user (org_id, user_id) VALUES (1, 1) ON CONFLICT DO NOTHING;"

# 4. Rebuild API container
docker-compose up -d --build api

# 5. Test without auth header
curl http://localhost:8000/entity?org_id=1
```

**Problem: Cognito JWKS download fails**

```
Error: "Token validation service unavailable"
```

Causes:
- Network connectivity to AWS Cognito
- Incorrect region in user_service.py (line 29)
- Invalid user_pool_id

```bash
# Test JWKS URL manually
USER_POOL_ID="us-east-1_XXXXXXXXX"
curl "https://cognito-idp.us-east-1.amazonaws.com/$USER_POOL_ID/.well-known/jwks.json"

# Should return JSON with public keys
{"keys": [{"alg": "RS256", "kid": "...", ...}]}
```

**Debugging Tips:**

```bash
# 1. Check API logs
docker-compose logs api | grep -E "ERROR|JWT|auth"

# 2. Check middleware is catching exceptions properly
# Look for: "HTTPException" handler in logs

# 3. Verify config is loaded correctly
docker exec -it api python3 -c \
  "from app.services import config_service; print(config_service.default_user)"

# 4. Test health endpoint (no auth required)
curl http://localhost:8000/health
```

### Security Best Practices

**Production:**
- ✅ Always use HTTPS in production
- ✅ Set short JWT expiration times (1 hour recommended)
- ✅ Implement token refresh flow in client applications
- ✅ Never expose `app_client_id` secret (use public client for JWT)
- ✅ Regularly rotate Cognito signing keys
- ✅ Monitor failed authentication attempts
- ✅ Use AWS Cognito user groups for role-based access

**Local Development:**
- ⚠️ Only use `defaultUser` in local/dev environments
- ⚠️ Never deploy with `defaultUser` enabled to production
- ⚠️ Use `dk_env` environment variable to switch configs
- ⚠️ Keep test user credentials out of version control

### Data Protection

- SQL injection prevention (SQLAlchemy parameterization)
- Input validation (Pydantic models)
- Error message sanitization (no sensitive data in errors)
- HTTPS required in production
- Database credentials in environment variables only
- Request ID tracking for audit logging

## 📈 Monitoring

### Health Endpoints

```bash
# Basic health
curl http://localhost:8000/health
# Response: {"status": "ok"}

# Database health
curl http://localhost:8000/health/databases
# Response includes connection status for all databases
```

### Logging

- Structured JSON logging
- Request ID tracking
- Error stack traces
- Configurable log levels (info, debug, error)

## 🔗 Related Documentation

- [Test Documentation](test/README.md) - Detailed test coverage and testing guide
- [Implementation Status](../IMPLEMENTATION_STATUS.md)
- [Simulator Integration](../simulator/README.md)
- [Database Schema](../schema/01_sql_schema_core_v2.sql)
- [Docker Setup](../docs/DOCKER_LOCAL_SETUP.md)
- [Archived Reports](docs/archive/) - Historical cleanup reports and bug tracking

## 📝 Notes

- FastAPI auto-generates OpenAPI documentation
- Pydantic models provide request/response validation
- SQLAlchemy ORM for database interactions
- Multi-database support with automatic failover
- TimescaleDB for efficient time-series storage
- Follows Project Haystack v3 specification
- Production-ready with comprehensive error handling
