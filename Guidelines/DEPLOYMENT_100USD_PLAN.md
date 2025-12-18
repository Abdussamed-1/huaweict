# 💰 100$ Kupon ile Huawei Cloud Deployment Planı

**Bütçe:** $100 USD  
**Hedef:** Production-ready deployment, minimum maliyet  
**Durum:** Optimize edilmiş mimari

---

## 📊 Maliyet Optimizasyonu Stratejisi

### ❌ Kaldırılan/İptal Edilen Servisler (İlk Aşamada)

1. **ELB (Elastic Load Balancer)** - ~$20/ay
   - **Alternatif:** Direkt ECS + EIP kullanımı
   - **Not:** Tek instance ile başlayıp, gerektiğinde eklenebilir

2. **NAT Gateway** - ~$35/ay
   - **Alternatif:** Public subnet kullanımı (outbound internet için)
   - **Not:** Milvus ve diğer servisler public subnet'te olabilir (güvenlik grupları ile korunur)

3. **Auto-Scaling Group** - Ekstra instance maliyeti
   - **Alternatif:** Tek instance ile başla, manuel scale-up

4. **WAF ve DDoS Protection** - Premium servisler
   - **Alternatif:** Security Groups ile temel koruma

5. **RDS (Relational Database)** - ~$50-100/ay
   - **Alternatif:** Gerekli değil (Milvus yeterli)

6. **Managed Milvus** - ~$200/ay
   - **Alternatif:** Mevcut Milvus Cloud (Zilliz) kullanımı veya self-managed

### ✅ Kullanılacak Servisler (Minimum Maliyet)

1. **VPC** - Ücretsiz
2. **ECS Instance** - 1 adet, küçük boyut
3. **EIP (Elastic IP)** - 1 adet, ~$5/ay
4. **OBS Bucket** - Minimal kullanım, ~$2-5/ay
5. **ModelArts API** - Pay-per-use, ~$10-20/ay (kullanıma göre)

---

## 🏗️ Optimize Edilmiş Mimari

```
┌─────────────────────────────────────────────────────────┐
│                    INTERNET / USERS                       │
└───────────────────────────┬───────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              ECS Instance (Public Subnet)                 │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Instance: s6.medium.2 (2 vCPU, 4GB RAM)          │ │
│  │  • Streamlit App (Port 8501)                       │ │
│  │  • Health Check (Port 8080)                        │ │
│  │  • Elastic IP attached                             │ │
│  │  • Security Group: sg-app-public                   │ │
│  └───────────────────────────────────────────────────┘ │
└───────────────────────────┬───────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              EXTERNAL SERVICES                           │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Milvus Cloud (Zilliz) - FREE TIER                 │ │
│  │  • Existing cloud cluster                          │ │
│  │  • Public endpoint                                 │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │  OBS Bucket - Minimal                              │ │
│  │  • Standard storage                                │ │
│  │  • ~10-50 GB                                       │ │
│  └───────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────┐ │
│  │  ModelArts API - Pay-per-use                      │ │
│  │  • DeepSeek v3.1 calls                            │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 💵 Detaylı Maliyet Hesaplaması

### Aylık Maliyet (USD)

| Servis | Spec | Aylık Maliyet |
|--------|------|---------------|
| **VPC** | Free tier | $0 |
| **ECS Instance** | s6.medium.2 (2vCPU, 4GB) | ~$30-40 |
| **EIP** | 1 adet, 5 Mbps | ~$5 |
| **OBS Storage** | 50 GB Standard | ~$2-3 |
| **OBS Requests** | ~10K requests | ~$1-2 |
| **ModelArts API** | ~100K tokens/ay | ~$10-20 |
| **Milvus Cloud** | Free tier (Zilliz) | $0 |
| **Bandwidth** | ~100 GB/ay | ~$5-10 |
| **TOTAL** | | **~$53-82/ay** |

### İlk Ay Maliyeti (Setup dahil)
- Setup ve test: ~$60-90
- **Kalan bütçe:** $10-40 (ikinci ay için)

---

## 🚀 Deployment Adımları (100$ için optimize)

### Phase 1: Infrastructure Setup (1-2 saat)

#### 1.1 VPC Oluşturma
```bash
# Huawei Cloud Console:
1. VPC → Create VPC
   - Name: huaweict-vpc-prod
   - CIDR: 10.0.0.0/16
   - Region: ap-southeast-1 (en ucuz)

