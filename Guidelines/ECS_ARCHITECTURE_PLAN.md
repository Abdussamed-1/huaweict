# 🖥️ ECS ve Container Engine Mimari Planı

**Bütçe:** $100 USD  
**Hedef:** Minimum maliyet, maksimum verimlilik

---

## 📊 Senaryo Karşılaştırması

### Senaryo 1: Direkt ECS (Önerilen - En Düşük Maliyet)

**Mimari:**
```
┌─────────────────────────────────────┐
│        1x ECS Instance             │
│  ┌───────────────────────────────┐ │
│  │  Streamlit App (Port 8501)    │ │
│  │  Health Check (Port 8080)    │ │
│  │  Python + Dependencies       │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

**ECS Instance:**
- **Type:** s6.medium.2
- **Specs:** 2 vCPU, 4GB RAM
- **Cost:** ~$30-40/ay
- **OS:** Ubuntu 22.04 LTS
- **Deployment:** Systemd services

**Avantajlar:**
- ✅ En düşük maliyet
- ✅ Basit yapılandırma
- ✅ Hızlı deployment
- ✅ Kolay bakım

**Dezavantajlar:**
- ❌ Auto-scaling yok (manuel scale-up gerekir)
- ❌ Container orchestration yok
- ❌ High availability yok (tek instance)

**Toplam Maliyet:** ~$30-40/ay

---

### Senaryo 2: Container Engine (CCE) - Minimal Cluster

**Mimari:**
```
┌─────────────────────────────────────┐
│    CCE Cluster (1 Node)             │
│  ┌───────────────────────────────┐ │
│  │  Kubernetes Node (ECS)        │ │
│  │  ┌─────────────────────────┐ │ │
│  │  │ Pod: Streamlit App       │ │ │
│  │  │ Pod: Health Check       │ │ │
│  │  └─────────────────────────┘ │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

**CCE Cluster:**
- **Type:** CCE Standard Cluster
- **Node Pool:** 1 node
- **Node Spec:** s6.medium.2 (2 vCPU, 4GB RAM)
- **Cost:** ~$40-50/ay (cluster + node)

**Avantajlar:**
- ✅ Container orchestration
- ✅ Auto-scaling potansiyeli
- ✅ Rolling updates
- ✅ Health checks ve restarts
- ✅ Production-ready

**Dezavantajlar:**
- ❌ Daha yüksek maliyet
- ❌ Daha kompleks yapılandırma
- ❌ Kubernetes bilgisi gerekir

**Toplam Maliyet:** ~$40-50/ay

---

### Senaryo 3: Hybrid - ECS + Docker (Önerilen Orta Yol)

