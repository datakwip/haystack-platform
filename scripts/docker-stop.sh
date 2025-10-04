#!/bin/bash

# Docker stop/cleanup script
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Haystack Data Simulator - Docker Cleanup"
echo "=================================================="

# Parse arguments
MODE=${1:-stop}

case $MODE in
    "stop")
        echo -e "\n${YELLOW}Stopping services (keeping data)...${NC}"
        docker compose down
        echo -e "${GREEN}✅ Services stopped${NC}"
        echo -e "\nData volumes preserved. Use '${YELLOW}./scripts/docker-stop.sh reset${NC}' to remove data."
        ;;
    "reset")
        echo -e "\n${RED}⚠️  WARNING: This will remove all data!${NC}"
        read -p "Are you sure? (yes/no): " -r
        echo
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo -e "${YELLOW}Stopping services and removing volumes...${NC}"
            docker compose down -v
            echo -e "${GREEN}✅ Services stopped and data removed${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
            exit 0
        fi
        ;;
    "clean")
        echo -e "\n${YELLOW}Cleaning up (including images)...${NC}"
        docker compose down -v --rmi local
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        ;;
    *)
        echo "Usage: $0 [stop|reset|clean]"
        echo "  stop   - Stop services, keep data (default)"
        echo "  reset  - Stop services and remove all data"
        echo "  clean  - Stop services, remove data and images"
        exit 1
        ;;
esac

echo ""
