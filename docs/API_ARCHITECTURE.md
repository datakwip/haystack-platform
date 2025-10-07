# API Architecture Documentation

**Last Updated**: October 2025
**Source**: Technical conversation between Cory Perdue and Alexey Matveev, supplemented with codebase analysis

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture & Design](#2-architecture--design)
3. [Authentication Flow](#3-authentication-flow)
4. [Authorization & Permissions](#4-authorization--permissions)
5. [Database Connections](#5-database-connections)
6. [ANTLR Filter Implementation](#6-antlr-filter-implementation)
7. [API Endpoints](#7-api-endpoints)
8. [Schemas & Models](#8-schemas--models)
9. [Table Structure](#9-table-structure)
10. [Multi-Tenancy & Organization Management](#10-multi-tenancy--organization-management)
11. [Security Considerations](#11-security-considerations)
12. [Configuration Reference](#12-configuration-reference)

---

## 1. Overview

The Haystack Platform API (originally called "db-service-layer") is a FastAPI-based REST service providing authenticated access to building automation data stored in TimescaleDB. It serves as the primary data access layer for the platform.

### Technology Stack

- **Framework**: FastAPI (Python)
- **ORM**: SQLAlchemy for database models
- **Schema Validation**: Pydantic for request/response validation
- **Database**: PostgreSQL/TimescaleDB with hypertables for time-series data
- **Query Parser**: ANTLR4 for Project Haystack filter syntax
- **Authentication**: AWS Cognito with JWT tokens
- **Testing**: pytest with integration test suite (47% coverage)

### Key Features

- **Haystack Filter Queries**: Full ANTLR-based parser supporting Project Haystack filter syntax
- **Multi-Tenant Architecture**: Organization-level isolation with fine-grained permissions
- **Dual Database Connections**: Separate read/write connections for performance optimization
- **Time-Series Optimization**: Dynamic per-organization hypertables for scalable time-series storage
- **Fine-Grained ACL**: Entity-level and tag-level permissions with grant/revoke capabilities

---

## 2. Architecture & Design

### Directory Structure

```
api/
├── src/app/
│   ├── api/                    # API endpoints
│   │   ├── source_objects/     # Entity, tag, value endpoints
│   │   ├── acl/               # Access control list endpoints
│   │   ├── auth/              # Authentication endpoints
│   │   └── filter/            # Filter endpoint with ANTLR parser
│   │       └── antlr/         # ANTLR grammar and visitor implementation
│   ├── services/              # Business logic layer
│   │   ├── acl/              # ACL services (user permissions)
│   │   ├── entity_service.py
│   │   ├── tag_service.py
│   │   └── value_service.py
│   ├── dto/                   # Data transfer objects
│   │   └── source_objects/   # Entity, tag, value DTOs
│   ├── model/
│   │   ├── pydantic/          # API request/response schemas
│   │   └── sqlalchemy/        # Database ORM models
│   ├── db/                    # Database connection management
│   │   └── database.py       # Session handling
│   └── main.py               # FastAPI app initialization
├── test/
│   └── integration/           # Integration test suite (40 tests passing)
├── config.json               # Environment-specific configurations
└── requirements.txt          # Python dependencies
```

### Middleware Architecture

**Location**: `api/src/app/main.py:109-134`

The API uses HTTP middleware to handle cross-cutting concerns:

```python
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """
    1. Creates database session per request
    2. Extracts and validates user from JWT token
    3. Assigns request ID for logging/tracing
    4. Manages dual database connections (primary + grafana)
    """
    request.state.db = database.get_local_session()
    request.state.user_id = user_service.get_current_user(
        request,
        request.state.db,
        config_service.default_user
    )
    # ... request processing
    request.state.db.close()
```

**Key Responsibilities**:
1. **Session Management**: Creates/closes database sessions per request
2. **User Authentication**: Validates JWT and extracts user ID
3. **Request Tracing**: Assigns UUID to each request for logging
4. **Exception Handling**: Catches and logs all exceptions

### Separation of Concerns

**Three-Layer Architecture**:

1. **API Layer** (`api/`): FastAPI endpoints, request/response handling
2. **DTO Layer** (`dto/`): Business logic, validation, ACL checks
3. **Service Layer** (`services/`): Database operations, core business logic

**Data Flow**:
```
Request → Middleware → API Endpoint → DTO → Service → Database
                ↓
         (Auth & Session)
```

---

## 3. Authentication Flow

### JWT-Based Authentication with AWS Cognito

**Authentication is WHO you are. Authorization is WHAT you can access.**

### Step 1: Obtain JWT Token

**Endpoint**: `POST /authorize/token`

**Request**:
```http
POST /authorize/token
Authorization: Basic <base64(username:password)>
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Process**:
1. API receives Basic Auth credentials
2. API forwards to AWS Cognito for validation
3. Cognito validates credentials against user pool
4. Cognito returns signed JWT token
5. API passes token to client

### Step 2: Use JWT Token for API Requests

**Request**:
```http
GET /entity?org_id=1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Middleware Processing**:
1. Extract token from `Authorization: Bearer <token>` header
2. Decode JWT header to extract Key ID (`kid`)
3. Download Cognito JWKS (JSON Web Key Set) public keys
4. Verify JWT signature using RSA public key
5. Validate JWT claims (issuer, audience, expiration)
6. Extract user email/username from payload
7. Look up user in `core.user` table
8. Store `user_id` in `request.state.user_id` for endpoint access

### JWT Validation Process

**Location**: `api/src/app/services/acl/user_service.py:16-73`

**Validation Steps**:

```python
def verify_cognito_token(token: str) -> dict:
    """
    1. Decode JWT header (without verification) to get kid
    2. Fetch JWKS from Cognito well-known endpoint
    3. Find matching public key by kid
    4. Verify signature using RS256 algorithm
    5. Validate issuer matches Cognito user pool
    6. Validate audience matches app client ID
    7. Check expiration timestamp
    8. Return decoded payload with user email
    """
```

**Cognito JWKS Endpoint**:
```
https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json
```

**Security Guarantees**:
- ✅ Token signed by Cognito (prevents forgery)
- ✅ Token not expired (enforces session timeout)
- ✅ Token issued by correct user pool (prevents pool confusion)
- ✅ Token intended for this API (audience validation)

### Development Mode: Default User Bypass

**Configuration**: `config.json` → `"defaultUser": "test@datakwip.local"`

**When to Use**:
- Local development without Cognito
- Internal services on trusted network (e.g., data pollers)
- Integration testing

**Behavior**:
- Skip JWT validation entirely
- Use configured default user for all requests
- No `Authorization` header required

**Security Warning**:
⚠️ **NEVER use `defaultUser` in production or public-facing configs**

**Example Config**:
```json
{
  "local": {
    "defaultUser": "test@datakwip.local",
    "dbUrl": "postgresql://...",
    ...
  },
  "prod": {
    // NO defaultUser field - Cognito required
    "dbUrl": "postgresql://...",
    ...
  }
}
```

---

## 4. Authorization & Permissions

**Authorization Model**: Role-based access control (RBAC) with org-level and entity-level permissions

### Core Authorization Flow

**Every API endpoint follows this pattern**:

```python
@app.get("/entity/{entity_id}")
def get_entity(entity_id: str, org_id: int, request: Request, db: Session):
    user_id = request.state.user_id  # From middleware

    # Step 1: Check org-level access
    user_service.is_org_id_visible(db, org_id, user_id)

    # Step 2: Check entity-level access (if applicable)
    user_service.is_entity_visible_for_user(db, entity_id, user_id)

    # Step 3: Proceed with business logic
    return entity_service.get_entity(db, org_id, entity_id)
```

### Authorization Tables

**All tables in `core` schema**

#### 1. User Registry

**`core.user`**
- **Purpose**: Registry of all API users (not general users - API access only)
- **Key Fields**: `id`, `email`, `disabled_ts`
- **Relationship**: User email from JWT must exist in this table
- **Creation**: Manually added or via user management endpoints

**Important**: This is specifically for API access. A user in Cognito must also exist in this table to use the API.

#### 2. Organization Access

**`core.org_user`**
- **Purpose**: Links users to organizations they can access
- **Key Fields**: `user_id`, `org_id`
- **Primary Key**: Composite `(user_id, org_id)`
- **Logic**: User can ONLY access organizations listed in this table

**Example Query**:
```sql
SELECT * FROM core.org_user
WHERE user_id = 123 AND org_id = 1;
-- If no row returned → 403 Forbidden
```

**`core.org_admin`**
- **Purpose**: Grants admin privileges within an organization
- **Key Fields**: `user_id`, `org_id`
- **Usage**: Checked by `is_user_org_admin()` service function
- **Privileges**: Can manage users, entities, permissions within org

#### 3. Entity-Level Permissions

**Grant Tables** (allow access):

**`core.org_entity_permission`**
- Organization-wide entity access grants
- All users in org can access these entities

**`core.user_entity_add_permission`**
- Per-user entity access grants
- Specific user can access specific entity

**Revoke Tables** (deny access):

**`core.user_entity_rev_permission`**
- Per-user entity access denials
- Overrides org-wide and user-specific grants

**Authorization Logic**:
```
(org_entity_permission OR user_entity_add_permission)
AND NOT user_entity_rev_permission
```

#### 4. Tag-Level Permissions

**Same pattern as entity permissions**:

**Grant Tables**:
- `core.org_tag_permission` - Org-wide tag visibility
- `core.user_tag_add_permission` - Per-user tag grants

**Revoke Tables**:
- `core.user_tag_rev_permission` - Per-user tag denials

**Use Case**: Hide sensitive tags (e.g., `costPerKWh`) from certain users

### Service Layer Functions

**Location**: `api/src/app/services/acl/user_service.py`

**Key Functions**:

```python
# Org-level check (REQUIRED in every endpoint)
is_org_id_visible(db: Session, org_id: int, user_id: int)
# Raises AccessDeniedException if user not in org_user table

# Entity-level check
is_entity_visible_for_user(db: Session, entity_id: str, user_id: int)
# Checks org_entity_permission, user grants, user revokes

# Tag-level check
is_tag_visible_for_user(db: Session, tag_name: str, user_id: int)
# Similar logic for tag visibility

# Admin check
is_user_org_admin(db: Session, org_id: int, user_id: int)
# Returns True if user is org admin
```

### Critical Security Pattern

**⚠️ CRITICAL**: Every endpoint MUST check `is_org_id_visible()` before accessing any data.

**Good Example**:
```python
@app.get("/entity")
def get_entities(org_id: int, request: Request, db: Session):
    user_id = request.state.user_id
    is_org_id_visible(db, org_id, user_id)  # ✅ Security check
    return entity_service.list_entities(db, org_id)
```

**Bad Example** (security vulnerability):
```python
@app.get("/entity")
def get_entities(org_id: int, request: Request, db: Session):
    # ❌ MISSING SECURITY CHECK - ANY AUTHENTICATED USER CAN ACCESS!
    return entity_service.list_entities(db, org_id)
```

**Impact of Missing Check**: Any authenticated user could access any organization's data by changing `org_id` parameter.

---

## 5. Database Connections

### Dual Connection Architecture

**Purpose**: Separate read-heavy filter queries from write operations for performance optimization

### Connection 1: Main Database

**Config Field**: `dbUrl`

**Used For**:
- Write operations (POST, PUT, DELETE)
- Entity creation/updates
- Tag management
- Value inserts/updates

**Connection Pool**: Configurable size via `main_db_pool_size`

**Example**:
```json
{
  "dbUrl": "postgresql://user:pass@primary.db.host:5432/datakwip"
}
```

### Connection 2: Grafana Connector (Filter Database)

**Config Field**: `dbUrlGrafanaConnector`

**Used For**:
- Filter queries (`POST /filter`)
- Values filter queries (`POST /values`)
- Read-heavy operations
- Dashboard data fetching

**Connection Pool**: Configurable size via `grafana_db_pool_size`

**Original Design**: Point to read replica to offload query traffic

**Example**:
```json
{
  "dbUrl": "postgresql://user:pass@primary.db.host:5432/datakwip",
  "dbUrlGrafanaConnector": "postgresql://user:pass@replica.db.host:5432/datakwip"
}
```

### Configuration Patterns

**Development** (same database for both):
```json
{
  "local": {
    "dbUrl": "postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip",
    "dbUrlGrafanaConnector": "postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip"
  }
}
```

**Production** (separate replica):
```json
{
  "prod": {
    "dbUrl": "postgresql://user:pass@primary.example.com:5432/db",
    "dbUrlGrafanaConnector": "postgresql://user:pass@replica.example.com:5432/db"
  }
}
```

### Database Session Management

**Pattern**: Session per request (managed by middleware)

**Implementation**:
```python
# Middleware creates session
request.state.db = database.get_local_session()

# Endpoint uses session
@app.get("/entity")
def get_entities(request: Request, db: Session):
    db = request.state.db  # Use session from middleware
    # ... perform queries

# Middleware closes session (in finally block)
request.state.db.close()
```

**Benefits**:
- Automatic connection pooling
- Session cleanup on errors
- Thread-safe request isolation

### Multi-Database Support

**Feature**: API can connect to multiple databases simultaneously

**Use Case**: Different organizations on different database instances

**Implementation**: `available_configs` list in config service

**Example**:
```json
{
  "available_configs": [
    {
      "key": "primary",
      "dbUrl": "postgresql://...",
      "is_primary": true,
      "is_available": true
    },
    {
      "key": "secondary",
      "dbUrl": "postgresql://other_db/...",
      "is_primary": false,
      "is_available": true
    }
  ]
}
```

**Behavior**:
- **Primary database failure** → API won't start
- **Secondary database failure** → Log warning, continue without it

---

## 6. ANTLR Filter Implementation

### Overview

**Purpose**: Parse Project Haystack filter queries into SQL

**Key Feature**: Production-ready implementation already tested with Grafana plugin

**Technology**: ANTLR4 (ANother Tool for Language Recognition)

### Haystack Filter Syntax

**Grammar Source**: Directly from Project Haystack specification

**Grammar File**: `api/src/app/api/filter/antlr/dqql_grammar.g4`

### Supported Query Operations

#### 1. Marker Tags (Tag Exists)
```
site          → Has 'site' tag
equip         → Has 'equip' tag
point         → Has 'point' tag
```

#### 2. Logical Operators
```
site and equip              → Boolean AND
ahu or vav                  → Boolean OR
not temp                    → Boolean NOT
(ahu or vav) and point      → Parentheses for grouping
```

#### 3. Comparison Operators
```
temp > 72                   → Greater than
temp >= 70                  → Greater than or equal
temp < 80                   → Less than
temp <= 75                  → Less than or equal
dis == "Building A"         → Equality
dis != "Building B"         → Inequality
```

#### 4. Arrow Navigation (Relationship Traversal)
```
equipRef->siteName          → Follow reference to site, get siteName tag
equipRef->siteRef->geoCity  → Multi-level navigation
```

**Use Case**: Find all equipment in buildings in New York:
```
equip and equipRef->siteRef->geoCity == "New York"
```

#### 5. IN Lists
```
type in ("ahu", "vav", "fan")
```

#### 6. Data Types

**Supported Value Types**:
- **Boolean**: `true`, `false`
- **String**: `"value"` (double quotes)
- **Number**: `123`, `45.67`, `1e10`
- **Date**: `2025-10-06`
- **Time**: `14:30:00`
- **Reference**: `@ref-id`
- **URI**: `` `http://example.com` `` (backticks)

### ANTLR Grammar Structure

```antlr
expr : cond EOF ;

cond : condOr ;

condOr : condAnd (OR condAnd)* ;

condAnd : term (AND term)* ;

term : parens | has | missing | cmp ;

has : path ;                    // Tag exists

missing : NOT path ;            // Tag doesn't exist

cmp : path cmpOp val ;          // Comparison

path : NAME (ARROW NAME)* ;     // Supports arrow navigation
```

### SQL Translation Process

**Visitor Pattern**: ANTLR generates parse tree, custom visitor translates to SQL

**File**: `api/src/app/api/filter/antlr/dqqlVisitor.py`

**Translation Flow**:

```
Haystack Filter String
    ↓
ANTLR Parser (dqql_grammar.g4)
    ↓
Parse Tree
    ↓
DqqlVisitor (walks tree)
    ↓
SQL Query String
    ↓
Execute against database
```

### Example Translation

**Input Haystack Filter**:
```
site and ahu and temp
```

**Generated SQL** (simplified):
```sql
SELECT e.id, e.org_id
FROM core.entity e
WHERE e.org_id = :org_id
  AND EXISTS (
    SELECT 1 FROM core.entity_tag et
    WHERE et.entity_id = e.id AND et.tag_name = 'site'
  )
  AND EXISTS (
    SELECT 1 FROM core.entity_tag et
    WHERE et.entity_id = e.id AND et.tag_name = 'ahu'
  )
  AND EXISTS (
    SELECT 1 FROM core.entity_tag et
    WHERE et.entity_id = e.id AND et.tag_name = 'temp'
  )
```

### Arrow Navigation Example

**Filter**:
```
equip and equipRef->siteName == "Building A"
```

**SQL Translation** (simplified):
```sql
SELECT e.id
FROM core.entity e
WHERE EXISTS (
    SELECT 1 FROM core.entity_tag et
    WHERE et.entity_id = e.id AND et.tag_name = 'equip'
  )
  AND EXISTS (
    SELECT 1 FROM core.entity_tag et1
    WHERE et1.entity_id = e.id
      AND et1.tag_name = 'equipRef'
      AND EXISTS (
        SELECT 1 FROM core.entity_tag et2
        WHERE et2.entity_id = et1.value_r  -- Follow reference
          AND et2.tag_name = 'siteName'
          AND et2.value_s = 'Building A'
      )
  )
```

### Filter Endpoint

**Endpoint**: `POST /filter`

**Request Schema**:
```json
{
  "filter": "site and ahu and temp",
  "tags": ["id", "dis", "siteRef"],
  "orgId": 1
}
```

**Request Fields**:
- `filter` (string, required): Haystack filter expression
- `tags` (array, optional): Specific tags to return (performance optimization)
- `orgId` (int, required): Organization context for query

**Response Schema**:
```json
[
  {
    "entityId": "entity-123",
    "tags": {
      "id": "@entity-123",
      "dis": "AHU-1",
      "siteRef": "@site-456"
    }
  },
  {
    "entityId": "entity-124",
    "tags": {
      "id": "@entity-124",
      "dis": "AHU-2",
      "siteRef": "@site-456"
    }
  }
]
```

**Performance Tip**: Requesting specific `tags` (instead of all tags) significantly improves query performance and reduces response size.

### Values Filter Endpoint

**Endpoint**: `POST /values`

**Purpose**: Get time-series values for entities matching filter

**Request Schema**:
```json
{
  "filter": "point and temp and sensor",
  "dateFrom": "2025-10-01T00:00:00",
  "dateTo": "2025-10-06T23:59:59",
  "operation": "avg",
  "orgId": 1
}
```

**Additional Fields**:
- `dateFrom` / `dateTo`: Time range for values
- `operation`: Aggregation function (`avg`, `min`, `max`, `sum`, `count`)

**Use Case**: "Get average temperature for all temperature sensors in Building A for the past week"

**Filter Example**:
```
point and temp and sensor and equipRef->siteRef->dis == "Building A"
```

**Note**: This endpoint was developed and tested for Grafana plugin integration and is production-ready.

### Supported Features & Limitations

**✅ Fully Supported**:
- Tag existence checks
- Boolean logic (AND, OR, NOT)
- Comparison operators
- Arrow navigation (unlimited depth)
- Parentheses grouping
- All Haystack data types

**⚠️ Potential Limitations**:
- Complex nested queries may have performance implications
- Very deep arrow navigation may require query optimization
- Edge cases may need additional testing

**Recommendation**: Test complex queries for performance before production use

---

## 7. API Endpoints

### Entity Management

**File**: `api/src/app/api/source_objects/entity.py`

#### Create Entity

```http
POST /entity
Authorization: Bearer <token>
Content-Type: application/json

{
  "orgId": 1,
  "tags": [
    {"tag_name": "site", "value_s": null},
    {"tag_name": "dis", "value_s": "Building A"},
    {"tag_name": "area", "value_n": 50000.0},
    {"tag_name": "geoCity", "value_s": "New York"}
  ]
}
```

**Tag Value Fields** (all nullable):
- `value_s`: String values
- `value_n`: Numeric values
- `value_b`: Boolean values (`true`/`false`)
- `value_r`: Reference values (entity ID)
- `value_d`: Date values
- `value_t`: Time values
- `value_uri`: URI values

**Marker Tags**: Tag with all value fields null (just `tag_name`)

**Response**:
```json
{
  "id": "entity-abc123",
  "orgId": 1,
  "created_ts": "2025-10-06T14:30:00Z",
  "tags": [...]
}
```

#### List Entities

```http
GET /entity?org_id=1&skip=0&limit=100
Authorization: Bearer <token>
```

**Query Parameters**:
- `org_id` (required): Organization filter
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Page size (default: 100)

#### Get Entity by ID

```http
GET /entity/{entity_id}?org_id=1
Authorization: Bearer <token>
```

**Security Note**: Returns 403 (not 404) for non-existent entities to prevent ID enumeration attacks.

#### Update Entity

```http
PUT /entity/{entity_id}
Authorization: Bearer <token>

{
  "orgId": 1,
  "tags": [...]  // Updated tag list
}
```

#### Delete Entity

```http
DELETE /entity/{entity_id}
Authorization: Bearer <token>

{
  "orgId": 1
}
```

**Note**: Soft delete (sets `disabled_ts` timestamp)

### Tag Definition Endpoints

**File**: `api/src/app/api/source_objects/tag_def.py`

#### List Tag Definitions

```http
GET /tag_def?org_id=1&skip=0&limit=100
Authorization: Bearer <token>
```

**Purpose**: Get Project Haystack tag definitions (ontology)

**Returns**:
```json
[
  {
    "id": 1,
    "name": "site",
    "kind": "marker",
    "doc": "Site entity marker"
  },
  {
    "id": 2,
    "name": "ahu",
    "kind": "marker",
    "doc": "Air handling unit"
  }
]
```

**Data Source**: Manually imported from Project Haystack JSON files (one-time load)

**Note**: No automated sync with Project Haystack updates

### Entity Tag Endpoints

**File**: `api/src/app/api/source_objects/entity_tag.py`

#### List Entity Tags

```http
GET /entity_tag?org_id=1&entity_id=entity-123
Authorization: Bearer <token>
```

#### Create Tag

```http
POST /entity_tag
Authorization: Bearer <token>

{
  "entityId": "entity-123",
  "orgId": 1,
  "tag_name": "temp",
  "value_n": 72.5
}
```

#### Update Tag

```http
PUT /entity_tag/{tag_id}
Authorization: Bearer <token>

{
  "orgId": 1,
  "value_n": 73.2
}
```

#### Delete Tag

```http
DELETE /entity_tag/{tag_id}
Authorization: Bearer <token>

{
  "orgId": 1
}
```

### Value Endpoints

**File**: `api/src/app/api/source_objects/value.py`

#### Get Values for Entity

```http
GET /value/{entity_id}?org_id=1&skip=0&limit=1000
Authorization: Bearer <token>
```

**Optional Query Parameters**:
- `date_from`: Start timestamp (ISO 8601)
- `date_to`: End timestamp (ISO 8601)
- `skip`: Pagination offset
- `limit`: Number of values to return

**Response**:
```json
[
  {
    "entity_id": "entity-123",
    "ts": "2025-10-06T14:30:00Z",
    "value": 72.5
  },
  {
    "entity_id": "entity-123",
    "ts": "2025-10-06T14:45:00Z",
    "value": 73.1
  }
]
```

#### Create Single Value

```http
POST /value
Authorization: Bearer <token>

{
  "entityId": "entity-123",
  "orgId": 1,
  "ts": "2025-10-06T14:30:00Z",
  "value": 72.5
}
```

**Note**: Use bulk endpoint for better performance

#### Bulk Create Values (Recommended)

```http
POST /value/bulk
Authorization: Bearer <token>

{
  "orgId": 1,
  "values": [
    {
      "entityId": "entity-123",
      "ts": "2025-10-06T14:30:00Z",
      "value": 72.5
    },
    {
      "entityId": "entity-124",
      "ts": "2025-10-06T14:30:00Z",
      "value": 68.2
    }
  ]
}
```

**Performance**: Bulk operations use single database transaction, much faster than individual inserts

### Filter Endpoints

See [Section 6: ANTLR Filter Implementation](#6-antlr-filter-implementation) for detailed documentation.

### System Endpoints

**File**: `api/src/app/api/system.py`

#### Health Check

```http
GET /health
```

**No authentication required** (bypassed in middleware)

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-06T14:30:00Z"
}
```

### User & Organization Management

**File**: `api/src/app/api/acl/org/org.py`, `api/src/app/api/acl/user/user.py`

**Endpoints** (require admin privileges):
- `POST /org` - Create organization
- `GET /org` - List organizations
- `POST /user` - Create API user
- `POST /org_user` - Grant user access to org
- `DELETE /org_user` - Revoke user access to org

---

## 8. Schemas & Models

### Architecture Pattern

```
Pydantic Schemas (API Layer)
        ↓
Business Logic (DTO/Service Layer)
        ↓
SQLAlchemy Models (Database Layer)
```

### Pydantic Schemas

**Location**: `api/src/app/model/pydantic/`

**Purpose**:
- Define JSON structure for API requests
- Define JSON structure for API responses
- Automatic validation via FastAPI
- Type hints and IDE support
- Documentation generation (OpenAPI/Swagger)

**Directory Structure**:
```
pydantic/
├── source_objects/
│   ├── entity_schema.py      # Entity create/read schemas
│   ├── tag_def_schema.py     # Tag definition schemas
│   └── value_schema.py       # Value schemas
├── filter/
│   ├── filter_schema.py      # FilterRequest, FilterResponse
│   └── value_schema.py       # ValueRequest
└── acl/
    └── user/
        └── user_schema.py    # User management schemas
```

**Common Naming Patterns**:
- `*Create` - POST request schemas
- `*Update` - PUT request schemas
- `*` (base) - GET response schemas
- `*Delete` - DELETE request schemas

**Example Schema**:
```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EntityTagCreate(BaseModel):
    tag_name: str
    value_s: Optional[str] = None
    value_n: Optional[float] = None
    value_b: Optional[bool] = None
    value_r: Optional[str] = None

class EntityCreate(BaseModel):
    orgId: int
    tags: List[EntityTagCreate]

class Entity(BaseModel):
    id: str
    orgId: int
    tags: List[EntityTag]
    created_ts: datetime
    updated_ts: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enable ORM mode
```

**Validation Benefits**:
- Type checking (string, int, float, etc.)
- Required vs optional fields
- Custom validators
- Automatic error messages

### SQLAlchemy Models

**Location**: `api/src/app/model/sqlalchemy/`

**Purpose**:
- Define database table structures
- ORM mapping for queries
- Relationship definitions
- Auto-create tables on startup (if not exist)

**Directory Structure**:
```
sqlalchemy/
├── source_object_model.py    # Entity, TagDef, TagMeta, EntityTag
├── acl_org_model.py          # Org, OrgUser, OrgAdmin, permissions
├── acl_user_model.py         # User, user permissions
├── values_tables.py          # Dynamic value table management
├── base.py                   # SQLAlchemy Base class
└── dynamic_value_tables.py   # Org-specific value tables
```

**Example Model**:
```python
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Entity(Base):
    __tablename__ = 'entity'
    __table_args__ = {'schema': 'core'}

    id = Column(String, primary_key=True)
    org_id = Column(Integer, ForeignKey('core.org.id'), nullable=False)
    created_ts = Column(DateTime, default=datetime.utcnow)
    updated_ts = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    disabled_ts = Column(DateTime, nullable=True)

    # Relationships
    tags = relationship("EntityTag", back_populates="entity")
    org = relationship("Org", back_populates="entities")
```

**Relationship Patterns**:
- `relationship()` - Defines ORM relationships
- `back_populates` - Bidirectional relationships
- `lazy='select'` - Load strategy (default)

### Dynamic Table Management

**Challenge**: Each organization has separate value tables

**Example**:
- Org key: `"demo"` → `values_demo` table
- Org key: `"green_gen"` → `values_green_gen` table

**Solution**: Dynamic SQLAlchemy table creation

**File**: `api/src/app/model/sqlalchemy/values_tables.py`

**Pattern**:
```python
# Dictionary of dynamically created table classes
value_tables = {}

def get_value_table_for_org(org_key: str):
    """
    Returns SQLAlchemy model class for org-specific value table
    Creates table class dynamically if not cached
    """
    if org_key not in value_tables:
        table_name = f"values_{org_key}"

        # Create dynamic class
        attrs = {
            '__tablename__': table_name,
            '__table_args__': {'schema': 'core'},
            'entity_id': Column(String, primary_key=True),
            'ts': Column(DateTime(timezone=True), primary_key=True),
            'value': Column(Numeric),
        }

        ValueTable = type(
            f'Values_{org_key}',
            (Base,),
            attrs
        )

        value_tables[org_key] = ValueTable

    return value_tables[org_key]
```

**Usage**:
```python
# In value_service.py
ValueTable = get_value_table_for_org(org_key)
results = db.query(ValueTable).filter(
    ValueTable.entity_id == entity_id,
    ValueTable.ts >= date_from,
    ValueTable.ts <= date_to
).all()
```

---

## 9. Table Structure

### Core Schema

**Schema Name**: `core` (configurable via `dbScheme` in config)

**All application tables reside in this schema**

### Source Object Tables

#### `core.entity`

Primary table for all entities (sites, equipment, points, etc.)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | string | PK | UUID or custom identifier |
| `org_id` | int | FK → org.id, NOT NULL | Organization ownership |
| `created_ts` | timestamp | NOT NULL, default now() | Creation timestamp |
| `updated_ts` | timestamp | nullable | Last modification timestamp |
| `disabled_ts` | timestamp | nullable | Soft delete timestamp |

**Indexes**:
- Primary key on `id`
- Index on `org_id` (frequent filter)
- Index on `disabled_ts` (null = active)

#### `core.entity_tag`

Tags attached to entities (wide table with nullable value columns)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | int | PK, auto-increment | Internal ID |
| `entity_id` | string | FK → entity.id, NOT NULL | Parent entity |
| `tag_name` | string | NOT NULL | Tag name (not FK) |
| `value_s` | string | nullable | String values |
| `value_n` | numeric | nullable | Numeric values |
| `value_b` | boolean | nullable | Boolean values |
| `value_r` | string | nullable | Reference values (entity IDs) |
| `value_d` | date | nullable | Date values |
| `value_t` | time | nullable | Time values |
| `value_uri` | string | nullable | URI values |

**Design Pattern**: Wide table with nullable columns for different value types

**Marker Tags**: Row with all value columns null (just tag_name)

**Indexes**:
- Primary key on `id`
- Index on `(entity_id, tag_name)` (frequent lookup)
- Index on `tag_name` (filter queries)

#### `core.tag_def`

Project Haystack tag definitions (ontology)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | int | PK, auto-increment | Internal ID |
| `name` | string | UNIQUE, NOT NULL | Tag name (e.g., "site", "ahu") |
| `kind` | string | NOT NULL | Data type (marker, number, str, ref) |
| `doc` | string | nullable | Documentation string |
| `disabled_ts` | timestamp | nullable | Soft delete |

**Data Source**: Manually imported from Project Haystack JSON files

#### `core.tag_meta`

Metadata about tag definitions (attributes like `lib:`, `doc:`)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | int | PK | Internal ID |
| `tag_id` | int | FK → tag_def.id | Tag being described |
| `attribute` | int | FK → tag_def.id | Attribute tag (e.g., "lib") |
| `value` | int | FK → tag_def.id | Value tag |

**Example**: Tag "site" has attribute "lib" with value "ph" (Project Haystack library)

### ACL Tables

#### `core.org`

Organizations (tenants)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | int | PK, auto-increment | Internal ID |
| `key` | string | UNIQUE, NOT NULL | Org identifier (e.g., "demo") |
| `name` | string | NOT NULL | Display name |
| `created_ts` | timestamp | NOT NULL | Creation timestamp |
| `disabled_ts` | timestamp | nullable | Soft delete |

**Org Key Usage**: Used for dynamic table naming (`values_{key}`)

#### `core.user`

API users (not general users - API access only)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | int | PK, auto-increment | Internal ID |
| `email` | string | UNIQUE, NOT NULL | Must match Cognito email |
| `created_ts` | timestamp | NOT NULL | Creation timestamp |
| `disabled_ts` | timestamp | nullable | Account disabled |

**Critical**: User in Cognito must also exist here to access API

#### `core.org_user`

User-to-organization access mapping

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | int | FK → user.id, NOT NULL | User |
| `org_id` | int | FK → org.id, NOT NULL | Organization |
| (composite PK) | | | `(user_id, org_id)` |

**Authorization**: User can ONLY access orgs in this table

#### `core.org_admin`

Organization administrators

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | int | FK → user.id, NOT NULL | User |
| `org_id` | int | FK → org.id, NOT NULL | Organization |
| (composite PK) | | | `(user_id, org_id)` |

**Privileges**: Can manage users, entities, permissions within org

#### Permission Tables

**Entity Permissions**:
- `core.org_entity_permission` - Org-wide entity grants
- `core.user_entity_add_permission` - Per-user entity grants
- `core.user_entity_rev_permission` - Per-user entity revokes

**Tag Permissions**:
- `core.org_tag_permission` - Org-wide tag grants
- `core.user_tag_add_permission` - Per-user tag grants
- `core.user_tag_rev_permission` - Per-user tag revokes

**Schema** (similar for all):
| Column | Type | Description |
|--------|------|-------------|
| `user_id` or `org_id` | int | User or org |
| `entity_id` or `tag_name` | string | Resource identifier |

### Time-Series Value Tables

**Dynamic Naming**: `values_{org_key}`

**Example**:
- Org key "demo" → `core.values_demo`
- Org key "green_gen" → `core.values_green_gen`

#### `core.values_{org_key}`

TimescaleDB hypertable for time-series data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `entity_id` | string | NOT NULL | FK to entity.id |
| `ts` | timestamp with tz | NOT NULL | Time dimension |
| `value` | numeric | nullable | Measurement value |
| (composite PK) | | | `(entity_id, ts)` |

**TimescaleDB Hypertable**: Automatically partitioned by time

**Indexes**:
- Primary key on `(entity_id, ts)`
- Index on `ts` (time-based queries)

#### `core.values_{org_key}_current`

Latest value per entity (optimization)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `entity_id` | string | PK | FK to entity.id |
| `ts` | timestamp with tz | NOT NULL | Latest timestamp |
| `value` | numeric | nullable | Latest value |

**Purpose**: Optimize "get current reading" queries (no time-series scan)

### Schema Initialization

**Process**:
1. SQL files in `/schema/` directory define initial schema
2. SQLAlchemy models in code
3. On startup: `Base.metadata.create_all()` creates missing tables

**Note**: Schema usually created by SQL initialization files, not auto-create

**File**: `api/src/app/main.py:97` (currently commented out)

---

## 10. Multi-Tenancy & Organization Management

### Multi-Tenancy Strategy

**Approach**: Hybrid isolation (schema-level + application-level)

### Organization Model

**Table**: `core.org`

**Key Fields**:
- `id` - Integer primary key (internal)
- `key` - String identifier (external, used for table naming)
- `name` - Display name

**Example**:
| id | key | name |
|----|-----|------|
| 1 | demo | Demo Organization |
| 2 | green_gen | Green Generation Energy |

### Isolation Layers

#### Layer 1: Application-Level Isolation (Standard)

**Pattern**: All orgs in same schema, filtered by `org_id`

**Enforcement**: Every query includes `WHERE org_id = :org_id`

**Authorization**: `org_user` table controls access

**Example Query**:
```sql
SELECT * FROM core.entity
WHERE org_id = :org_id
  AND id = :entity_id
  AND EXISTS (
    SELECT 1 FROM core.org_user
    WHERE user_id = :user_id AND org_id = :org_id
  )
```

**Strengths**:
- Simple to manage
- Efficient queries
- Easy data migration

**Risks**:
- Relies on application code for isolation
- Missing `WHERE org_id` = cross-org leakage

#### Layer 2: Value Table Separation (Hybrid)

**Pattern**: Each org has separate value tables

**Naming**: `values_{org_key}`

**Example**:
- Org "demo" → `core.values_demo`
- Org "green_gen" → `core.values_green_gen`

**Benefits**:
- Performance (smaller tables, better indexes)
- Easier backup/restore per org
- Physical separation of time-series data
- Independent retention policies per org

**Implementation**:
```python
# Dynamic table lookup
org_key = get_org_key(org_id)
table_name = f"values_{org_key}"
ValueTable = value_tables[org_key]

# Query org-specific table
values = db.query(ValueTable).filter(
    ValueTable.entity_id == entity_id
).all()
```

#### Layer 3: Schema Separation (Optional)

**Pattern**: Different orgs use different database schemas

**Configuration**: `dbScheme` field in config

**Example**:
- Org "demo" → schema `core_demo`
- Org "green_gen" → schema `core_greengen`

**Benefits**:
- Physical separation at database level
- Impossible cross-org queries (different schemas)
- Independent schema evolution per org

**Drawbacks**:
- Complex management (multiple schemas)
- Harder cross-org analytics
- Schema migrations multiply

**Use Case**: High-security orgs requiring strict isolation

### Organization Access Control

**Critical Function**: `is_org_id_visible(db, org_id, user_id)`

**Location**: `api/src/app/services/acl/user_service.py`

**Implementation**:
```python
def is_org_id_visible(db: Session, org_id: int, user_id: int) -> bool:
    """
    Verify user has access to organization
    Raises AccessDeniedException if not authorized
    """
    result = db.query(OrgUser).filter(
        OrgUser.user_id == user_id,
        OrgUser.org_id == org_id
    ).first()

    if result is None:
        raise AccessDeniedException(
            detail=f"User {user_id} cannot access org {org_id}"
        )

    return True
```

**Usage Pattern** (REQUIRED in every endpoint):
```python
@app.get("/entity")
def get_entities(org_id: int, request: Request, db: Session):
    user_id = request.state.user_id
    is_org_id_visible(db, org_id, user_id)  # ✅ Security check
    return entity_service.list_entities(db, org_id)
```

### Multi-Database Support

**Feature**: API can connect to multiple databases simultaneously

**Configuration**: `available_configs` list

**Example**:
```json
{
  "available_configs": [
    {
      "key": "primary",
      "dbUrl": "postgresql://primary.db:5432/db1",
      "dbScheme": "core",
      "is_primary": true,
      "is_available": true
    },
    {
      "key": "secondary",
      "dbUrl": "postgresql://secondary.db:5432/db2",
      "dbScheme": "core",
      "is_primary": false,
      "is_available": true
    }
  ]
}
```

**Behavior**:
- **Primary database unavailable** → API startup fails
- **Secondary database unavailable** → Log warning, continue without it
- **Per-request database routing** → Based on org configuration

---

## 11. Security Considerations

### Authentication Security

**Strengths**:
- ✅ JWT signature verification (prevents token forgery)
- ✅ Issuer validation (prevents token substitution)
- ✅ Audience validation (prevents token reuse)
- ✅ Expiration checking (enforces session timeout)
- ✅ HTTPS required in production (prevents token interception)

**Token Lifetime**:
- Cognito default: 1 hour
- Configurable in Cognito user pool settings
- Expired tokens rejected with 403 Forbidden

**Recommendations**:
- Use short token lifetimes (< 1 hour)
- Implement token refresh flow for long-running clients
- Log all authentication failures
- Monitor for suspicious token usage patterns

### Authorization Security

**Strengths**:
- ✅ Org-level isolation via `org_user` table
- ✅ Entity-level permissions (grant/revoke tables)
- ✅ Tag-level permissions (hide sensitive data)
- ✅ Schema separation option for strict isolation
- ✅ Multiple isolation layers (defense in depth)

**Risks & Mitigations**:

#### Risk 1: Missing Authorization Checks

**Risk**: Developer forgets `is_org_id_visible()` check

**Impact**: Any authenticated user can access any org's data

**Example Vulnerable Code**:
```python
@app.get("/entity")
def get_entities(org_id: int, db: Session):
    # ❌ MISSING: is_org_id_visible() check
    return db.query(Entity).filter(Entity.org_id == org_id).all()
```

**Mitigations**:
- Code review checklist (require org check in every endpoint)
- Integration tests for cross-org access denial
- Automated linting/static analysis for missing checks
- Middleware enforcement (future enhancement)

#### Risk 2: Application Logic Dependency

**Risk**: All security enforced in Python code, not database

**Impact**: Code bug = security bypass

**Mitigations**:
- Comprehensive test coverage (especially auth/z)
- Schema separation for critical orgs
- Regular security audits
- Principle of least privilege (limit API user DB permissions)

#### Risk 3: Single Database User

**Risk**: API uses one DB user for all requests

**Impact**: Database audit logs don't show end users

**Mitigations**:
- Application-level audit logging (track user actions)
- Log all data modifications with user_id
- Periodic audit log review

### SQL Injection Prevention

**Protection Mechanisms**:
- ✅ SQLAlchemy ORM (parameterized queries)
- ✅ ANTLR parser (validates syntax before SQL generation)
- ✅ No raw SQL string concatenation
- ✅ Pydantic validation (type checking)

**Example Safe Query**:
```python
# SQLAlchemy automatically parameterizes
db.query(Entity).filter(Entity.id == entity_id).first()

# Generates: SELECT * FROM entity WHERE id = :id
# Parameters: {'id': 'entity-123'}
```

**Filter Query Safety**:
- ANTLR validates filter syntax before SQL generation
- Invalid filters rejected with 400 Bad Request
- No user input directly interpolated into SQL

### Input Validation

**Pydantic Validation**:
- Type checking (prevents type confusion attacks)
- String length limits (prevents DoS via large inputs)
- Email validation (proper format)
- Enum validation (only allowed values)

**Example**:
```python
class EntityCreate(BaseModel):
    orgId: int  # Must be integer
    tags: List[EntityTagCreate]  # Must be array

    @validator('tags')
    def validate_tags_length(cls, v):
        if len(v) > 1000:
            raise ValueError("Too many tags (max 1000)")
        return v
```

### CSRF Protection

**Not Needed**: API uses JWT bearer tokens (not cookies)

**Why**: CSRF attacks rely on browsers automatically sending cookies

**Token Storage**: Client stores JWT in memory or localStorage, explicitly sends in header

### Rate Limiting

**Current Status**: ❌ Not implemented

**Recommendations**:
- Add rate limiting middleware (e.g., `slowapi`)
- Limits per user (e.g., 100 requests/minute)
- Limits per org (e.g., 10,000 requests/hour)
- Stricter limits for expensive operations (filter queries)

**Example Implementation**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/filter")
@limiter.limit("10/minute")
def filter_endpoint(...):
    ...
```

### Audit Logging

**Current Logging**:
- Request IDs (UUID per request)
- User IDs (from JWT)
- Error details and stack traces
- Request/response timing

**Missing** (recommendations):
- Successful data access events
- Data modifications (create/update/delete)
- Permission changes
- Authorization failures (who tried to access what)

**Recommended Enhancement**:
```python
# Audit log example
audit_logger.info({
    "event": "entity_create",
    "user_id": user_id,
    "org_id": org_id,
    "entity_id": entity_id,
    "timestamp": datetime.utcnow(),
    "request_id": request.state.request_id
})
```

### Security Best Practices

**✅ DO**:
- Always check `is_org_id_visible()` in endpoints
- Use HTTPS in production
- Rotate credentials regularly
- Store secrets in environment variables
- Log authentication/authorization failures
- Implement rate limiting
- Use short JWT expiration times

**❌ DON'T**:
- Use `defaultUser` in production
- Store credentials in config files
- Skip authorization checks for "internal" endpoints
- Trust client-provided `user_id` (always use `request.state.user_id`)
- Log sensitive data (passwords, tokens)
- Use same database user for all tenants (if possible)

---

## 12. Configuration Reference

### Environment-Based Configuration

**Config File**: `api/config.json`

**Environment Selection**: `dk_env` environment variable

**Example**:
```bash
export dk_env=local
python api/src/app/main.py
# Loads config.json["local"]
```

**Priority**:
1. Environment variables (highest)
2. `config.json[dk_env]`
3. Default values (lowest)

### Local Development Configuration

```json
{
  "local": {
    "dbUrl": "postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip",
    "dbUrlGrafanaConnector": "postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip",
    "dbScheme": "core",
    "defaultUser": "test@datakwip.local",
    "logLevel": "info",
    "loadDataFromCsv": false,
    "main_db_pool_size": 5,
    "grafana_db_pool_size": 10,
    "app_client_id": "local-dev-no-auth",
    "user_pool_id": "local-dev-no-auth"
  }
}
```

**Key Fields**:
- `defaultUser`: Bypass Cognito (dev only) ⚠️
- `app_client_id` / `user_pool_id`: Dummy values when not using Cognito
- Same DB for read/write (dev simplicity)
- Debug logging enabled

### Production Configuration

```json
{
  "prod": {
    "dbUrl": "postgresql://user:pass@primary.db.example.com:5432/datakwip",
    "dbUrlGrafanaConnector": "postgresql://user:pass@replica.db.example.com:5432/datakwip",
    "dbScheme": "core",
    "logLevel": "warning",
    "main_db_pool_size": 20,
    "grafana_db_pool_size": 50,
    "app_client_id": "abc123xyz456",
    "user_pool_id": "us-east-1_ABC123XYZ"
  }
}
```

**Key Differences**:
- ❌ NO `defaultUser` (Cognito required)
- Separate replica for filter queries (performance)
- Real Cognito credentials
- Higher log level (less verbose)
- Larger connection pools (production traffic)

### Configuration Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dbUrl` | string | Yes | Primary database connection string |
| `dbUrlGrafanaConnector` | string | Yes | Read replica connection string |
| `dbScheme` | string | Yes | Database schema name (default: "core") |
| `defaultUser` | string | No | Bypass auth user (dev only) |
| `logLevel` | string | No | Logging level (debug, info, warning, error) |
| `loadDataFromCsv` | boolean | No | Load initial data on startup |
| `main_db_pool_size` | int | No | Primary DB connection pool size |
| `grafana_db_pool_size` | int | No | Replica DB connection pool size |
| `app_client_id` | string | Yes* | Cognito app client ID (*if using Cognito) |
| `user_pool_id` | string | Yes* | Cognito user pool ID (*if using Cognito) |

### Environment Variable Overrides

**Pattern**: Config values can be overridden by environment variables

**Example**:
```bash
export DATABASE_URL="postgresql://..."
export DK_ENV="prod"
export LOG_LEVEL="debug"
```

**Override Priority**:
1. `DATABASE_URL` environment variable
2. `config.json[dk_env]["dbUrl"]`
3. Default value

### Configuration Service

**File**: `api/src/app/services/config_service.py`

**Responsibilities**:
- Load config.json
- Parse environment variables
- Provide config values to application
- Validate required fields

**Usage**:
```python
from app.services import config_service

db_url = config_service.dbUrl
default_user = config_service.default_user
```

---

## Development Workflow

### Local Setup

**Prerequisites**:
1. Docker & Docker Compose
2. Python 3.9+
3. Conda (recommended) or pip

**Steps**:
```bash
# 1. Clone repository
git clone <repo-url>
cd haystack-platform

# 2. Set up Python environment
conda env create -f environment.yml
conda activate haystack-platform

# 3. Start databases
docker compose up -d timescaledb statedb

# 4. Run API
cd api
export dk_env=local
python src/app/main.py

# API now running on http://localhost:8000
```

### Testing Without Cognito

**Method 1: Default User (Recommended for Dev)**

1. Add to `config.json`:
```json
{
  "local": {
    "defaultUser": "test@datakwip.local",
    ...
  }
}
```

2. Ensure user exists in database:
```sql
INSERT INTO core.user (email, created_ts)
VALUES ('test@datakwip.local', NOW());

INSERT INTO core.org_user (user_id, org_id)
VALUES (
  (SELECT id FROM core.user WHERE email = 'test@datakwip.local'),
  1  -- Org ID
);
```

3. Make requests without `Authorization` header

**Method 2: Manual JWT Creation (Advanced)**

Not recommended - requires Cognito setup or JWT signing

### Adding New Endpoints

**Checklist**:
1. ✅ Create Pydantic schemas (`model/pydantic/`)
2. ✅ Create SQLAlchemy models (if new tables)
3. ✅ Create endpoint in `api/`
4. ✅ Add `is_org_id_visible()` authorization check
5. ✅ Create service layer logic (`services/`)
6. ✅ Add integration tests (`test/integration/`)
7. ✅ Update documentation

**Example Endpoint**:
```python
# api/src/app/api/source_objects/custom.py

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.model.pydantic.custom_schema import CustomCreate, Custom
from app.services.acl import user_service
from app.services import custom_service
from app.db.database import get_db

@app.post("/custom", response_model=Custom)
def create_custom(
    data: CustomCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        user_id = request.state.user_id

        # CRITICAL: Authorization check
        user_service.is_org_id_visible(db, data.orgId, user_id)

        # Business logic
        result = custom_service.create(db, data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Running Tests

```bash
# All integration tests
pytest test/integration/ -v

# Specific test file
pytest test/integration/test_entity.py -v

# With coverage report
pytest test/integration/ --cov=app --cov-report=html

# Current status: 40/40 tests passing, 47% coverage
```

---

## Common Issues & Troubleshooting

### Issue 1: "User not authorized for org"

**Symptom**: 403 Forbidden when accessing endpoint

**Causes**:
1. User not in `core.user` table
2. User not in `core.org_user` for specified org
3. JWT email doesn't match database user email

**Solution**:
```sql
-- Check user exists
SELECT * FROM core.user WHERE email = 'user@example.com';

-- Check org access
SELECT * FROM core.org_user WHERE user_id = <user_id> AND org_id = <org_id>;

-- Grant access if missing
INSERT INTO core.org_user (user_id, org_id)
VALUES (<user_id>, <org_id>);
```

### Issue 2: "ANTLR filter syntax error"

**Symptom**: 400 Bad Request on filter endpoint

**Causes**:
1. Invalid Haystack filter syntax
2. Unsupported operator
3. Malformed query

**Solution**:
- Validate syntax against Haystack specification
- Check for balanced parentheses
- Ensure proper quoting of strings

**Example Valid Queries**:
```
site
site and equip
equip and (ahu or vav)
temp > 72
equipRef->siteName == "Building A"
```

### Issue 3: "Cannot connect to database"

**Symptom**: Connection refused or timeout errors

**Causes**:
1. Database not running
2. Wrong connection string
3. Firewall blocking connection

**Solution**:
```bash
# Check database is running
docker compose ps

# Test connection
psql postgresql://user:pass@host:5432/db

# Check config
echo $dk_env
cat config.json | jq ".$dk_env.dbUrl"
```

---

## Future Enhancements

### Short-Term Priorities

1. **Rate Limiting**
   - Per-user limits
   - Per-org limits
   - Endpoint-specific limits

2. **Audit Logging**
   - Log all data modifications
   - Log authorization failures
   - Structured logging format

3. **OpenAPI Documentation**
   - Generate from Pydantic schemas
   - Interactive API explorer
   - Client SDK generation

### Medium-Term Goals

1. **Database Migrations**
   - Add Alembic for schema versioning
   - Automated migration scripts
   - Rollback capabilities

2. **Performance Optimization**
   - Query performance analysis
   - Index optimization
   - Connection pool tuning

3. **Enhanced Testing**
   - Unit test coverage > 80%
   - Load testing
   - Security testing (OWASP)

### Long-Term Vision

1. **Row-Level Security**
   - Investigate PostgreSQL RLS compatibility
   - Benchmark performance impact
   - Hybrid application + database security

2. **Multi-Region Support**
   - Database replication across regions
   - API deployment in multiple regions
   - Geo-routing for performance

3. **GraphQL API**
   - Alternative to REST
   - Flexible query capabilities
   - Reduced over-fetching

---

## Appendix

### Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Project overview and current status
- **[IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)** - Roadmap and next steps
- **[SERVICE_MODE_SUMMARY.md](SERVICE_MODE_SUMMARY.md)** - Simulator service documentation
- **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** - Deployment guide

### External Resources

- **Project Haystack**: https://project-haystack.org/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **ANTLR4 Documentation**: https://github.com/antlr/antlr4/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **AWS Cognito JWT Verification**: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html

### Contact Information

**Original Development**: Alexey Matveev
**Documentation Source**: Technical conversation transcript (October 2025)
**Maintained By**: Datakwip Platform Team

---

**Last Updated**: October 2025
**Version**: 1.0
**Status**: Production-Ready API with 40/40 integration tests passing
