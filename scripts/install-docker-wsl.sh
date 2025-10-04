#!/bin/bash

# Install Docker in WSL2
# Run this script with: bash scripts/install-docker-wsl.sh

set -e

echo "=================================================="
echo "Installing Docker in WSL2"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running in WSL
if ! grep -q microsoft /proc/version; then
    echo -e "${RED}This script is designed for WSL2. Exiting.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Updating package lists...${NC}"
sudo apt-get update

echo -e "\n${YELLOW}Step 2: Installing prerequisites...${NC}"
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

echo -e "\n${YELLOW}Step 3: Adding Docker's official GPG key...${NC}"
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo -e "\n${YELLOW}Step 4: Setting up Docker repository...${NC}"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo -e "\n${YELLOW}Step 5: Updating package lists again...${NC}"
sudo apt-get update

echo -e "\n${YELLOW}Step 6: Installing Docker Engine...${NC}"
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo -e "\n${YELLOW}Step 7: Adding user to docker group...${NC}"
sudo usermod -aG docker $USER

echo -e "\n${YELLOW}Step 8: Starting Docker service...${NC}"
sudo service docker start

echo -e "\n${GREEN}=================================================="
echo "Docker Installation Complete!"
echo "==================================================${NC}"

# Test Docker
echo -e "\n${YELLOW}Testing Docker installation...${NC}"
if sudo docker run hello-world > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker is working correctly!${NC}"
else
    echo -e "${RED}⚠️  Docker test failed${NC}"
fi

echo -e "\n${YELLOW}=================================================="
echo "IMPORTANT: Next Steps"
echo "==================================================${NC}"
echo "1. Log out and log back in to apply group changes, OR run:"
echo "   ${GREEN}newgrp docker${NC}"
echo ""
echo "2. To start Docker on boot, you can add this to your ~/.bashrc:"
echo "   ${GREEN}if ! service docker status > /dev/null 2>&1; then${NC}"
echo "   ${GREEN}    sudo service docker start > /dev/null 2>&1${NC}"
echo "   ${GREEN}fi${NC}"
echo ""
echo "3. Verify Docker is working (without sudo):"
echo "   ${GREEN}docker --version${NC}"
echo "   ${GREEN}docker-compose version${NC}"
echo ""
echo "4. Start the Haystack simulator database:"
echo "   ${GREEN}./scripts/docker-start.sh${NC}"
echo ""
echo -e "${GREEN}==================================================${NC}\n"
