#!/bin/bash
# restructure-to-monorepo.sh
# Converts haystack-data-simulator structure to monorepo (api + simulator + webapp)

set -e  # Exit on error

echo "=========================================="
echo "🔄 Converting to Monorepo Structure"
echo "=========================================="
echo ""

# Check we're in the right place
if [ ! -f "PRE_DEPLOYMENT_REVIEW.md" ]; then
    echo "❌ Error: Run this from haystack-data-simulator root"
    echo "   (Looking for PRE_DEPLOYMENT_REVIEW.md)"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "⚠️  Warning: You have uncommitted changes."
    echo "   Please commit or stash them first."
    git status --short
    exit 1
fi

echo "📦 Current directory: $(pwd)"
echo "📍 Git remote: $(git remote get-url origin)"
echo ""
read -p "Continue with restructuring? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "📁 Step 1/6: Moving simulator code to simulator/ directory..."
echo "------------------------------------------------------------"

# Create simulator directory
mkdir -p simulator

# Move simulator-specific files
echo "  Moving src/ → simulator/src/"
git mv src simulator/src

echo "  Moving config/ → simulator/config/"
git mv config simulator/config

echo "  Moving test/ → simulator/test/"
git mv test simulator/test

echo "  Moving validation/ → simulator/validation/"
git mv validation simulator/validation

echo "  Moving Dockerfile → simulator/Dockerfile"
git mv Dockerfile simulator/Dockerfile

echo "  Moving requirements.txt → simulator/requirements.txt"
git mv requirements.txt simulator/requirements.txt

echo "  Moving .dockerignore → simulator/.dockerignore (if exists)"
[ -f .dockerignore ] && git mv .dockerignore simulator/.dockerignore || echo "    (no .dockerignore found)"

echo "✅ Simulator code moved"
echo ""

echo "🌐 Step 2/6: Adding db-service-layer as api/..."
echo "------------------------------------------------------------"

# Check if db-service-layer exists in parent directory
if [ -d "../db-service-layer" ]; then
    echo "  Found db-service-layer in parent directory"
    echo "  Copying to api/..."
    cp -r ../db-service-layer api
    # Remove its .git to make it part of our monorepo
    rm -rf api/.git
    echo "  ✅ Copied from ../db-service-layer"
else
    echo "  db-service-layer not found in parent directory"
    echo "  Cloning from GitHub..."
    git clone git@github.com:datakwip/db-service-layer.git api
    rm -rf api/.git
    echo "  ✅ Cloned from GitHub"
fi

git add api/
echo ""

echo "🎨 Step 3/6: Creating webapp/ skeleton..."
echo "------------------------------------------------------------"

mkdir -p webapp/app webapp/components webapp/lib

# Create minimal package.json
cat > webapp/package.json <<'EOF'
{
  "name": "haystack-webapp",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5"
  }
}
EOF

# Create next.config.js
cat > webapp/next.config.js <<'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
}

module.exports = nextConfig
EOF

# Create tsconfig.json
cat > webapp/tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

# Create placeholder app/page.tsx
mkdir -p webapp/app
cat > webapp/app/page.tsx <<'EOF'
export default function Home() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">Haystack Platform</h1>
      <p className="mt-4">Web interface coming soon...</p>
    </main>
  )
}
EOF

# Create Dockerfile
cat > webapp/Dockerfile <<'EOF'
FROM node:20-alpine AS base

# Install dependencies
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Build application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
EOF

# Create .gitignore for webapp
cat > webapp/.gitignore <<'EOF'
# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local

# typescript
*.tsbuildinfo
next-env.d.ts
EOF

git add webapp/
echo "✅ Webapp skeleton created"
echo ""

echo "🐳 Step 4/6: Creating updated docker-compose.yaml..."
echo "------------------------------------------------------------"

# Backup existing docker-compose
if [ -f docker-compose.yaml ]; then
    cp docker-compose.yaml docker-compose.yaml.backup
    echo "  Backed up existing docker-compose.yaml → docker-compose.yaml.backup"
fi

cat > docker-compose.yaml <<'EOF'
version: '3.8'

