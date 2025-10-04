# Implementation Status - Haystack Platform

**Last Updated:** 2025-10-04
**Status:** Monorepo Structure Complete ✅ | API Integration Pending ⏳

---

## ✅ Completed

### Infrastructure
- [x] Created monorepo structure (api/, simulator/, webapp/)
- [x] Set up GitHub repository: https://github.com/datakwip/haystack-platform
- [x] Integrated db-service-layer as `api/`
- [x] Moved simulator code to `simulator/`
- [x] Created webapp skeleton (Next.js + TypeScript)
- [x] Updated docker-compose.yaml for all services
- [x] Configured two-database architecture (TimescaleDB + PostgreSQL)

### Documentation
- [x] Created comprehensive API_EXTENSION_PLAN.md
- [x] Analyzed db-service-layer in DB_SERVICE_LAYER_ANALYSIS.md
- [x] Updated CLAUDE.md for monorepo development
- [x] Created migration guide (MIGRATION_TO_MONOREPO.md)
- [x] Documented pre-deployment review

### Database Architecture
- [x] Separated building data (TimescaleDB) from simulator state (PostgreSQL)
- [x] Created simulator_state table schema
- [x] Dynamic table name support (no hardcoded values)
- [x] Hypertable setup for time-series data

---

## ⏳ Phase 1: API Integration (NEXT - HIGH PRIORITY)

### 1.1 Add Simulator Endpoints to API

**Status:** 📋 Not Started
**Location:** `api/src/app/api/simulator/`

**Tasks:**
- [ ] Create `api/src/app/api/simulator/simulator_api.py`
  - [ ] `POST /simulator/config` - Create/update simulator config
  - [ ] `GET /simulator/config` - List simulator configs
  - [ ] `GET /simulator/config/{sim_id}` - Get specific config
  - [ ] `GET /simulator/state/{sim_id}` - Get operational state
  - [ ] `POST /simulator/state/{sim_id}` - Update state
  - [ ] `GET /simulator/health/{sim_id}` - Health check
  - [ ] `GET /simulator/activity/{sim_id}` - Activity log
  - [ ] `POST /simulator/start/{sim_id}` - Start simulator
  - [ ] `POST /simulator/stop/{sim_id}` - Stop simulator
  - [ ] `POST /simulator/reset/{sim_id}` - Reset data

**See:** `API_EXTENSION_PLAN.md` lines 140-271 for detailed code examples

### 1.2 Add State Database Connection

**Status:** 📋 Not Started
**Location:** `api/src/app/services/config_service.py`, `api/src/app/main.py`

**Tasks:**
- [ ] Add STATE_DB_URL to `config_service.py`
- [ ] Initialize state database connection in `main.py`
- [ ] Add state_db to request middleware
- [ ] Create `get_state_db()` dependency function

**See:** `API_EXTENSION_PLAN.md` lines 152-180

### 1.3 Create Simulator Service Layer

**Status:** 📋 Not Started
**Location:** `api/src/app/services/`

**Tasks:**
- [ ] Create `simulator_config_service.py`
  - Register simulator as poller_type='simulator'
  - CRUD operations for simulator configs
- [ ] Create `simulator_state_service.py`
  - Read/write simulator_state table
  - Manage totalizers and last run timestamps
- [ ] Create `simulator_activity_service.py`
  - Log domain-level events
  - Query activity history

**See:** `API_EXTENSION_PLAN.md` lines 181-231

### 1.4 Create Pydantic Models

**Status:** 📋 Not Started
**Location:** `api/src/app/model/pydantic/simulator/`

**Tasks:**
- [ ] Create `simulator_config_schema.py`
- [ ] Create `simulator_state_schema.py`
- [ ] Create `simulator_activity_schema.py`

**See:** `API_EXTENSION_PLAN.md` lines 232-289

### 1.5 Create Activity Log Table

**Status:** 📋 Not Started
**Location:** `schema/`

**Tasks:**
- [ ] Create `03_simulator_activity_log.sql`
- [ ] Add indexes for simulator_id and timestamp
- [ ] Update docker-compose.yaml to mount new schema file

**See:** `knowledge/DB_SERVICE_LAYER_ANALYSIS.md` lines 553-569

---

## ⏳ Phase 2: Authentication Integration (HIGH PRIORITY)

### 2.1 Cognito Service Account Setup

**Status:** 📋 Not Started
**Dependencies:** AWS Cognito User Pool (existing)

