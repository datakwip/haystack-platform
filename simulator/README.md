# Haystack Building Data Simulator

A standalone service for generating realistic building automation data with web-based control interface.

## 🏗️ Architecture

```
Simulator Service
├── Backend API (FastAPI on :8080)
│   └── Control, status, config endpoints
├── Frontend GUI (Next.js on :3001)
│   └── Dashboard, config editor, activity log
└── PostgreSQL State DB (:5433)
    ├── simulator_state (runtime state)
    └── simulator_activity_log (event history)
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# From repository root
docker-compose up simulator simulator-webapp statedb timescaledb

# Access:
# - Simulator GUI: http://localhost:3001
# - API Docs: http://localhost:8080/docs
# - TimescaleDB: localhost:5432
# - State DB: localhost:5433
```

### Option 2: Local Development

**Terminal 1: Start Databases**
```bash
docker-compose up timescaledb statedb
```

**Terminal 2: Start Simulator Backend**
```bash
cd simulator
pip install -r requirements.txt
python src/service_main.py
```

**Terminal 3: Start Simulator Frontend**
```bash
cd simulator/webapp
npm install
npm run dev
```

Then visit:
- **Dashboard**: http://localhost:3001
- **API Docs**: http://localhost:8080/docs

## 📁 Project Structure

```
simulator/
├── src/
│   ├── api/
│   │   └── simulator_api.py       # FastAPI endpoints
│   ├── service/
│   │   ├── continuous_generator.py # Data generation
│   │   ├── activity_logger.py      # Event logging
│   │   ├── state_manager.py        # State persistence
│   │   └── gap_filler.py           # Gap detection/filling
│   ├── generators/                 # Data generators
│   ├── database/                   # DB utilities
│   └── service_main.py             # Main entry point
├── webapp/
│   ├── app/
│   │   ├── page.tsx                # Dashboard
│   │   ├── config/page.tsx         # Config editor
│   │   └── activity/page.tsx       # Activity log
│   ├── components/ui/              # UI components
│   └── lib/
│       └── api-client.ts           # API client library
├── config/
│   ├── building_config.yaml        # Building configuration
│   └── database_config.yaml        # DB configuration
└── test/                           # Tests
```

## 🎯 Features

### Web Dashboard
- **Real-time Status**: Monitor simulator state, uptime, points generated
- **Control Panel**: Start, stop, reset simulator with one click
- **Metrics**: View generation rate, entity count, error count
- **Activity Timeline**: Browse event history with filtering
- **Configuration Editor**: Edit simulator config via JSON editor

### API Endpoints

**Health & Status:**
- `GET /api/health` - Health check
- `GET /api/status` - Current status
- `GET /api/state` - Detailed state
- `GET /api/metrics` - Generation metrics

**Control:**
- `POST /api/control/start` - Start generation
- `POST /api/control/stop` - Stop generation
- `POST /api/control/reset` - Reset state

**Configuration:**
- `GET /api/config` - Get configuration
- `PUT /api/config` - Update configuration

**Activity:**
- `GET /api/activity` - Activity log (with pagination & filtering)

## 📊 Data Generation

The simulator generates realistic building data including:

- **Equipment**: Chillers, AHUs, VAV boxes, meters
- **Points**: Temperature, pressure, flow, energy consumption
- **Patterns**: Occupancy schedules, weather simulation
- **Continuity**: Totalizers for energy/water/gas meters

### Data Flow

1. **Generation**: Creates data points every 15 minutes
2. **Validation**: Ensures coherent relationships (VAV → AHU → Chiller)
3. **Storage**: Writes to TimescaleDB via database connection
4. **State Tracking**: Updates state in PostgreSQL
5. **Activity Logging**: Records events for monitoring

## 🗄️ Database Schema

**TimescaleDB (Building Data)**:
- `entity` - Building equipment
- `entity_tag` - Haystack tags
- `values_{org_key}` - Time-series data (hypertable)

**PostgreSQL (Simulator State)**:
- `simulator_state` - Runtime state, totalizers
- `simulator_activity_log` - Event history

## ⚙️ Configuration

### Environment Variables

**Backend (simulator):**
```bash
DB_CONFIG_PATH=config/database_config.yaml
BUILDING_CONFIG_PATH=config/building_config.yaml
API_PORT=8080
SERVICE_INTERVAL_MINUTES=15

# Database connections
DATABASE_URL=postgresql://user:pass@localhost:5432/datakwip
STATE_DB_URL=postgresql://user:pass@localhost:5433/simulator_state
```

**Frontend (webapp):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### Building Configuration

Edit `config/building_config.yaml` to customize:
- Building size and floors
- Equipment counts (AHUs, VAVs, chillers)
- Weather simulation
- Occupancy schedules
- Data generation intervals

## 🧪 Testing

```bash
# Unit tests
cd simulator
python test/test_state_manager.py
python test/test_gap_filler.py
python test/test_continuous_service.py

# Integration test
python test/test_resumption.py

# Validation
python validation/validate_service_state.py
python validation/validate_gaps.py
python validation/validate_service_health.py
```

## 📖 API Documentation

Once running, visit **http://localhost:8080/docs** for interactive API documentation (Swagger UI).

## 🔧 Development

### Adding New Endpoints

1. Add endpoint function in `src/api/simulator_api.py`
2. Add API client method in `webapp/lib/api-client.ts`
3. Use in React components

### Adding UI Components

shadcn/ui components are in `webapp/components/ui/`. Add new components:

```bash
cd simulator/webapp
npx shadcn@latest add [component-name]
```

## 🐛 Troubleshooting

### Simulator won't start
- Check database connections (TimescaleDB on 5432, State DB on 5433)
- Verify config files exist in `config/`
- Check logs for specific errors

### Frontend can't connect to API
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check CORS settings in `simulator_api.py`
- Ensure backend is running on port 8080

### Database connection errors
- Start databases: `docker-compose up timescaledb statedb`
- Check credentials in config files
- Verify network connectivity

## 📝 Notes

- The simulator is designed to run independently of the enterprise API
- Configuration is stored in the state database and persists across restarts
- Activity log provides audit trail of all simulator operations
- Dashboard auto-refreshes every 5 seconds

## 🔗 Related Documentation

- [Implementation Status](../IMPLEMENTATION_STATUS.md)
- [API Extension Plan](../API_EXTENSION_PLAN.md)
- [Docker Setup Guide](../docs/DOCKER_LOCAL_SETUP.md)