services:
  # TimescaleDB - Building Data
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    container_name: haystack-timescaledb
    environment:
      POSTGRES_DB: datakwip
      POSTGRES_USER: datakwip_user
      POSTGRES_PASSWORD: datakwip_password
    ports:
      - "5432:5432"
    volumes:
      - timescale-data:/var/lib/postgresql/data
      - ./schema/01_sql_schema_core_v2.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U datakwip_user -d datakwip"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - haystack-network

  # PostgreSQL - Simulator State
  statedb:
    image: postgres:15-alpine
    container_name: haystack-statedb
    environment:
      POSTGRES_DB: simulator_state
      POSTGRES_USER: simulator_user
      POSTGRES_PASSWORD: simulator_password
    ports:
      - "5433:5432"
    volumes:
      - state-data:/var/lib/postgresql/data
      - ./schema/02_simulator_state.sql:/docker-entrypoint-initdb.d/01_state.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U simulator_user -d simulator_state"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - haystack-network

  # API Service (db-service-layer with simulator extensions)
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    container_name: haystack-api
    environment:
      DATABASE_URL: postgresql://datakwip_user:datakwip_password@timescaledb:5432/datakwip
      STATE_DB_URL: postgresql://simulator_user:simulator_password@statedb:5432/simulator_state
      dk_env: "local"
      MAIN_DB_POOL_SIZE: 10
      MAIN_DB_MAX_OVERFLOW: 10
    ports:
      - "8000:8000"
    volumes:
      - ./api/src:/app/src:ro
    depends_on:
      timescaledb:
        condition: service_healthy
      statedb:
        condition: service_healthy
    networks:
      - haystack-network

  # Simulator Service
  simulator:
    build:
      context: ./simulator
      dockerfile: Dockerfile
    container_name: haystack-simulator
    environment:
      API_URL: http://api:8000
      SIMULATOR_ID: 1
      API_KEY: dev-key-local-only
      STATE_DB_URL: postgresql://simulator_user:simulator_password@statedb:5432/simulator_state
      HEALTH_CHECK_PORT: 8080
      SERVICE_INTERVAL_MINUTES: 15
      BUILDING_CONFIG_PATH: config/building_config.yaml
      DB_CONFIG_PATH: config/database_config.docker.yaml
    ports:
      - "8080:8080"
    volumes:
      - ./simulator/src:/app/src:ro
      - ./simulator/config:/app/config:ro
    depends_on:
      - api
    networks:
      - haystack-network

  # Web Application
  webapp:
    build:
      context: ./webapp
      dockerfile: Dockerfile
    container_name: haystack-webapp
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      API_INTERNAL_URL: http://api:8000
    ports:
      - "3000:3000"
    volumes:
      - ./webapp/app:/app/app:ro
      - ./webapp/components:/app/components:ro
    depends_on:
      - api
    networks:
      - haystack-network

volumes:
  timescale-data:
  state-data:

networks:
  haystack-network:
    driver: bridge
EOF

git add docker-compose.yaml
[ -f docker-compose.yaml.backup ] && git add docker-compose.yaml.backup
echo "✅ docker-compose.yaml updated"
echo ""

echo "📝 Step 5/6: Updating README.md..."
echo "------------------------------------------------------------"

cat > README.md <<'EOF'
# Haystack Platform

Complete building automation data platform with simulator, API, and web interface.

## 🏗️ Architecture

```
haystack-platform/
├── api/           FastAPI backend (extended db-service-layer)
├── simulator/     Haystack building data generator
├── webapp/        Next.js web interface
├── schema/        Database schemas (TimescaleDB + PostgreSQL)
└── docs/          Documentation
```

## 🚀 Quick Start

```bash
# Start all services
docker-compose up

# Access:
# - API:              http://localhost:8000
# - API Docs:         http://localhost:8000/docs
# - Simulator Health: http://localhost:8080/health
# - Web GUI:          http://localhost:3000
```

## 📚 Documentation

- **[API Extension Plan](API_EXTENSION_PLAN.md)** - Implementation roadmap
- **[Pre-Deployment Review](PRE_DEPLOYMENT_REVIEW.md)** - Production readiness
- **[DB Service Layer Analysis](knowledge/DB_SERVICE_LAYER_ANALYSIS.md)** - API architecture
- **[Critical Design Decisions](knowledge/CRITICAL_DESIGN_DECISIONS.md)** - Design rationale

## 🛠️ Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for webapp development)

### Local Development

```bash
# Start databases only
docker-compose up timescaledb statedb

# Run API locally
cd api
pip install -r requirements.txt
uvicorn src.app.main:app --reload --port 8000

# Run simulator locally
cd simulator
pip install -r requirements.txt
python src/main.py --days 7

# Run webapp locally
cd webapp
npm install
npm run dev
```

### Running Tests

```bash
# Simulator tests
cd simulator
python test/test_state_manager.py
python test/test_gap_filler.py
python test/test_continuous_service.py
python test/test_resumption.py

# Validation
python validation/validate_service_state.py
python validation/validate_gaps.py
python validation/validate_service_health.py
```