**Tasks:**
- [ ] Create Cognito service account user: `simulator-service`
- [ ] Set permanent password (store in AWS Secrets Manager)
- [ ] Create "ServiceAccounts" group in Cognito
- [ ] Add simulator-service to ServiceAccounts group
- [ ] Configure permissions for service accounts

**Reference Commands:**
```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username "simulator-service" \
  --user-attributes Name=email,Value=simulator@datakwip.com
```

**See:** Authentication section in discussion history

### 2.2 Simulator Cognito Auth Client

**Status:** 📋 Not Started
**Location:** `simulator/src/service/`

**Tasks:**
- [ ] Create `cognito_auth.py`
  - [ ] Implement `CognitoServiceAuth` class
  - [ ] Handle USER_PASSWORD_AUTH flow
  - [ ] Implement token refresh logic
  - [ ] Add token expiry checking (5-min buffer)
- [ ] Add boto3 to `simulator/requirements.txt`

**Key Features:**
- Automatic token refresh before expiry
- Fallback to re-authentication if refresh fails
- Thread-safe token storage

**See:** Authentication implementation in discussion history

### 2.3 Update API Client for Cognito

**Status:** 📋 Not Started
**Location:** `simulator/src/service/api_client.py`

**Tasks:**
- [ ] Add `CognitoServiceAuth` parameter to `DataKwipAPIClient.__init__()`
- [ ] Update `_get_headers()` to use Cognito tokens
- [ ] Keep API key fallback for local development
- [ ] Handle 401/403 responses gracefully

### 2.4 Update service_main.py for Cognito

**Status:** 📋 Not Started
**Location:** `simulator/src/service_main.py`

**Tasks:**
- [ ] Add Cognito environment variable parsing
  - COGNITO_USER_POOL_ID
  - COGNITO_APP_CLIENT_ID
  - COGNITO_USERNAME
  - COGNITO_PASSWORD (from secrets)
  - AWS_REGION
- [ ] Initialize `CognitoServiceAuth` if credentials provided
- [ ] Pass auth to API client
- [ ] Test authentication on startup

### 2.5 WebApp Cognito Integration

**Status:** 📋 Not Started (Future)
**Location:** `webapp/lib/auth/`

**Tasks:**
- [ ] Install `amazon-cognito-identity-js`
- [ ] Create `webapp/lib/auth/cognito.ts`
- [ ] Implement sign-in flow
- [ ] Implement token refresh
- [ ] Create login page (`webapp/app/(auth)/login/page.tsx`)
- [ ] Add auth middleware

**Note:** This is lower priority - focus on simulator auth first

---

## ⏳ Phase 3: Simulator API Integration (DEPENDS ON PHASE 1)

### 3.1 Create API Client

**Status:** 📋 Not Started
**Location:** `simulator/src/service/api_client.py`

**Tasks:**
- [ ] Create `DataKwipAPIClient` class
- [ ] Implement `bulk_insert_values()` - calls POST /bulk/value
- [ ] Implement `update_state()` - calls POST /simulator/state/{id}
- [ ] Implement `log_activity()` - calls POST /simulator/activity/{id}
- [ ] Implement `get_state()` - calls GET /simulator/state/{id}
- [ ] Handle 503 responses (primary DB down)
- [ ] Handle 401/403 responses (auth failure)

### 3.2 Modify ContinuousDataService

**Status:** 📋 Not Started
**Location:** `simulator/src/service/continuous_generator.py`

**Tasks:**
- [ ] Add `api_client` parameter to `__init__()`
- [ ] Add `use_api` flag (True if api_client provided)
- [ ] Update `generate_current_interval()`:
  - [ ] Convert data_points to API format (JSON with ISO timestamps)
  - [ ] Call `api_client.bulk_insert_values()` instead of direct DB writes
  - [ ] Call `api_client.update_state()` to save totalizers
  - [ ] Call `api_client.log_activity()` for domain events
  - [ ] Keep direct DB writes as fallback (local dev mode)

### 3.3 Update service_main.py

**Status:** 📋 Not Started
**Location:** `simulator/src/service_main.py`

**Tasks:**
- [ ] Add API_URL environment variable
- [ ] Add SIMULATOR_ID environment variable
- [ ] Initialize API client if API_URL provided
- [ ] Pass API client to ContinuousDataService
- [ ] Add API key fallback for local dev

### 3.4 Environment Configuration

**Status:** 📋 Not Started