2. Create Subnet
   - Name: huaweict-subnet-public
   - CIDR: 10.0.1.0/24
   - Type: Public

3. Create Internet Gateway
   - Attach to VPC

4. Create Security Group
   - Name: sg-app-public
   - Rules:
     * Inbound: SSH (22) from your IP
     * Inbound: HTTP (80) from 0.0.0.0/0
     * Inbound: HTTPS (443) from 0.0.0.0/0
     * Inbound: Custom TCP (8501) from 0.0.0.0/0 (Streamlit)
     * Inbound: Custom TCP (8080) from 0.0.0.0/0 (Health check)
     * Outbound: All traffic
```

#### 1.2 ECS Instance Oluşturma
```bash
# Huawei Cloud Console → ECS → Create Instance

Configuration:
- Instance Type: s6.medium.2
  * vCPU: 2
  * RAM: 4 GB
  * Cost: ~$30-40/ay
  
- Image: Ubuntu 22.04 LTS Server
  
- System Disk: 
  * Type: SSD
  * Size: 40 GB
  
- Network:
  * VPC: huaweict-vpc-prod
  * Subnet: huaweict-subnet-public
  * Security Group: sg-app-public
  
- Elastic IP:
  * Allocate new EIP
  * Bandwidth: 5 Mbps
  * Attach to instance
```

#### 1.3 OBS Bucket Oluşturma
```bash
# Huawei Cloud Console → OBS → Create Bucket

Configuration:
- Name: medical-documents-prod
- Region: ap-southeast-1
- Storage Class: Standard
- Access: Private
- Versioning: Disabled (to save cost)
```

---

### Phase 2: Application Deployment (2-3 saat)

#### 2.1 ECS Instance Setup
```bash
# SSH ile bağlan
ssh ubuntu@<EIP-ADDRESS>

# System update
sudo apt update && sudo apt upgrade -y

# Python 3.11 kurulumu
sudo apt install python3.11 python3.11-venv python3-pip git -y

# Application directory
mkdir -p /opt/huaweict
cd /opt/huaweict
```

#### 2.2 Code Deployment
```bash
# Repository clone (veya SCP ile upload)
git clone <your-repo-url> app
cd app

# Virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Environment variables
nano .env
# .env dosyasını doldur (aşağıdaki template'e göre)
```

#### 2.3 .env Configuration (100$ için optimize)
```env
# Milvus - Mevcut Milvus Cloud kullan
MILVUS_USE_CLOUD=true
MILVUS_HOST=<your-zilliz-cloud-endpoint>
MILVUS_PORT=443
MILVUS_API_KEY=<your-zilliz-api-key>
MILVUS_COLLECTION_NAME=medical_knowledge_base

# OBS - Huawei Cloud OBS
OBS_ACCESS_KEY=<huawei-obs-access-key>
OBS_SECRET_KEY=<huawei-obs-secret-key>
OBS_ENDPOINT=obs.ap-southeast-1.myhuaweicloud.com
OBS_BUCKET_NAME=medical-documents-prod

# ModelArts - DeepSeek API
MODELARTS_ENDPOINT=https://modelarts.ap-southeast-1.myhuaweicloud.com
DEEPSEEK_API_KEY=<huawei-modelarts-api-key>
MODELARTS_MODEL_NAME=deepseek-v3.1

# LLM Configuration
LLM_MODEL=deepseek-v3.1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048

# Fallback - Google Gemini (opsiyonel)
GOOGLE_API_KEY=<your-google-api-key>

# Embedding
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_DEVICE=cpu