## 🎯 Services

### API (Port 8000)
FastAPI backend with:
- Building data management (entities, tags, time-series)
- Poller configuration
- Simulator control endpoints
- Multi-database support

### Simulator (Port 8080)
Data generation service:
- Realistic building automation data
- Continuous 15-minute interval generation
- Gap detection and filling
- State persistence

### WebApp (Port 3000)
Next.js web interface:
- System dashboard
- Simulator control panel
- Database inspector
- Activity timeline
- Data explorer

## 📦 Deployment

### Railway

See [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md) for detailed instructions.

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yaml up -d
```

## 🤖 Claude Code

This project is optimized for development with Claude Code. See [CLAUDE.md](CLAUDE.md) for instructions.

## 📄 License

[Add your license]

## 🙏 Acknowledgments

Built on top of [db-service-layer](https://github.com/datakwip/db-service-layer)
EOF

git add README.md
echo "✅ README.md updated"
echo ""

echo "📖 Step 6/6: Updating CLAUDE.md..."
echo "------------------------------------------------------------"

cat > CLAUDE.md <<'EOF'
# Claude Code Assistant Instructions - Haystack Platform

## Project Overview

This is a **monorepo** containing the complete Haystack Building Data Platform:

### Services

1. **api/** - FastAPI backend (extended db-service-layer)
   - Building data management (entities, tags, time-series)
   - Simulator control endpoints (`/simulator/*`)
   - Multi-database support (TimescaleDB + PostgreSQL)

2. **simulator/** - Haystack data generator service
   - Generates realistic building automation data
   - Calls API endpoints for data insertion
   - Manages operational state

3. **webapp/** - Next.js web interface
   - System dashboard
   - Simulator control panel
   - Data explorer with Haystack tag filtering

## Folder Structure

```
haystack-platform/
├── api/
│   ├── src/app/
│   │   ├── api/simulator/       # NEW: Simulator endpoints
│   │   ├── api/source_objects/  # Existing: Entity, tag, value APIs
│   │   ├── services/            # Business logic
│   │   └── model/               # Pydantic & SQLAlchemy models
│   └── Dockerfile
│
├── simulator/
│   ├── src/
│   │   ├── service/            # Core simulator logic
│   │   │   ├── api_client.py   # Calls ../api endpoints
│   │   │   ├── continuous_generator.py
│   │   │   └── cognito_auth.py
│   │   ├── generators/         # Data generation
│   │   └── database/           # DB utilities
│   ├── config/                 # YAML configs
│   ├── test/                   # Tests
│   └── Dockerfile
│
├── webapp/
│   ├── app/
│   │   ├── (dashboard)/        # Authenticated pages
│   │   │   ├── page.tsx        # Main dashboard
│   │   │   ├── simulator/      # Simulator control
│   │   │   ├── activity/       # Activity timeline
│   │   │   └── explorer/       # Data explorer
│   │   └── api/                # Next.js API routes
│   ├── components/             # React components
│   └── lib/
│       └── api-client.ts       # Calls ../api endpoints
│
├── schema/                     # Database schemas
│   ├── 01_sql_schema_core_v2.sql
│   └── 02_simulator_state.sql
│
├── docs/                       # Documentation
├── knowledge/                  # Critical design decisions
└── docker-compose.yaml         # All services
```

## Important: Multi-Service Coordination

When making changes that span services:

✅ **DO THIS** (Atomic changes across services):
```
You: "Add a /simulator/metrics endpoint that returns generation stats,
     update the simulator to call it every hour, and display metrics
     on the webapp dashboard"

Claude:
1. Adds endpoint in api/src/app/api/simulator/simulator_api.py
2. Updates simulator/src/service/api_client.py with metrics() method
3. Updates simulator/src/service/continuous_generator.py to call it
4. Updates webapp/lib/api-client.ts with getMetrics()
5. Updates webapp/app/(dashboard)/page.tsx to display metrics
```

❌ **NOT THIS** (Making changes one service at a time):
```
You: "Add /simulator/metrics in the API"
Claude: [adds endpoint]
You: "Now update the simulator to call it"
Claude: [updates simulator, might miss details from API]
```

### Cross-Service Guidelines

- **API endpoint changes** → Update both `simulator/src/service/api_client.py` AND `webapp/lib/api-client.ts`
- **Database schema changes** → Update all three services that touch the DB
- **Authentication changes** → Update API middleware, simulator auth, webapp auth
- **Always test with**: `docker-compose up`

## File Placement Rules

1. **API Endpoints**: `api/src/app/api/`
   - Simulator-specific: `api/src/app/api/simulator/`
   - Existing endpoints: `api/src/app/api/source_objects/`

2. **Business Logic**: `api/src/app/services/`
   - Simulator services: `simulator_config_service.py`, `simulator_state_service.py`

3. **Data Models**:
   - Pydantic: `api/src/app/model/pydantic/simulator/`
   - SQLAlchemy: `api/src/app/model/sqlalchemy/`

4. **Simulator Core**: `simulator/src/service/`
   - Generator logic: `simulator/src/generators/`
   - Tests: `simulator/test/`

5. **WebApp Pages**: `webapp/app/(dashboard)/`
   - Components: `webapp/components/`
   - Utilities: `webapp/lib/`

6. **Shared Resources**:
   - Database schemas: `schema/`
   - Documentation: `docs/`
   - Design decisions: `knowledge/`

## Development Workflow

### Starting Services

```bash
# All services
docker-compose up

# Specific service
docker-compose up timescaledb statedb api

# Logs for one service
docker-compose logs -f simulator
```

### Making Changes

1. **Make changes across services** in single Claude session
2. **Test**: `docker-compose up`
3. **Commit all changes together** (atomic)
4. **Deploy all services** (coordinated)

### Running Tests

```bash
# Simulator tests
cd simulator
python test/test_state_manager.py
python test/test_gap_filler.py

# API tests
cd api
pytest

# Webapp tests
cd webapp
npm test
```

## Key Design Decisions

### Two-Database Architecture

- **TimescaleDB** (port 5432): Building data (entities, tags, time-series)
- **PostgreSQL** (port 5433): Simulator operational state

**Why**: Clean separation between user-facing data and simulator internals.

### API-First Architecture

- Simulator **calls API** endpoints (not direct DB writes)
- WebApp **calls API** endpoints
- Single source of truth for data operations

**Why**: Consistent data access, better error handling, multi-database support.

### Haystack v3 Schema

- Follows Project Haystack tagging conventions
- Entity-attribute-value model
- Tag-based filtering

**Why**: Industry standard for building automation systems.

## Common Tasks

### Add New Simulator Endpoint

1. Define endpoint: `api/src/app/api/simulator/simulator_api.py`
2. Add service logic: `api/src/app/services/simulator_*.py`
3. Update API client: `simulator/src/service/api_client.py`
4. Update webapp client: `webapp/lib/api-client.ts`

### Add New GUI Page

1. Create page: `webapp/app/(dashboard)/[name]/page.tsx`
2. Create components: `webapp/components/[name]/`
3. Update navigation: `webapp/components/layout/Navigation.tsx`

### Modify Database Schema

1. Update schema file: `schema/*.sql`
2. Update SQLAlchemy models: `api/src/app/model/sqlalchemy/`
3. Rebuild databases: `docker-compose down -v && docker-compose up`

## Authentication

- **Production**: AWS Cognito (SSO)
  - Users: Human login via webapp
  - Services: Service account with machine-to-machine auth

- **Local Dev**: API key fallback (for testing without Cognito)

## Important Reminders

- ✅ **Always** make cross-service changes in single session
- ✅ **Always** test with `docker-compose up` after changes
- ✅ **Never** create files unless absolutely necessary
- ✅ **Prefer** editing existing files over creating new ones
- ✅ **Log** critical decisions in `knowledge/CRITICAL_DESIGN_DECISIONS.md`

## Contact & Resources

- Main docs: `docs/`
- API plan: `API_EXTENSION_PLAN.md`
- Deployment: `PRE_DEPLOYMENT_REVIEW.md`
- DB analysis: `knowledge/DB_SERVICE_LAYER_ANALYSIS.md`
EOF

git add CLAUDE.md
echo "✅ CLAUDE.md updated"
echo ""

echo "=========================================="
echo "✅ Restructuring Complete!"
echo "=========================================="
echo ""
echo "Summary of changes:"
echo "  📁 Moved simulator code to simulator/"
echo "  🌐 Added db-service-layer as api/"
echo "  🎨 Created webapp/ skeleton"
echo "  🐳 Updated docker-compose.yaml"
echo "  📝 Updated README.md and CLAUDE.md"
echo ""
echo "Next steps:"
echo "  1. Review changes:    git status"
echo "  2. Review diff:       git diff --staged"
echo "  3. Commit changes:    git commit -m 'Convert to monorepo structure'"
echo "  4. Push to new repo:  git push -u origin main"
echo ""
echo "After pushing:"
echo "  - Test locally:       docker-compose up"
echo "  - Update GitHub name: Settings → Rename to 'haystack-platform'"
echo ""
