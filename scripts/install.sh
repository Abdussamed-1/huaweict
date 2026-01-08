#!/bin/bash
# =============================================================================
# Huawei Cloud AI Health Assistant - ECS Installation Script
# This script performs a complete installation on ECS instance
# Usage: sudo ./install.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
APP_NAME="huaweict"
APP_DIR="/opt/${APP_NAME}"
APP_USER="ubuntu"
PYTHON_VERSION="3.11"
STREAMLIT_PORT="8501"
HEALTH_PORT="8080"

# =============================================================================
# Helper Functions
# =============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║     Huawei Cloud AI Health Assistant - ECS Installation          ║"
    echo "║                        v2.0.0                                    ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run this script as root: sudo ./install.sh"
    fi
}

# =============================================================================
# 1. System Preparation
# =============================================================================

prepare_system() {
    log_info "Updating system..."
    apt-get update -qq
    apt-get upgrade -y -qq
    
    log_info "Installing base packages..."
    apt-get install -y -qq \
        software-properties-common \
        build-essential \
        curl \
        wget \
        git \
        nano \
        htop \
        unzip \
        ca-certificates \
        gnupg \
        lsb-release
    
    log_success "System prepared"
}

# =============================================================================
# 2. Python Installation
# =============================================================================

install_python() {
    log_info "Checking Python ${PYTHON_VERSION}..."
    
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        log_success "Python ${PYTHON_VERSION} already installed"
    else
        log_info "Installing Python ${PYTHON_VERSION}..."
        add-apt-repository -y ppa:deadsnakes/ppa
        apt-get update -qq
        apt-get install -y -qq \
            python${PYTHON_VERSION} \
            python${PYTHON_VERSION}-venv \
            python${PYTHON_VERSION}-dev \
            python3-pip
        log_success "Python ${PYTHON_VERSION} installed"
    fi
}

# =============================================================================
# 3. Nginx Installation
# =============================================================================

install_nginx() {
    log_info "Installing Nginx..."
    
    apt-get install -y -qq nginx
    
    # Create Nginx SSL directory
    mkdir -p /etc/nginx/ssl
    
    # Create self-signed certificate (temporary)
    if [ ! -f /etc/nginx/ssl/fullchain.pem ]; then
        log_info "Creating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/privkey.pem \
            -out /etc/nginx/ssl/fullchain.pem \
            -subj "/C=TR/ST=Istanbul/L=Istanbul/O=HuaweiCT/CN=localhost"
        chmod 600 /etc/nginx/ssl/privkey.pem
        log_warning "Self-signed certificate created. Use Let's Encrypt for production."
    fi
    
    log_success "Nginx installed"
}

# =============================================================================
# 4. Application Directory Setup
# =============================================================================

setup_app_directory() {
    log_info "Preparing application directory: ${APP_DIR}"
    
    mkdir -p ${APP_DIR}/app
    mkdir -p ${APP_DIR}/logs
    mkdir -p ${APP_DIR}/data
    mkdir -p ${APP_DIR}/backups
    
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
    chmod -R 755 ${APP_DIR}
    
    log_success "Application directory prepared"
}

# =============================================================================
# 5. Deploy Application Files
# =============================================================================

