#!/bin/bash
# ECS Instance Setup Script
# Run this script on the ECS instance after SSH connection

set -e

echo "🔧 Setting up ECS instance for Huawei Cloud AI Health Assistant..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Install system dependencies for sentence-transformers
echo "📚 Installing system dependencies..."
sudo apt install -y build-essential

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/huaweict
sudo chown ubuntu:ubuntu /opt/huaweict
cd /opt/huaweict

# Clone repository (or upload files via SCP)
echo "📥 Cloning repository..."
# git clone <your-repo-url> app
# OR: Upload files via SCP from local machine
# scp -r /path/to/local/repo/* ubuntu@<EIP>:/opt/huaweict/app/

cd app

# Create virtual environment
echo "🔌 Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file (user should fill this)
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit /opt/huaweict/app/.env with your credentials!"
fi

# Create systemd service files
echo "⚙️  Creating systemd services..."

# Streamlit service
sudo tee /etc/systemd/system/huaweict-streamlit.service > /dev/null <<EOF
[Unit]
Description=Huawei Cloud AI Health Assistant Streamlit App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/huaweict/app
Environment="PATH=/opt/huaweict/app/venv/bin"
ExecStart=/opt/huaweict/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Health check service
sudo tee /etc/systemd/system/huaweict-health.service > /dev/null <<EOF
[Unit]
Description=Huawei Cloud AI Health Assistant Health Check
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/huaweict/app
Environment="PATH=/opt/huaweict/app/venv/bin"
ExecStart=/opt/huaweict/app/venv/bin/python health_check.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "✅ Enabling services..."
sudo systemctl enable huaweict-streamlit
sudo systemctl enable huaweict-health

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 8501/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/huaweict/app/.env with your credentials"
echo "2. Start services:"
echo "   sudo systemctl start huaweict-streamlit"
echo "   sudo systemctl start huaweict-health"
echo "3. Check status:"
echo "   sudo systemctl status huaweict-streamlit"
echo "   sudo systemctl status huaweict-health"
echo "4. Test health check: curl http://localhost:8080/health"
echo "5. Test application: curl http://localhost:8501"

