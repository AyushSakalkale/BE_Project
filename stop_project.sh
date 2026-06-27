#!/bin/bash

# Visual styling
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

clear
echo -e "${RED}${BOLD}========================================================================${NC}"
echo -e "${RED}${BOLD}     STOPPING LOG ANOMALY DETECTION SYSTEM COMPONENTS                   ${NC}"
echo -e "${RED}${BOLD}========================================================================${NC}"
echo ""

# 1. Stop Frontend Dev Server
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}1. Stopping Frontend Dev Server on port 5173...${NC}"
    PID=$(lsof -t -i:5173)
    kill -9 $PID
    echo -e "   Frontend stopped (PID $PID)."
else
    echo -e "1. Frontend Dev Server is not running."
fi
echo ""

# 2. Stop Docker Containers
echo -e "${RED}2. Stopping Docker Containers (db, redis, backend, kafka, flink)...${NC}"
docker compose -f backend/docker-compose.yml down

echo ""
echo -e "${RED}${BOLD}========================================================================${NC}"
echo -e "${RED}${BOLD}     ALL SERVICES STOPPED SUCCESSFULLY                                  ${NC}"
echo -e "${RED}${BOLD}========================================================================${NC}"
echo ""
