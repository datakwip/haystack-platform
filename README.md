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
- Simulator control endpoints (future)
- Multi-database support

### Simulator (Port 8080)
Data generation service:
- Realistic building automation data
- Continuous 15-minute interval generation
- Gap detection and filling
- State persistence

### WebApp (Port 3000)
Next.js web interface (coming soon):
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
