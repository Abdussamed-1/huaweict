#!/bin/bash
# =============================================================================
# Huawei Cloud AI Health Assistant - Service Management Script
# Usage: ./manage.sh [start|stop|restart|status|logs]
# =============================================================================

APP_NAME="huaweict"
APP_DIR="/opt/${APP_NAME}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Show service status"
    echo "  logs        - Watch all logs live"
    echo "  logs-app    - Watch application logs only"
    echo "  logs-health - Watch health check logs only"
    echo "  check       - Perform health check"
    echo "  update      - Update application (git pull)"
    echo ""
}

start_services() {
    echo -e "${BLUE}[INFO]${NC} Starting services..."
    sudo systemctl start ${APP_NAME}-app
    sudo systemctl start ${APP_NAME}-health
    sudo systemctl start nginx
    echo -e "${GREEN}[✓]${NC} Services started"
    show_status
}

stop_services() {
    echo -e "${YELLOW}[⚠]${NC} Stopping services..."
    sudo systemctl stop ${APP_NAME}-app
    sudo systemctl stop ${APP_NAME}-health
    echo -e "${GREEN}[✓]${NC} Services stopped"
}

restart_services() {
    echo -e "${BLUE}[INFO]${NC} Restarting services..."
    sudo systemctl restart ${APP_NAME}-app
    sudo systemctl restart ${APP_NAME}-health
    sudo systemctl restart nginx
    echo -e "${GREEN}[✓]${NC} Services restarted"
    sleep 2
    show_status
}

show_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${BLUE}              Service Status                ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
    
    # Streamlit App
    APP_STATUS=$(systemctl is-active ${APP_NAME}-app 2>/dev/null)
    if [ "$APP_STATUS" = "active" ]; then
        echo -e "  ${APP_NAME}-app    : ${GREEN}● active${NC}"
    else
        echo -e "  ${APP_NAME}-app    : ${RED}○ inactive${NC}"
    fi
    
    # Health Check
    HEALTH_STATUS=$(systemctl is-active ${APP_NAME}-health 2>/dev/null)
    if [ "$HEALTH_STATUS" = "active" ]; then
        echo -e "  ${APP_NAME}-health : ${GREEN}● active${NC}"
    else
        echo -e "  ${APP_NAME}-health : ${RED}○ inactive${NC}"
    fi
    
    # Nginx
    NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null)
    if [ "$NGINX_STATUS" = "active" ]; then
        echo -e "  nginx             : ${GREEN}● active${NC}"
    else
        echo -e "  nginx             : ${RED}○ inactive${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════${NC}"
    echo ""
}

show_logs() {
    echo -e "${BLUE}[INFO]${NC} Watching all logs (Ctrl+C to exit)..."
    tail -f ${APP_DIR}/logs/*.log
}

show_app_logs() {
    echo -e "${BLUE}[INFO]${NC} Watching application logs (Ctrl+C to exit)..."
    tail -f ${APP_DIR}/logs/streamlit.log ${APP_DIR}/logs/streamlit-error.log
}

show_health_logs() {
    echo -e "${BLUE}[INFO]${NC} Watching health check logs (Ctrl+C to exit)..."
    tail -f ${APP_DIR}/logs/health.log ${APP_DIR}/logs/health-error.log
}

health_check() {
    echo -e "${BLUE}[INFO]${NC} Performing health check..."
    echo ""
    
    # Local health check
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/health 2>/dev/null)
    
    if [ "$RESPONSE" = "200" ]; then
        echo -e "${GREEN}[✓]${NC} Health check successful (HTTP $RESPONSE)"
        echo ""
        curl -s http://127.0.0.1:8080/health | python3 -m json.tool 2>/dev/null || curl -s http://127.0.0.1:8080/health
    else
        echo -e "${RED}[✗]${NC} Health check failed (HTTP $RESPONSE)"
    fi
    echo ""
}

update_app() {
    echo -e "${BLUE}[INFO]${NC} Updating application..."
    
    cd ${APP_DIR}/app
    
    # Git pull
    if [ -d ".git" ]; then
        git pull origin main
    else
        echo -e "${YELLOW}[⚠]${NC} Git repository not found"
    fi
    
    # Update dependencies
    echo -e "${BLUE}[INFO]${NC} Updating dependencies..."
    ${APP_DIR}/venv/bin/pip install -r requirements.txt --upgrade
    
    # Restart services
    restart_services
    
    echo -e "${GREEN}[✓]${NC} Update completed"
}

# Main menu
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-app)
        show_app_logs
        ;;
    logs-health)
        show_health_logs
        ;;
    check)
        health_check
        ;;
    update)
        update_app
        ;;
    *)
        show_help
        ;;
esac
