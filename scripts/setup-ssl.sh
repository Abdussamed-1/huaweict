#!/bin/bash
# =============================================================================
# Let's Encrypt SSL Certificate Installation Script
# Usage: sudo ./setup-ssl.sh your-domain.com
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# Domain check
DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "Usage: sudo $0 <domain>"
    echo "Example: sudo $0 health.example.com"
    exit 1
fi

# Root check
if [ "$EUID" -ne 0 ]; then
    log_error "Please run this script as root: sudo $0 $DOMAIN"
fi

log_info "Installing Let's Encrypt SSL certificate: $DOMAIN"

# Certbot installation
log_info "Installing Certbot..."
apt-get update -qq
apt-get install -y -qq certbot python3-certbot-nginx

# Set Nginx to temporary HTTP-only mode
log_info "Preparing Nginx configuration..."

# Temporary HTTP-only config
cat > /etc/nginx/sites-available/huaweict-temp << TMPEOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
TMPEOF

# Activate temporary config
ln -sf /etc/nginx/sites-available/huaweict-temp /etc/nginx/sites-enabled/huaweict-temp
rm -f /etc/nginx/sites-enabled/huaweict 2>/dev/null || true
systemctl reload nginx

# Obtain SSL certificate
log_info "Obtaining SSL certificate..."
certbot certonly --webroot \
    -w /var/www/html \
    -d ${DOMAIN} \
    --non-interactive \
    --agree-tos \
    --email admin@${DOMAIN} \
    --no-eff-email

# Update certificate paths
log_info "Updating Nginx configuration..."

# Update main Nginx config
sed -i "s|/etc/nginx/ssl/fullchain.pem|/etc/letsencrypt/live/${DOMAIN}/fullchain.pem|g" /etc/nginx/sites-available/huaweict
sed -i "s|/etc/nginx/ssl/privkey.pem|/etc/letsencrypt/live/${DOMAIN}/privkey.pem|g" /etc/nginx/sites-available/huaweict
sed -i "s|server_name _;|server_name ${DOMAIN};|g" /etc/nginx/sites-available/huaweict

# Activate main config, remove temporary config
ln -sf /etc/nginx/sites-available/huaweict /etc/nginx/sites-enabled/huaweict
rm -f /etc/nginx/sites-enabled/huaweict-temp
rm -f /etc/nginx/sites-available/huaweict-temp

# Nginx test and reload
nginx -t || log_error "Nginx configuration error!"
systemctl reload nginx

# Auto-renewal cron job
log_info "Configuring automatic renewal..."
(crontab -l 2>/dev/null | grep -v certbot; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -

log_success "SSL certificate installed successfully!"
echo ""
echo -e "${GREEN}Certificate Information:${NC}"
echo "  Domain      : ${DOMAIN}"
echo "  Certificate : /etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
echo "  Key         : /etc/letsencrypt/live/${DOMAIN}/privkey.pem"
echo ""
echo -e "${GREEN}Endpoint:${NC}"
echo "  https://${DOMAIN}"
echo ""
echo -e "${YELLOW}Note:${NC} Certificate will be renewed automatically."
