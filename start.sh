#!/bin/bash
# Cloud deployment startup script for Huawei Cloud ECS
# This script starts both Streamlit app and health check service

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Huawei Cloud AI Health Assistant...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env file with required configuration."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found!${NC}"
    exit 1
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Start health check service in background
echo -e "${YELLOW}🏥 Starting health check service on port ${HEALTH_CHECK_PORT:-8080}...${NC}"
python3 health_check.py &
HEALTH_PID=$!

# Wait a moment for health check to start
sleep 2

# Start Streamlit app
echo -e "${YELLOW}🌐 Starting Streamlit app on port ${STREAMLIT_SERVER_PORT:-8501}...${NC}"
streamlit run app.py \
    --server.port=${STREAMLIT_SERVER_PORT:-8501} \
    --server.address=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0} \
    --server.headless=${STREAMLIT_SERVER_HEADLESS:-true} \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false

# Cleanup on exit
trap "kill $HEALTH_PID 2>/dev/null" EXIT
