#!/bin/bash
# Huawei Cloud Deployment Script
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 Starting Huawei Cloud Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please copy .env.example to .env and fill in your credentials."
    exit 1
fi

# Check Python version
echo -e "${YELLOW}📋 Checking Python version...${NC}"
python3 --version || { echo -e "${RED}❌ Python 3 not found!${NC}"; exit 1; }

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check configuration
echo -e "${YELLOW}🔍 Checking configuration...${NC}"
python3 check_config.py || echo -e "${YELLOW}⚠️  Configuration check script not found, skipping...${NC}"

# Test Milvus connection
echo -e "${YELLOW}🔗 Testing Milvus connection...${NC}"
python3 test_connection.py || echo -e "${YELLOW}⚠️  Milvus connection test failed, but continuing...${NC}"

echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start Streamlit: streamlit run app.py --server.port=8501 --server.address=0.0.0.0"
echo "2. Start Health Check: python3 health_check.py"
echo "3. Or use systemd services (see DEPLOYMENT_100USD_PLAN.md)"

