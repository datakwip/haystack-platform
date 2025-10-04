# Simulator Quick Start Guide

## ✅ Phase 1 Complete

All components are implemented and ready to test:
- FastAPI backend on port 8080
- Next.js frontend on port 3001
- Activity logging to PostgreSQL
- Control endpoints (start, stop, reset)
- Web dashboard with real-time updates

## 🚀 Quick Test (Docker Compose - Recommended)

```bash
# From repository root
cd /home/csperdue/datakwip-projects/haystack-platform

# Start all services
docker-compose up simulator simulator-webapp statedb timescaledb

# Access:
# - Simulator GUI: http://localhost:3001
# - API Docs: http://localhost:8080/docs
# - TimescaleDB: localhost:5432
# - State DB: localhost:5433
```

## 🔧 Local Development Test

**Terminal 1: Start Databases**
```bash
cd /home/csperdue/datakwip-projects/haystack-platform
docker-compose up timescaledb statedb
```

**Terminal 2: Start Simulator Backend**
```bash
cd /home/csperdue/datakwip-projects/haystack-platform/simulator
python src/service_main.py
```

**Terminal 3: Start Simulator Frontend**
```bash
cd /home/csperdue/datakwip-projects/haystack-platform/simulator/webapp
npm run dev
```

Then visit:
- **Dashboard**: http://localhost:3001
- **API Docs**: http://localhost:8080/docs
- **Activity Log**: http://localhost:3001/activity
- **Config Editor**: http://localhost:3001/config

## 📋 Features to Test

### Dashboard (/)
- [ ] View simulator status (running, stopped)
- [ ] Click "Start" button
- [ ] Click "Stop" button
- [ ] Click "Reset" button (confirm dialog)
- [ ] Click "Reset with Data" button (confirm dialog)
- [ ] View real-time metrics (points generated, uptime)

### Activity Log (/activity)
- [ ] View recent activity events
- [ ] Filter by event type (generation, start, stop, error)
- [ ] Load more events (pagination)
- [ ] Expand event details (JSON)

### Config Editor (/config)
- [ ] View current configuration
- [ ] Click "Edit Configuration"
- [ ] Modify JSON configuration
- [ ] Click "Save Configuration"
- [ ] View updated configuration

### API Endpoints (/docs)
- [ ] GET /api/health (health check)
- [ ] GET /api/status (current status)
- [ ] GET /api/state (detailed state)
- [ ] GET /api/metrics (generation metrics)
- [ ] POST /api/control/start
- [ ] POST /api/control/stop
- [ ] POST /api/control/reset
- [ ] GET /api/config
- [ ] PUT /api/config
- [ ] GET /api/activity

## ✅ Validation Results

- ✅ Python imports valid
- ✅ FastAPI dependencies installed
- ✅ Next.js builds successfully (6 pages)
- ✅ Activity log schema created
- ✅ Docker compose configured

## 📊 Implementation Status

See [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) for complete status.

**Phase 1:** ✅ Complete
**Phase 2:** ⏳ Authentication Integration (next)
