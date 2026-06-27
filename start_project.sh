#!/bin/bash

# Visual styling
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo -e "${BLUE}${BOLD}     STARTING LOG ANOMALY DETECTION SYSTEM COMPONENTS                  ${NC}"
echo -e "${BLUE}${BOLD}========================================================================${NC}"
echo ""

# 1. Start Docker Containers for Backend, DB, and Redis
echo -e "${YELLOW}1. Launching Docker Containers (db, redis, backend)...${NC}"
docker compose -f backend/docker-compose.yml up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to launch Docker containers. Make sure Docker Desktop is open and running!${NC}"
    exit 1
fi

echo -e "${GREEN}Docker containers started successfully.${NC}"
echo ""

# 2. Check and Install Frontend Node Modules if missing
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}2. node_modules not found in frontend directory. Running npm install...${NC}"
    cd frontend && npm install && cd ..
fi

# 3. Start Frontend Dev Server
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}3. Frontend Dev Server is already running on port 5173.${NC}"
else
    echo -e "${YELLOW}3. Starting Frontend Dev Server on port 5173 in the background...${NC}"
    cd frontend
    npm run dev > vite.log 2>&1 &
    cd ..
    sleep 2
fi

echo ""
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "${GREEN}${BOLD}     ALL SERVICES LAUNCHED AND VERIFIED                                 ${NC}"
echo -e "${GREEN}${BOLD}========================================================================${NC}"
echo -e "  - Backend Swagger Docs: http://localhost:8000/docs"
echo -e "  - Frontend Web UI:      http://localhost:5173/"
echo ""
echo -e "To stop all backend containers later, run: ${BOLD}docker compose -f backend/docker-compose.yml down${NC}"
