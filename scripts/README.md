# Docker Scripts

**← [Back to Main README](../README.md)**

Convenience scripts for managing Docker services locally.

**Related Documentation**:
- [Docker Setup Guide](../docs/DOCKER_LOCAL_SETUP.md) - Complete Docker documentation
- [Service Mode](../docs/SERVICE_MODE_SUMMARY.md) - Running as a continuous service

## Quick Start

```bash
# Start TimescaleDB only (for local development)
./scripts/docker-start.sh

# Start full stack (DB + Simulator)
./scripts/docker-start.sh full

# Stop services (keep data)
./scripts/docker-stop.sh

# Stop and remove all data
./scripts/docker-stop.sh reset
```

## Scripts

### docker-start.sh

Starts Docker services with automatic database initialization.

**Usage:**
```bash
./scripts/docker-start.sh [MODE]
```

**Modes:**
- `db-only` (default) - Start only TimescaleDB
- `full` - Start TimescaleDB + Simulator service
- `rebuild` - Rebuild images and start full stack

**Examples:**
```bash
# Start just the database
./scripts/docker-start.sh

# Start everything
./scripts/docker-start.sh full

# Rebuild and start
./scripts/docker-start.sh rebuild
```

### docker-stop.sh

Stops Docker services with various cleanup options.

**Usage:**
```bash
./scripts/docker-stop.sh [MODE]
```

**Modes:**
- `stop` (default) - Stop services, keep data
- `reset` - Stop services and remove all data (prompts for confirmation)
- `clean` - Stop services, remove data and images

**Examples:**
```bash
# Stop services (data persists)
./scripts/docker-stop.sh

# Remove everything
./scripts/docker-stop.sh reset

# Full cleanup including images
./scripts/docker-stop.sh clean
```

## Common Workflows

### Local Development (Database in Docker, Simulator on Host)

```bash
# Start database
./scripts/docker-start.sh

# Run simulator locally
python src/main.py --reset --days 7
python src/main.py --service

# When done
./scripts/docker-stop.sh
```

### Full Docker Stack Testing

```bash
# Start everything
./scripts/docker-start.sh full

# Check health
curl http://localhost:8080/health

# View logs
docker-compose logs -f

# When done
./scripts/docker-stop.sh
```

### Fresh Start

```bash
# Remove all data and restart
./scripts/docker-stop.sh reset
./scripts/docker-start.sh

# Initialize with data
python src/main.py --reset --days 30
```

## Manual Commands

If you prefer to use docker-compose directly:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild
docker-compose up -d --build
```

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# View logs
docker-compose logs

# Try fresh start
./scripts/docker-stop.sh reset
./scripts/docker-start.sh
```

### Database connection errors
```bash
# Verify database is running
docker ps | grep timescaledb

# Test connection
docker exec haystack-timescaledb pg_isready -U datakwip_user

# Check database logs
docker-compose logs timescaledb
```

### Permission errors
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

For more detailed information, see [docs/DOCKER_LOCAL_SETUP.md](../docs/DOCKER_LOCAL_SETUP.md)
