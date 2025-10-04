#!/bin/bash

# Docker startup script for local development
set -e

echo "=================================================="
echo "Haystack Data Simulator - Docker Setup"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Parse arguments
MODE=${1:-db-only}

case $MODE in
    "db-only")
        echo -e "\n${YELLOW}Starting TimescaleDB only...${NC}"
        docker compose up -d timescaledb
        ;;
    "full")
        echo -e "\n${YELLOW}Starting full stack (DB + Simulator)...${NC}"
        docker compose up -d
        ;;
    "rebuild")
        echo -e "\n${YELLOW}Rebuilding and starting full stack...${NC}"
        docker compose up -d --build
        ;;
    *)
        echo "Usage: $0 [db-only|full|rebuild]"
        echo "  db-only  - Start only TimescaleDB (default)"
        echo "  full     - Start TimescaleDB + Simulator"
        echo "  rebuild  - Rebuild and start full stack"
        exit 1
        ;;
esac

# Wait for database to be healthy
echo -e "\n${YELLOW}Waiting for database to be ready...${NC}"
sleep 2

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker exec haystack-timescaledb pg_isready -U datakwip_user -d datakwip > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Database is ready!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "\n${RED}❌ Database failed to start${NC}"
    docker-compose logs timescaledb
    exit 1
fi

# Check if schema tables exist
echo -e "\n${YELLOW}Checking database schema...${NC}"

TABLES_EXIST=$(docker exec haystack-timescaledb psql -U datakwip_user -d datakwip -t -c "
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_schema = 'core' AND table_name IN ('entity', 'simulator_state');
" 2>/dev/null | tr -d ' ')

if [ "$TABLES_EXIST" -eq "2" ]; then
    echo -e "${GREEN}✅ Database schema already initialized${NC}"
else
    echo -e "${YELLOW}⚙️  Initializing database schema...${NC}"

    # Apply core schema
    if [ -f "schema/sql_schema_core_v2.sql" ]; then
        docker exec -i haystack-timescaledb psql -U datakwip_user -d datakwip < schema/sql_schema_core_v2.sql > /dev/null 2>&1
        echo -e "${GREEN}✅ Core schema applied${NC}"
    fi

    # Apply simulator state schema
    if [ -f "schema/simulator_state.sql" ]; then
        docker exec -i haystack-timescaledb psql -U datakwip_user -d datakwip < schema/simulator_state.sql > /dev/null 2>&1
        echo -e "${GREEN}✅ Simulator state schema applied${NC}"
    fi
fi

# Show status
echo -e "\n${GREEN}=================================================="
echo "Docker Services Status"
echo "==================================================${NC}"
docker compose ps

# Show connection info
echo -e "\n${GREEN}=================================================="
echo "Database Connection Info"
echo "==================================================${NC}"
echo "Host: localhost"
echo "Port: 5432"
echo "Database: datakwip"
echo "User: datakwip_user"
echo "Password: datakwip_password"
echo ""
echo "Connection String:"
echo "postgresql://datakwip_user:datakwip_password@localhost:5432/datakwip"

# Show next steps
echo -e "\n${GREEN}=================================================="
echo "Next Steps"
echo "==================================================${NC}"

if [ "$MODE" = "db-only" ]; then
    echo "Database is running. You can now:"
    echo ""
    echo "1. Run the simulator locally:"
    echo "   ${YELLOW}python src/main.py --reset --days 7${NC}"
    echo ""
    echo "2. Run in service mode:"
    echo "   ${YELLOW}python src/main.py --service${NC}"
    echo ""
    echo "3. Run tests:"
    echo "   ${YELLOW}python test/test_state_manager.py${NC}"
    echo ""
    echo "4. Connect to database:"
    echo "   ${YELLOW}docker exec -it haystack-timescaledb psql -U datakwip_user -d datakwip${NC}"
else
    echo "Full stack is running. You can:"
    echo ""
    echo "1. Check service health:"
    echo "   ${YELLOW}curl http://localhost:8080/health${NC}"
    echo ""
    echo "2. View logs:"
    echo "   ${YELLOW}docker compose logs -f${NC}"
    echo ""
    echo "3. Check service state:"
    echo "   ${YELLOW}python src/main.py --check-state${NC}"
fi

echo ""
echo "To stop services:"
echo "   ${YELLOW}docker compose down${NC}"
echo ""
echo "To reset everything:"
echo "   ${YELLOW}docker compose down -v${NC}"
echo ""
echo "For more info, see: ${YELLOW}docs/DOCKER_LOCAL_SETUP.md${NC}"
echo -e "${GREEN}==================================================${NC}\n"