# RAG Configuration
RETRIEVAL_TOP_K=5
GRAPH_RAG_ENABLED=true
AGENTIC_RAG_ENABLED=false
```

**Not:** `all-MiniLM-L6-v2` kullanarak embedding boyutunu 384'e düşürdük (768 yerine) - daha hızlı ve daha az memory kullanır.

#### 2.4 Systemd Services

**Streamlit Service:**
```bash
sudo nano /etc/systemd/system/huaweict-streamlit.service
```

```ini
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
```

**Health Check Service:**
```bash
sudo nano /etc/systemd/system/huaweict-health.service
```

```ini
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
```

**Services'i başlat:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable huaweict-streamlit
sudo systemctl enable huaweict-health
sudo systemctl start huaweict-streamlit
sudo systemctl start huaweict-health

# Status kontrol
sudo systemctl status huaweict-streamlit
sudo systemctl status huaweict-health
```

---

### Phase 3: Testing ve Validation (1 saat)

#### 3.1 Health Check Test
```bash
curl http://<EIP-ADDRESS>:8080/health
# Expected: {"status": "healthy", ...}
```

#### 3.2 Application Test
```bash
# Browser'da aç
http://<EIP-ADDRESS>:8501

# Test query gönder
# Milvus connection test
python test_connection.py

# RAG test
python test_rag.py
```

#### 3.3 OBS Test
```python
# Python shell'de test
from obs_client import OBSClient
client = OBSClient()
client.list_documents()
```

---

### Phase 4: Domain ve SSL (Opsiyonel - ekstra maliyet)

**Domain yoksa:**
- Direkt IP ile erişim mümkün
- SSL olmadan HTTP kullanılabilir (development için)

**Domain varsa:**
- DNS A record: domain → EIP
- Let's Encrypt SSL (ücretsiz)
- Nginx reverse proxy (opsiyonel)

---

## 🔧 Troubleshooting

### ECS Instance'a Bağlanamıyorum
```bash
# Security Group kontrolü
# SSH port (22) açık mı?
# EIP doğru mu?

# Firewall kontrolü
sudo ufw status
sudo ufw allow 22
sudo ufw allow 8501
sudo ufw allow 8080
```

### Milvus Connection Error
```bash
# .env dosyasını kontrol et
# MILVUS_HOST, MILVUS_API_KEY doğru mu?
# Network connectivity test
curl -v https://<milvus-host>:443
```

### ModelArts API Error
```bash
# API key doğru mu?
# Endpoint doğru mu?
# Rate limit kontrolü
```

---

## 📈 Scaling Planı (Gelecekte)

100$ bittikten sonra, gerektiğinde:

1. **ELB ekle** - $20/ay
2. **Daha büyük ECS** - s6.large.2 (4vCPU, 8GB) - $60/ay
3. **Auto-scaling** - 2-3 instance
4. **Managed Milvus** - $200/ay (self-managed yerine)

---

## ✅ Deployment Checklist

- [ ] VPC ve subnet oluşturuldu
- [ ] Security group yapılandırıldı
- [ ] ECS instance oluşturuldu ve EIP atandı
- [ ] OBS bucket oluşturuldu
- [ ] Application code deploy edildi
- [ ] .env dosyası dolduruldu
- [ ] Dependencies kuruldu
- [ ] Systemd services başlatıldı
- [ ] Health check çalışıyor
- [ ] Streamlit app çalışıyor
- [ ] Milvus connection test edildi
- [ ] OBS connection test edildi
- [ ] ModelArts API test edildi
- [ ] End-to-end test yapıldı

---

## 🎯 Başarı Kriterleri

1. ✅ Application erişilebilir (http://<EIP>:8501)
2. ✅ Health check çalışıyor (http://<EIP>:8080/health)
3. ✅ Milvus queries başarılı
4. ✅ ModelArts API calls başarılı
5. ✅ OBS upload/download çalışıyor
6. ✅ Aylık maliyet < $100

---

**Son Güncelleme:** 2024  
**Durum:** Ready for Deployment  
**Tahmini Deployment Süresi:** 4-6 saat