**Mimari:**
```
┌─────────────────────────────────────┐
│        1x ECS Instance             │
│  ┌───────────────────────────────┐ │
│  │  Docker Compose               │ │
│  │  ┌─────────────────────────┐ │ │
│  │  │ Container: Streamlit    │ │ │
│  │  │ Container: Health Check │ │ │
│  │  └─────────────────────────┘ │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

**ECS Instance:**
- **Type:** s6.medium.2
- **Specs:** 2 vCPU, 4GB RAM
- **Cost:** ~$30-40/ay
- **Deployment:** Docker Compose

**Avantajlar:**
- ✅ Containerization avantajları
- ✅ Kolay deployment ve update
- ✅ Environment isolation
- ✅ Direkt ECS kadar ucuz
- ✅ Gelecekte CCE'ye kolay geçiş

**Dezavantajlar:**
- ❌ Auto-scaling yok
- ❌ Orchestration yok (tek host)

**Toplam Maliyet:** ~$30-40/ay

---

## 💰 Maliyet Karşılaştırması

| Senaryo | Aylık Maliyet | İlk Ay Setup | Toplam (2 ay) |
|---------|---------------|--------------|---------------|
| **Direkt ECS** | $30-40 | $35 | $65-75 |
| **CCE Cluster** | $40-50 | $45 | $85-95 |
| **ECS + Docker** | $30-40 | $35 | $65-75 |

**100$ Bütçe ile:**
- Direkt ECS: ~2.5-3 ay
- CCE: ~2 ay
- ECS + Docker: ~2.5-3 ay

---

## 🎯 Önerilen Senaryo: ECS + Docker Compose

### Neden Bu Senaryo?

1. **Maliyet:** Direkt ECS kadar ucuz
2. **Esneklik:** Containerization avantajları
3. **Gelecek:** İhtiyaç olursa CCE'ye kolay geçiş
4. **Basitlik:** Kubernetes kompleksliği yok

### ECS Instance Sayısı: **1 adet**

**Tek instance yeterli çünkü:**
- Streamlit app hafif bir uygulama
- Health check minimal resource kullanır
- Milvus Cloud external (ECS'te değil)
- ModelArts API external (ECS'te değil)
- OBS external (ECS'te değil)

**Resource Kullanımı Tahmini:**
- Streamlit App: ~1-2 GB RAM, ~1 vCPU
- Health Check: ~50 MB RAM, minimal CPU
- System: ~500 MB RAM
- **Toplam:** ~2.5-3 GB RAM / 2 vCPU (4GB RAM'lı instance yeterli)

---

## 🏗️ Detaylı Mimari: ECS + Docker Compose

### Infrastructure

```
┌─────────────────────────────────────────────────────────┐
│              Huawei Cloud VPC                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Public Subnet (10.0.1.0/24)                     │ │
│  │  ┌────────────────────────────────────────────┐  │ │
│  │  │  ECS Instance: s6.medium.2                 │  │ │
│  │  │  • 2 vCPU, 4GB RAM                         │  │ │
│  │  │  • Ubuntu 22.04 LTS                        │  │ │
│  │  │  • Docker + Docker Compose                  │  │ │
│  │  │  • Elastic IP attached                     │  │ │
│  │  │                                             │  │ │
│  │  │  ┌──────────────────────────────────────┐ │  │ │
│  │  │  │  Docker Compose Services:            │ │  │ │
│  │  │  │  • streamlit-app (Port 8501)         │ │  │ │
│  │  │  │  • health-check (Port 8080)          │ │  │ │
│  │  │  └──────────────────────────────────────┘ │  │ │
│  │  └────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Docker Compose Yapılandırması

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  streamlit-app:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: huaweict-streamlit
    ports:
      - "8501:8501"
    environment:
      - MILVUS_HOST=${MILVUS_HOST}
      - MILVUS_PORT=${MILVUS_PORT}
      - MILVUS_API_KEY=${MILVUS_API_KEY}
      - MODELARTS_ENDPOINT=${MODELARTS_ENDPOINT}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      # ... diğer env variables
    volumes:
      - ./:/app
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - huaweict-network

  health-check:
    build:
      context: .
      dockerfile: Dockerfile.health
    container_name: huaweict-health
    ports:
      - "8080:8080"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    networks:
      - huaweict-network

networks:
  huaweict-network:
    driver: bridge