deploy_application() {
    log_info "Copying application files..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
    
    if [ -f "${PROJECT_DIR}/app.py" ]; then
        # Copy Python files
        cp ${PROJECT_DIR}/*.py ${APP_DIR}/app/ 2>/dev/null || true
        cp ${PROJECT_DIR}/requirements.txt ${APP_DIR}/app/
        
        # Copy .streamlit directory
        if [ -d "${PROJECT_DIR}/.streamlit" ]; then
            cp -r ${PROJECT_DIR}/.streamlit ${APP_DIR}/app/
        fi
        
        # Copy Nginx config
        if [ -f "${PROJECT_DIR}/scripts/nginx.conf" ]; then
            cp ${PROJECT_DIR}/scripts/nginx.conf /etc/nginx/sites-available/${APP_NAME}
            ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
            rm -f /etc/nginx/sites-enabled/default
        fi
        
        chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
        log_success "Application files copied"
    else
        log_warning "Application files not found."
        log_info "Copy manually: scp -r ./* ${APP_USER}@<ECS_IP>:${APP_DIR}/app/"
    fi
}

# =============================================================================
# 6. Virtual Environment and Dependencies
# =============================================================================

setup_virtualenv() {
    log_info "Creating virtual environment..."
    
    cd ${APP_DIR}/app
    
    sudo -u ${APP_USER} python${PYTHON_VERSION} -m venv ${APP_DIR}/venv
    sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install --upgrade pip wheel setuptools
    
    if [ -f requirements.txt ]; then
        log_info "Installing Python packages (this may take a few minutes)..."
        sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install -r requirements.txt
        log_success "Python packages installed"
    else
        log_warning "requirements.txt not found"
    fi
}

# =============================================================================
# 7. Environment File
# =============================================================================

create_env_file() {
    log_info "Checking environment file..."
    
    ENV_FILE="${APP_DIR}/app/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << 'ENVEOF'
# =============================================================================
# Huawei Cloud AI Health Assistant - Environment Variables
# =============================================================================

# ------------------ DeepSeek API (Required) ------------------
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat
DEEPSEEK_USE_DIRECT_API=true

# ------------------ Milvus Cloud (Required) ------------------
MILVUS_HOST=your-milvus-cluster.zillizcloud.com
MILVUS_PORT=443
MILVUS_API_KEY=your-milvus-api-key
MILVUS_COLLECTION_NAME=medical_knowledge_base
MILVUS_USE_CLOUD=true

# ------------------ ModelArts (Optional - Qwen3-32B) ------------------
# MODELARTS_ENDPOINT=https://your-modelarts-endpoint
# MODELARTS_PROJECT_ID=your-project-id
# MODELARTS_MODEL_NAME=qwen3-32b

# ------------------ OBS Storage (Optional) ------------------
# OBS_ACCESS_KEY=your-obs-access-key
# OBS_SECRET_KEY=your-obs-secret-key
# OBS_ENDPOINT=https://obs.tr-west-1.myhuaweicloud.com
# OBS_BUCKET_NAME=your-bucket-name

# ------------------ Server Configuration ------------------
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=127.0.0.1
HEALTH_CHECK_PORT=8080
LOG_LEVEL=INFO

# ------------------ RAG Configuration ------------------
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048
RETRIEVAL_TOP_K=5

# ------------------ Feature Flags ------------------
GRAPH_RAG_ENABLED=true
AGENTIC_RAG_ENABLED=true
AGENT_MAX_ITERATIONS=5
ENVEOF
        
        chown ${APP_USER}:${APP_USER} "$ENV_FILE"
        chmod 600 "$ENV_FILE"
        log_warning "Environment file created: ${ENV_FILE}"
        log_warning "⚠️  Please edit .env file and enter your API keys!"
    else
        log_success "Environment file already exists"
    fi
}

# =============================================================================
# 8. Systemd Services
# =============================================================================

create_systemd_services() {
    log_info "Creating systemd services..."
    
    # Streamlit Service
    cat > /etc/systemd/system/${APP_NAME}-app.service << SVCEOF
[Unit]
Description=Huawei Cloud AI Health Assistant - Streamlit App
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}/app
Environment="PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${APP_DIR}/app/.env
ExecStart=${APP_DIR}/venv/bin/streamlit run app.py \\
    --server.port=${STREAMLIT_PORT} \\
    --server.address=127.0.0.1 \\
    --server.headless=true \\
    --server.enableCORS=false \\
    --server.enableXsrfProtection=true \\
    --browser.gatherUsageStats=false
Restart=always
RestartSec=10
StandardOutput=append:${APP_DIR}/logs/streamlit.log
StandardError=append:${APP_DIR}/logs/streamlit-error.log

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SVCEOF
    
    # Health Check Service
    cat > /etc/systemd/system/${APP_NAME}-health.service << SVCEOF
[Unit]
Description=Huawei Cloud AI Health Assistant - Health Check
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}/app
Environment="PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=${APP_DIR}/app/.env
ExecStart=${APP_DIR}/venv/bin/python health_check.py
Restart=always
RestartSec=10
StandardOutput=append:${APP_DIR}/logs/health.log
StandardError=append:${APP_DIR}/logs/health-error.log

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SVCEOF
    
    systemctl daemon-reload
    log_success "Systemd services created"
}

# =============================================================================
# 9. Log Rotation
# =============================================================================

setup_logrotate() {
    log_info "Configuring log rotation..."
    
    cat > /etc/logrotate.d/${APP_NAME} << LOGEOF
${APP_DIR}/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ${APP_USER} ${APP_USER}
    sharedscripts
    postrotate
        systemctl reload ${APP_NAME}-app > /dev/null 2>&1 || true
    endscript
}
LOGEOF
    
    log_success "Log rotation configured"
}

# =============================================================================
# 10. Firewall Configuration
# =============================================================================

setup_firewall() {
    log_info "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp comment 'SSH'
        ufw allow 80/tcp comment 'HTTP'
        ufw allow 443/tcp comment 'HTTPS'
        
        # Block internal ports (localhost only)
        ufw deny 8501/tcp comment 'Streamlit - internal only'
        ufw deny 8080/tcp comment 'Health - internal only'
        
        log_success "Firewall rules added"
        log_warning "To enable UFW: sudo ufw enable"
    else
        log_warning "UFW not found. Check security group settings."
    fi
}

# =============================================================================
# 11. Start Services
# =============================================================================

start_services() {
    log_info "Starting services..."
    
    # Nginx test
    nginx -t || log_error "Nginx configuration error!"
    
    # Enable services
    systemctl enable ${APP_NAME}-app
    systemctl enable ${APP_NAME}-health
    systemctl enable nginx
    
    # Start services
    systemctl restart ${APP_NAME}-app
    systemctl restart ${APP_NAME}-health
    systemctl restart nginx
    
    log_success "All services started"
}

# =============================================================================
# Installation Summary
# =============================================================================

print_summary() {
    # Check service status
    APP_STATUS=$(systemctl is-active ${APP_NAME}-app 2>/dev/null || echo "inactive")
    HEALTH_STATUS=$(systemctl is-active ${APP_NAME}-health 2>/dev/null || echo "inactive")
    NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null || echo "inactive")
    
    # Get ECS IP
    ECS_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "<ECS_IP>")
    
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    Installation Complete!                        ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}📁 Directory Structure:${NC}"
    echo "   ${APP_DIR}/app    - Application files"
    echo "   ${APP_DIR}/venv   - Python virtual environment"
    echo "   ${APP_DIR}/logs   - Log files"
    echo ""
    echo -e "${GREEN}🔧 Service Status:${NC}"
    echo "   ${APP_NAME}-app     : ${APP_STATUS}"
    echo "   ${APP_NAME}-health  : ${HEALTH_STATUS}"
    echo "   nginx              : ${NGINX_STATUS}"
    echo ""
    echo -e "${GREEN}🌐 Endpoints:${NC}"
    echo "   Application : https://${ECS_IP}"
    echo "   Health      : https://${ECS_IP}/health"
    echo ""
    echo -e "${YELLOW}⚠️  Important Steps:${NC}"
    echo "   1. Edit the .env file:"
    echo "      ${BLUE}nano ${APP_DIR}/app/.env${NC}"
    echo ""
    echo "   2. Restart services:"
    echo "      ${BLUE}sudo systemctl restart ${APP_NAME}-app ${APP_NAME}-health${NC}"
    echo ""
    echo "   3. Monitor logs:"
    echo "      ${BLUE}tail -f ${APP_DIR}/logs/streamlit.log${NC}"
    echo ""
    echo -e "${GREEN}📋 Security Group Settings:${NC}"
    echo "   Inbound: TCP 22 (SSH), TCP 80 (HTTP), TCP 443 (HTTPS)"
    echo ""
}

# =============================================================================
# Main Installation Flow
# =============================================================================

main() {
    print_banner
    check_root
    
    prepare_system
    install_python
    install_nginx
    setup_app_directory
    deploy_application
    setup_virtualenv
    create_env_file
    create_systemd_services
    setup_logrotate
    setup_firewall
    start_services
    
    print_summary
}

# Run script
main "$@"
