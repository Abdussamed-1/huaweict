# Cloud Deployment Guide

Bu rehber, uygulamanın cloud ortamına (Huawei Cloud ECS) deploy edilmesi için gerekli adımları açıklar.

## 📋 Önkoşullar

- Huawei Cloud hesabı
- ECS instance (Ubuntu 22.04 önerilir)
- Milvus Cloud cluster
- DeepSeek API key veya ModelArts endpoint
- Domain name (opsiyonel)

## 🚀 Hızlı Başlangıç

### 1. ECS Instance Hazırlığı

```bash
# SSH ile bağlan
ssh ubuntu@your-ecs-ip

# Sistem güncellemesi
sudo apt update && sudo apt upgrade -y

# Python 3.11 kurulumu
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Proje dizini oluştur
sudo mkdir -p /opt/huaweict/app
sudo chown ubuntu:ubuntu /opt/huaweict/app
cd /opt/huaweict/app
```

### 2. Kod Deployment

```bash
# Repository'yi clone et
git clone <your-repo-url> .

# veya SCP ile upload
# scp -r . ubuntu@your-ecs-ip:/opt/huaweict/app/
```

### 3. Environment Variables

```bash
# .env dosyası oluştur
nano .env

# Aşağıdaki değişkenleri doldur:
# - DEEPSEEK_API_KEY
# - MILVUS_HOST, MILVUS_API_KEY
# - RDS_HOST, RDS_USER, RDS_PASSWORD (opsiyonel)
# - OBS_ACCESS_KEY, OBS_SECRET_KEY (opsiyonel)
```

### 4. Dependencies Kurulumu

```bash
# Virtual environment oluştur
python3.11 -m venv venv
source venv/bin/activate

# Dependencies kur
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Systemd Service Kurulumu

```bash
# setup_ecs.sh scriptini çalıştır
chmod +x setup_ecs.sh
./setup_ecs.sh

# veya manuel olarak:
sudo systemctl enable huaweict-streamlit
sudo systemctl enable huaweict-health
sudo systemctl start huaweict-streamlit
sudo systemctl start huaweict-health
```

## 🔧 Yapılandırma

### Environment Variables

Tüm yapılandırma `.env` dosyasından yapılır. Örnek:

```env
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_USE_DIRECT_API=true

# Milvus
MILVUS_HOST=your-milvus-host.com
MILVUS_PORT=443
MILVUS_API_KEY=your-milvus-key
MILVUS_USE_CLOUD=true

# Logging
LOG_LEVEL=INFO

# Server
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
HEALTH_CHECK_PORT=8080
```

### Port Yapılandırması

- **8501**: Streamlit uygulaması
- **8080**: Health check servisi

Security group'da bu portları açın:
- Inbound: TCP 8501, 8080 from 0.0.0.0/0 (veya ELB IP)

## 🏥 Health Check

Health check endpoint'leri:

- `GET /health` - Kapsamlı health check (Milvus, RDS kontrolü)
- `GET /health/liveness` - Liveness probe
- `GET /health/readiness` - Readiness probe

Test:
```bash
curl http://localhost:8080/health
```

## 📊 Monitoring

### Logs

```bash
# Streamlit logs
sudo journalctl -u huaweict-streamlit -f

# Health check logs
sudo journalctl -u huaweict-health -f

# Application logs (stdout)
tail -f /opt/huaweict/app/logs/app.log
```

### Metrics

Health check endpoint'inden metrics alabilirsiniz:
```bash
curl http://localhost:8080/health | jq
```

## 🔒 Güvenlik

1. **API Keys**: `.env` dosyasını güvenli tutun, commit etmeyin
2. **Firewall**: Sadece gerekli portları açın
3. **HTTPS**: ELB üzerinden HTTPS kullanın
4. **VPC**: Private subnet kullanın (mümkünse)

## 🐛 Sorun Giderme

### Uygulama başlamıyor

```bash
# Service status kontrol
sudo systemctl status huaweict-streamlit
sudo systemctl status huaweict-health

# Logs kontrol
sudo journalctl -u huaweict-streamlit -n 50
```

### Milvus bağlantı hatası

```bash
# Connection test
python3 test_connection.py

# Network kontrol
telnet $MILVUS_HOST $MILVUS_PORT
```

### Port zaten kullanımda

```bash
# Port kontrol
sudo netstat -tulpn | grep 8501
sudo netstat -tulpn | grep 8080

# Process kill
sudo kill -9 <PID>
```

## 📈 Scaling

### Horizontal Scaling

1. ELB arkasına birden fazla ECS instance ekleyin
2. Health check endpoint'i otomatik olarak yeni instance'ları kontrol eder
3. Session state Streamlit'in memory'sinde tutulur (stateless design)

### Vertical Scaling

1. ECS instance type'ını artırın
2. GPU instance kullanın (embedding için)

## 🔄 Updates

```bash
# Code update
cd /opt/huaweict/app
git pull

# Restart services
sudo systemctl restart huaweict-streamlit
sudo systemctl restart huaweict-health
```

## 📝 Checklist

- [ ] ECS instance oluşturuldu
- [ ] Security group yapılandırıldı
- [ ] .env dosyası oluşturuldu ve dolduruldu
- [ ] Dependencies kuruldu
- [ ] Systemd services kuruldu ve başlatıldı
- [ ] Health check çalışıyor
- [ ] Streamlit app erişilebilir
- [ ] Milvus bağlantısı test edildi
- [ ] Logs kontrol edildi
- [ ] ELB yapılandırıldı (opsiyonel)

---

**Son Güncelleme:** 2024