```

---

## 📦 Container Engine (CCE) Senaryosu

Eğer Container Engine kullanmak isterseniz:

### CCE Cluster Yapılandırması

**Cluster Specs:**
- **Cluster Type:** Standard Cluster
- **Kubernetes Version:** 1.25+ (latest stable)
- **Network:** VPC network
- **Node Pool:** 1 node pool

**Node Pool:**
- **Node Count:** 1 (minimum)
- **Instance Type:** s6.medium.2
- **OS:** Ubuntu 22.04
- **Auto-scaling:** Disabled (maliyet için)

**Deployment:**
- **Deployment:** Streamlit app (1 replica)
- **Service:** LoadBalancer veya NodePort
- **Health Check:** Liveness ve Readiness probes

**Maliyet:**
- CCE Cluster: ~$10-15/ay (management)
- Node (ECS): ~$30-40/ay
- **Toplam:** ~$40-55/ay

---

## 🔄 Scaling Senaryoları

### Mevcut Durum (100$ bütçe)
- **1 ECS Instance** yeterli
- Tek instance'da tüm servisler

### Gelecek Scaling (Bütçe artarsa)

**Option 1: Horizontal Scaling (Daha fazla ECS)**
```
2x ECS Instances (s6.medium.2)
+ ELB (Load Balancer)
= ~$70-90/ay
```

**Option 2: Vertical Scaling (Daha büyük ECS)**
```
1x ECS Instance (s6.large.2 - 4 vCPU, 8GB RAM)
= ~$60-80/ay
```

**Option 3: CCE Auto-scaling**
```
CCE Cluster
+ Auto-scaling (1-3 nodes)
= ~$50-120/ay (kullanıma göre)
```

---

## ✅ Önerilen Deployment Planı

### Phase 1: Başlangıç (100$ bütçe)
- **1x ECS Instance** (s6.medium.2)
- **Docker Compose** deployment
- **Direkt EIP** ile erişim
- **Maliyet:** ~$30-40/ay

### Phase 2: Growth (Bütçe artarsa)
- **2x ECS Instances** (s6.medium.2)
- **ELB** ekle
- **Auto-scaling** (opsiyonel)
- **Maliyet:** ~$70-90/ay

### Phase 3: Production (Yüksek trafik)
- **CCE Cluster** (2-3 nodes)
- **Auto-scaling** enabled
- **Monitoring** ve **Logging**
- **Maliyet:** ~$100-150/ay

---

## 📋 ECS Instance Detayları

### Tek Instance Yeterli Çünkü:

1. **Application Layer:**
   - Streamlit app: ~1-2 GB RAM
   - Health check: ~50 MB RAM
   - **Toplam:** ~2-2.5 GB RAM

2. **External Services (ECS'te değil):**
   - Milvus Cloud: External (Zilliz Cloud)
   - ModelArts API: External (Huawei Cloud)
   - OBS: External (Huawei Cloud)

3. **Resource Limits:**
   - s6.medium.2: 4 GB RAM
   - Kullanım: ~2.5 GB
   - **Margin:** ~1.5 GB (yeterli)

### Ne Zaman Daha Fazla ECS Gerekir?

- **Traffic:** >1000 concurrent users
- **Memory:** >3.5 GB kullanımı
- **CPU:** >80% sürekli kullanım
- **High Availability:** Uptime >99.9% gerekiyorsa

---

## 🚀 Deployment Adımları

### Senaryo: ECS + Docker Compose

**1. ECS Instance Oluştur:**
```bash
# Huawei Cloud Console:
- Instance Type: s6.medium.2
- Image: Ubuntu 22.04 LTS
- Network: Public Subnet
- Security Group: sg-app-public
- EIP: Allocate and attach
```

**2. Docker Kurulumu:**
```bash
ssh ubuntu@<EIP>

# Docker kurulumu
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker

# Docker Compose kurulumu
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**3. Application Deployment:**
```bash
# Repository clone
cd /opt/huaweict
git clone <repo-url> app
cd app

# .env dosyasını doldur
nano .env

# Docker Compose ile başlat
docker-compose up -d

# Logs kontrol
docker-compose logs -f
```

---

## 📊 Resource Monitoring

### Monitoring Metrics

**CPU Usage:**
- Normal: <50%
- Warning: 50-70%
- Critical: >70%

**Memory Usage:**
- Normal: <60% (2.4 GB / 4 GB)
- Warning: 60-80%
- Critical: >80%

**Disk Usage:**
- Normal: <70%
- Warning: 70-85%
- Critical: >85%

### Monitoring Tools

```bash
# System resources
htop
# veya
top

# Docker resources
docker stats

# Disk usage
df -h
```

---

## 🎯 Sonuç ve Öneri

### 100$ Bütçe İçin:

**Önerilen:** **1x ECS Instance + Docker Compose**

**Neden:**
- ✅ En düşük maliyet (~$30-40/ay)
- ✅ Containerization avantajları
- ✅ Kolay deployment ve maintenance
- ✅ Gelecekte CCE'ye kolay geçiş
- ✅ Tek instance yeterli (external services sayesinde)

**Container Engine (CCE) Ne Zaman?**
- Bütçe >$150/ay olursa
- Auto-scaling gerekiyorsa
- Multi-region deployment gerekiyorsa
- Enterprise-grade orchestration gerekiyorsa

---

**Son Güncelleme:** 2024  
**Durum:** Ready for Deployment  
**Önerilen ECS Sayısı:** **1 adet** (s6.medium.2)