**Production (Railway):**
```bash
API_URL=https://api.railway.app
SIMULATOR_ID=1
COGNITO_USER_POOL_ID=us-east-1_xxxxx
COGNITO_APP_CLIENT_ID=xxxxxx
COGNITO_USERNAME=simulator-service
COGNITO_PASSWORD=<from-secrets-manager>
AWS_REGION=us-east-1
```

**Local Development:**
```bash
# Use direct DB (no API)
DATABASE_URL=postgresql://...@localhost:5432/datakwip
STATE_DB_URL=postgresql://...@localhost:5433/simulator_state

# OR use API with API key
API_URL=http://localhost:8000
API_KEY=dev-key-local-only
SIMULATOR_ID=1
```

---

## ⏳ Phase 4: WebApp Development (FUTURE)

**Status:** 📋 Not Started
**Priority:** Low (can be done in parallel later)

### 4.1 Dashboard Page
- [ ] System status cards
- [ ] Service health checks
- [ ] Quick actions (start/stop simulator)

### 4.2 Simulator Control Page
- [ ] Configuration editor (YAML → form)
- [ ] Start/Stop/Reset buttons
- [ ] Current status display
- [ ] Generation metrics

### 4.3 Activity Timeline
- [ ] Real-time event stream (Server-Sent Events)
- [ ] Domain-level event display
- [ ] Filtering by time/type
- [ ] Event details expansion

### 4.4 Database Inspector
- [ ] Two tabs: TimescaleDB | PostgreSQL
- [ ] Entity counts, table sizes
- [ ] Recent records viewer
- [ ] Read-only SQL query interface

### 4.5 Data Explorer
- [ ] Haystack tag filter builder
- [ ] Entity list with tag display
- [ ] Time series chart (recharts)
- [ ] Export to CSV/JSON

**See:** `API_EXTENSION_PLAN.md` Phase 3 for detailed implementation

---

## 📋 Immediate Next Steps (Prioritized)

### Week 1: API Foundation
1. **Add simulator endpoints to API** (Phase 1.1)
2. **Set up state database connection** (Phase 1.2)
3. **Create service layer** (Phase 1.3)
4. **Test API endpoints** with Postman/curl

### Week 2: Authentication
1. **Create Cognito service account** (Phase 2.1)
2. **Implement Cognito auth client** (Phase 2.2)
3. **Update API client** (Phase 2.3)
4. **Test authentication** end-to-end

### Week 3: Simulator Integration
1. **Create API client** (Phase 3.1)
2. **Modify simulator service** (Phase 3.2)
3. **Test with local API** (docker-compose up api simulator)
4. **Verify data flow** (API → TimescaleDB)

### Week 4: Production Deployment
1. **Deploy API to Railway** (with both databases)
2. **Deploy simulator to Railway** (with Cognito auth)
3. **Verify production data generation**
4. **Monitor logs and health checks**

---

## 🔗 Related Documentation

- **[API_EXTENSION_PLAN.md](API_EXTENSION_PLAN.md)** - Detailed implementation guide with code examples
- **[DB_SERVICE_LAYER_ANALYSIS.md](knowledge/DB_SERVICE_LAYER_ANALYSIS.md)** - Existing API architecture analysis
- **[CLAUDE.md](CLAUDE.md)** - Development instructions for Claude Code
- **[PRE_DEPLOYMENT_REVIEW.md](PRE_DEPLOYMENT_REVIEW.md)** - Production readiness checklist

---

## 📝 Notes

### Design Decisions Made
1. **Two-database architecture** - TimescaleDB (building data) + PostgreSQL (simulator state)
2. **API-first approach** - Simulator calls API instead of direct DB writes
3. **Cognito for all auth** - Service accounts for simulator, SSO for users
4. **Simulator as poller** - Integrates with existing poller_config infrastructure

### Key Constraints
1. Must maintain backwards compatibility with existing db-service-layer API
2. Simulator must gracefully handle API unavailability (503 responses)
3. Authentication must work in both local dev (API key) and production (Cognito)
4. All changes must be testable via docker-compose locally

### Questions to Resolve
- [ ] Which AWS region for Cognito? (Assume us-east-1)
- [ ] Store Cognito password in AWS Secrets Manager or Railway env vars?
- [ ] Support multiple simulators per organization? (Yes, via SIMULATOR_ID)
- [ ] How to handle simulator discovery/registration? (Manual via POST /simulator/config)

---

**Generated:** 2025-10-04
**Maintained By:** Project team
**Review Frequency:** Weekly during active development
