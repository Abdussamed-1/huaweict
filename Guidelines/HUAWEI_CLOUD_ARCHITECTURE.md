# 🏗️ Huawei Cloud Uçtan Uca Mimari Dokümantasyonu

**Proje:** Huawei Cloud AI Health Assistant  
**Tarih:** 2024  
**Durum:** Mimari Tasarım ve Deployment Planı

---

## 📋 İçindekiler

1. [Genel Mimari Genel Bakış](#genel-mimari-genel-bakış)
2. [Ağ Katmanı (VPC) Detayları](#ağ-katmanı-vpc-detayları)
3. [Hesaplama Katmanı (ECS) Detayları](#hesaplama-katmanı-ecs-detayları)
4. [Yük Dengeleme (ELB) Yapılandırması](#yük-dengeleme-elb-yapılandırması)
5. [Veri Katmanı - Milvus Vector Database](#veri-katmanı---milvus-vector-database)
6. [Depolama Katmanı - OBS (Object Storage Service)](#depolama-katmanı---obs-object-storage-service)
7. [AI/ML Katmanı - ModelArts DeepSeek Entegrasyonu](#aiml-katmanı---modelarts-deepseek-entegrasyonu)
8. [External Access ve Güvenlik](#external-access-ve-güvenlik)
9. [Milvus Transfer Süreci](#milvus-transfer-süreci)
10. [Deployment Adımları](#deployment-adımları)

---

## 🎯 Genel Mimari Genel Bakış

### Mimari Diyagramı

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERNET / EXTERNAL USERS                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ELB (Elastic Load Balancer)                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  • HTTPS Listener (Port 443)                                     │  │
│  │  • HTTP Listener (Port 80) → HTTPS Redirect                      │  │
│  │  • Health Check: /health endpoint                                │  │
│  │  • SSL/TLS Certificate (Let's Encrypt veya Huawei SSL)          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         VPC (Virtual Private Cloud)                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  VPC CIDR: 10.0.0.0/16                                          │  │
│  │  Region: ap-southeast-1 (Singapore) veya eu-west-1              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  PUBLIC SUBNET (10.0.1.0/24)                                     │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  ECS Instance Group (Application Servers)                  │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  ECS-1: Streamlit App Server                         │ │  │  │
│  │  │  │  • Instance Type: s6.xlarge.2 (4 vCPU, 8GB RAM)      │ │  │  │
│  │  │  │  • OS: Ubuntu 22.04 LTS                               │ │  │  │
│  │  │  │  • Python 3.11+                                       │ │  │  │
│  │  │  │  • Elastic IP (EIP) attached                          │ │  │  │
│  │  │  │  • Security Group: sg-app-public                       │ │  │  │
│  │  │  └──────────────────────────────────────────────────────┘ │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  ECS-2: Streamlit App Server (Auto-scaling)         │ │  │  │
│  │  │  │  • Same configuration as ECS-1                      │ │  │  │
│  │  │  └──────────────────────────────────────────────────────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  NAT Gateway (Optional - for outbound internet access)    │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  PRIVATE SUBNET (10.0.2.0/24)                                    │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  Milvus Cluster (Vector Database)                         │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  Option 1: Huawei Cloud Milvus Service               │ │  │  │
│  │  │  │  • Managed Milvus instance                            │ │  │  │
│  │  │  │  • High availability                                 │ │  │  │
│  │  │  │  • Auto-scaling                                      │ │  │  │
│  │  │  └──────────────────────────────────────────────────────┘ │  │  │
│  │  │  ┌──────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  Option 2: Self-managed Milvus on ECS                │ │  │  │
│  │  │  │  • ECS Instance: s6.2xlarge.4 (8 vCPU, 16GB RAM)    │ │  │  │
│  │  │  │  • Docker container with Milvus                      │ │  │  │
│  │  │  │  • Persistent storage: EVS (Elastic Volume Service) │ │  │  │
│  │  │  │  • Security Group: sg-db-private                     │ │  │  │
│  │  │  └──────────────────────────────────────────────────────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  RDS (Relational Database) - Optional                      │  │  │
│  │  │  • PostgreSQL/MySQL for metadata                          │  │  │
│  │  │  • User sessions, logs, etc.                              │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  PRIVATE SUBNET (10.0.3.0/24) - AI/ML Services                  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  ModelArts Endpoint (DeepSeek v3.1)                       │  │  │
│  │  │  • Private endpoint for secure access                     │  │  │
│  │  │  • Ascend chip acceleration                               │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES LAYER                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  OBS (Object Storage Service)                                    │  │
│  │  • Bucket: medical-documents-prod                                │  │
│  │  • Region: Same as VPC                                           │  │
│  │  • Storage Class: Standard                                       │  │
│  │  • Access: Private (via IAM roles)                               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ModelArts Studio (MaaS) - DeepSeek API                          │  │
│  │  • Public API endpoint                                           │  │
│  │  • API Key authentication                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Cloud Log Service (LTS)                                         │  │
│  │  • Centralized logging                                           │  │
│  │  • Log aggregation and analysis                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Cloud Eye (Monitoring & Alerting)                               │  │
│  │  • System metrics                                                │  │
│  │  • Application performance monitoring                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🌐 Ağ Katmanı (VPC) Detayları

### VPC Yapılandırması

#### 1. VPC Oluşturma

```yaml
VPC Configuration:
  Name: huaweict-vpc-prod
  CIDR Block: 10.0.0.0/16
  Region: ap-southeast-1 (Singapore) veya eu-west-1
  Description: Production VPC for AI Health Assistant
```

**Adımlar:**
1. Huawei Cloud Console → VPC → Create VPC
2. CIDR: `10.0.0.0/16` seç
3. Region seçimi (kullanıcılarınıza en yakın)
4. Enterprise Project'e atama (opsiyonel)

#### 2. Subnet Yapılandırması

**Public Subnet (10.0.1.0/24)**
- **Amaç:** ECS application server'ları için
- **Route Table:** Internet Gateway'e bağlı
- **Kullanım:** Streamlit uygulaması, external access
- **NAT Gateway:** Gerekirse outbound internet için

**Private Subnet 1 (10.0.2.0/24)**
- **Amaç:** Database ve internal services
- **Route Table:** NAT Gateway üzerinden internet (outbound only)
- **Kullanım:** Milvus cluster, RDS (opsiyonel)
- **Güvenlik:** Internet'ten direkt erişim YOK

**Private Subnet 2 (10.0.3.0/24)**
- **Amaç:** AI/ML services
- **Route Table:** NAT Gateway üzerinden internet
- **Kullanım:** ModelArts private endpoints, internal AI services

#### 3. Internet Gateway (IGW)

```yaml
Internet Gateway:
  Name: huaweict-igw-prod
  Attached to: huaweict-vpc-prod
  Purpose: Public subnet'ten internet erişimi
```

#### 4. NAT Gateway (Opsiyonel)

```yaml
NAT Gateway:
  Name: huaweict-nat-prod
  Subnet: Public Subnet (10.0.1.0/24)
  Elastic IP: Required
  Purpose: Private subnet'lerden outbound internet erişimi
  Cost: ~$0.05/hour (check current pricing)
```

**Kullanım Senaryoları:**
- Private subnet'teki Milvus'un external API'lere erişimi
- ModelArts API çağrıları için outbound access
- Package updates, pip installs

#### 5. Route Tables

**Public Route Table:**
```
Destination          Target
10.0.0.0/16         Local
0.0.0.0/0           Internet Gateway
```

**Private Route Table:**
```
Destination          Target
10.0.0.0/16         Local
0.0.0.0/0           NAT Gateway (if configured)
```

#### 6. Security Groups

**Security Group: sg-app-public**
```yaml
Inbound Rules:
  - Type: HTTPS
    Port: 443
    Source: 0.0.0.0/0
    Description: HTTPS from ELB
  
  - Type: HTTP
    Port: 80
    Source: 0.0.0.0/0
    Description: HTTP from ELB
  
  - Type: SSH
    Port: 22
    Source: <Your-IP>/32
    Description: SSH access for management

Outbound Rules:
  - Type: All Traffic
    Port: All
    Destination: 0.0.0.0/0
    Description: All outbound traffic
```

**Security Group: sg-db-private**
```yaml
Inbound Rules:
  - Type: Custom TCP
    Port: 19530 (Milvus port)
    Source: sg-app-public
    Description: Milvus access from app servers
  
  - Type: Custom TCP
    Port: 9091 (Milvus metrics)
    Source: sg-app-public
    Description: Milvus metrics

Outbound Rules:
  - Type: HTTPS
    Port: 443
    Destination: 0.0.0.0/0
    Description: Outbound HTTPS for API calls
```

**Security Group: sg-elb**
```yaml
Inbound Rules:
  - Type: HTTPS
    Port: 443
    Source: 0.0.0.0/0
    Description: Public HTTPS access
  
  - Type: HTTP
    Port: 80
    Source: 0.0.0.0/0
    Description: Public HTTP access

Outbound Rules:
  - Type: All Traffic
    Port: All
    Destination: sg-app-public
    Description: Forward to app servers
```

---

## 💻 Hesaplama Katmanı (ECS) Detayları

### ECS Instance Yapılandırması

#### 1. ECS Instance Specs

**Production ECS Instance:**
```yaml
Instance Configuration:
  Name: huaweict-app-server-1
  Instance Type: s6.xlarge.2
    - vCPU: 4
    - RAM: 8 GB
    - Network: High Performance
    - Disk I/O: High
  
  Alternative (for higher load):
  Instance Type: s6.2xlarge.2
    - vCPU: 8
    - RAM: 16 GB
  
  OS: Ubuntu 22.04 LTS Server
  System Disk: 
    - Type: SSD
    - Size: 40 GB
    - Disk Type: Ultra-high I/O (SSD)
  
  Data Disk (Optional):
    - Type: SSD
    - Size: 100 GB
    - Purpose: Application data, logs
```

#### 2. ECS Deployment Adımları

**a) Instance Oluşturma:**
1. Huawei Cloud Console → ECS → Create Instance
2. Region: VPC ile aynı region
3. Availability Zone: Multi-AZ için farklı AZ'ler seç
4. Network: Public Subnet (10.0.1.0/24) seç
5. Security Group: sg-app-public
6. Elastic IP: Allocate and attach

**b) Initial Setup:**
```bash
# SSH ile bağlan
ssh ubuntu@<EIP-ADDRESS>

# System update
sudo apt update && sudo apt upgrade -y

# Python 3.11+ kurulumu
sudo apt install python3.11 python3.11-venv python3-pip -y

# Git kurulumu
sudo apt install git -y

# Docker kurulumu (opsiyonel, Milvus için)
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker

# Application directory oluştur
mkdir -p /opt/huaweict
cd /opt/huaweict
```

**c) Application Deployment:**
```bash
# Repository clone
git clone <your-repo-url> /opt/huaweict/app

# Virtual environment oluştur
cd /opt/huaweict/app
python3.11 -m venv venv
source venv/bin/activate

# Dependencies kurulumu
pip install --upgrade pip
pip install -r requirements.txt

# Environment variables
sudo nano /opt/huaweict/app/.env
# .env dosyasını doldur (aşağıdaki bölümde detaylar)
```

**d) Systemd Service Oluşturma:**
```bash
# Streamlit service dosyası oluştur
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
ExecStart=/opt/huaweict/app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Service'i başlat
sudo systemctl daemon-reload
sudo systemctl enable huaweict-streamlit
sudo systemctl start huaweict-streamlit
sudo systemctl status huaweict-streamlit
```

#### 3. Auto-Scaling Configuration

**Auto Scaling Group:**
```yaml
Auto Scaling Group:
  Name: huaweict-asg-prod
  Min Instances: 1
  Max Instances: 5
  Desired Capacity: 2
  
  Scaling Policies:
    Scale Up:
      Metric: CPU Utilization > 70%
      Cooldown: 300 seconds
      Action: Add 1 instance
    
    Scale Down:
      Metric: CPU Utilization < 30%
      Cooldown: 600 seconds
      Action: Remove 1 instance
  
  Health Check:
    Type: ELB health check
    Grace Period: 300 seconds
```

---

## ⚖️ Yük Dengeleme (ELB) Yapılandırması

### ELB Setup

#### 1. ELB Instance Oluşturma

```yaml
ELB Configuration:
  Name: huaweict-elb-prod
  Type: Application Load Balancer (ALB)
  Network: Public Subnet (10.0.1.0/24)
  Security Group: sg-elb
  
  Listeners:
    - Protocol: HTTPS
      Port: 443
      Certificate: SSL Certificate (Let's Encrypt or Huawei SSL)
      Default Action: Forward to Target Group
    
    - Protocol: HTTP
      Port: 80
      Default Action: Redirect to HTTPS
```

#### 2. Target Group Yapılandırması

```yaml
Target Group:
  Name: huaweict-tg-app
  Protocol: HTTP
  Port: 8501 (Streamlit default port)
  
  Health Check:
    Protocol: HTTP
    Path: /health
    Port: 8501
    Interval: 30 seconds
    Timeout: 5 seconds
    Healthy Threshold: 2
    Unhealthy Threshold: 3
  
  Targets:
    - ECS Instance 1: Port 8501
    - ECS Instance 2: Port 8501
    - Auto-scaling instances: Port 8501
```

#### 3. SSL/TLS Certificate

**Option 1: Huawei Cloud SSL Certificate Service**
- Huawei Cloud Console → SSL Certificate Manager
- Upload existing certificate veya purchase new one
- Bind to ELB listener

**Option 2: Let's Encrypt (Free)**
```bash
# ECS instance'da certbot kurulumu
sudo apt install certbot -y

# Certificate oluştur
sudo certbot certonly --standalone -d yourdomain.com

# Certificate'leri ELB'ye upload et
# Huawei Cloud Console → SSL Certificate Manager → Import Certificate
```

#### 4. Health Check Endpoint

**app.py'ye health check ekle:**
```python
# app.py içine ekle
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health_check():
    return {'status': 'healthy'}, 200
```

---

## 🗄️ Veri Katmanı - Milvus Vector Database

### Milvus Deployment Seçenekleri

#### Option 1: Huawei Cloud Managed Milvus (Önerilen)

**Avantajlar:**
- Fully managed service
- Auto-scaling
- High availability
- Automatic backups
- Monitoring built-in

**Yapılandırma:**
```yaml
Managed Milvus:
  Service Name: huaweict-milvus-prod
  Version: Milvus 2.3+
  Instance Type: 
    - Small: 2 vCPU, 4GB RAM (dev/test)
    - Medium: 4 vCPU, 8GB RAM (production)
    - Large: 8 vCPU, 16GB RAM (high load)
  
  Network: Private Subnet (10.0.2.0/24)
  Security: VPC peering veya private endpoint
  Backup: Daily automatic backups
  Multi-AZ: Enabled for HA
```

**Connection String:**
```python
# .env dosyasına ekle
MILVUS_HOST=milvus-xxx.huaweicloud.com
MILVUS_PORT=19530
MILVUS_USE_CLOUD=true
MILVUS_API_KEY=<huawei-cloud-api-key>
MILVUS_COLLECTION_NAME=medical_knowledge_base
```

#### Option 2: Self-Managed Milvus on ECS

**ECS Instance Specs:**
```yaml
Milvus ECS Instance:
  Instance Type: s6.2xlarge.4
    - vCPU: 8
    - RAM: 16 GB
  
  OS: Ubuntu 22.04 LTS
  System Disk: 40 GB SSD
  Data Disk: 500 GB Ultra-high I/O SSD
  
  Network: Private Subnet (10.0.2.0/24)
  Security Group: sg-db-private
```

**Docker Deployment:**
```yaml
# docker-compose.yml
version: '3.5'

services:
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9001:9001"
      - "9000:9000"
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  standalone:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.3
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - "etcd"
      - "minio"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      start_period: 90s
      timeout: 20s
      retries: 3

volumes:
  etcd_data:
  minio_data:
  milvus_data:
```

**Deployment:**
```bash
# ECS instance'da
cd /opt/milvus
sudo docker-compose up -d

# Health check
curl http://localhost:9091/healthz
```

### Milvus Collection Schema

```python
# Collection schema for medical knowledge base
from pymilvus import CollectionSchema, FieldSchema, DataType

fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
    FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=2000),
    FieldSchema(name="response", dtype=DataType.VARCHAR, max_length=10000),
    FieldSchema(name="combined_embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="related_nodes", dtype=DataType.ARRAY, element_type=DataType.VARCHAR),
    FieldSchema(name="metadata", dtype=DataType.JSON)
]

schema = CollectionSchema(
    fields=fields,
    description="Medical knowledge base with GraphRAG support"
)
```

---

## 📦 Depolama Katmanı - OBS (Object Storage Service)

### OBS Bucket Yapılandırması

#### 1. Bucket Oluşturma

```yaml
OBS Bucket Configuration:
  Name: medical-documents-prod
  Region: Same as VPC (ap-southeast-1)
  Storage Class: Standard
  Data Redundancy: Multi-AZ (for high availability)
  
  Access Control:
    Bucket Policy: Private
    Public Access: Blocked
    Access via: IAM roles and policies
  
  Versioning: Enabled (for document history)
  Lifecycle Rules:
    - Transition to Infrequent Access after 30 days
    - Archive after 90 days
    - Delete after 1 year (if not accessed)
```

#### 2. Bucket Structure

```
medical-documents-prod/
├── raw-documents/          # Original uploaded documents
│   ├── pdf/
│   ├── docx/
│   └── txt/
├── processed/              # Processed and chunked documents
│   ├── embeddings/
│   └── metadata/
├── backups/                # Backup files
└── temp/                   # Temporary uploads
```

#### 3. IAM Policy for OBS Access

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "obs:GetObject",
        "obs:PutObject",
        "obs:DeleteObject",
        "obs:ListBucket"
      ],
      "Resource": [
        "obs:*:medical-documents-prod/*",
        "obs:*:medical-documents-prod"
      ]
    }
  ]
}
```

#### 4. OBS SDK Integration

**Python SDK Kurulumu:**
```bash
pip install esdk-obs-python
```

**OBS Client Implementation:**
```python
# obs_client.py
from obs import ObsClient
import os
from config import OBS_ACCESS_KEY, OBS_SECRET_KEY, OBS_ENDPOINT, OBS_BUCKET_NAME

class OBSClient:
    def __init__(self):
        self.client = ObsClient(
            access_key_id=OBS_ACCESS_KEY,
            secret_access_key=OBS_SECRET_KEY,
            server=OBS_ENDPOINT
        )
        self.bucket_name = OBS_BUCKET_NAME
    
    def upload_document(self, file_path: str, object_key: str):
        """Upload document to OBS"""
        try:
            resp = self.client.putFile(
                Bucket=self.bucket_name,
                Key=object_key,
                file_path=file_path
            )
            return resp.status < 300
        except Exception as e:
            logger.error(f"OBS upload error: {e}")
            return False
    
    def download_document(self, object_key: str, local_path: str):
        """Download document from OBS"""
        try:
            resp = self.client.getObject(
                Bucket=self.bucket_name,
                Key=object_key,
                downloadPath=local_path
            )
            return resp.status < 300
        except Exception as e:
            logger.error(f"OBS download error: {e}")
            return False
    
    def list_documents(self, prefix: str = ""):
        """List documents in bucket"""
        try:
            resp = self.client.listObjects(
                Bucket=self.bucket_name,
                prefix=prefix
            )
            return [obj.key for obj in resp.body.contents]
        except Exception as e:
            logger.error(f"OBS list error: {e}")
            return []
```

---

## 🤖 AI/ML Katmanı - ModelArts DeepSeek Entegrasyonu

### ModelArts Studio (MaaS) Yapılandırması

#### 1. ModelArts Endpoint Oluşturma

```yaml
ModelArts Configuration:
  Service: ModelArts Studio (MaaS)
  Model: DeepSeek v3.1
  Endpoint Type: 
    - Public API (default)
    - Private Endpoint (VPC içinden)
  
  Authentication:
    Method: API Key
    Key Location: Huawei Cloud Secrets Manager
```

#### 2. DeepSeek API Integration

**API Client Implementation:**
```python
# modelarts_client.py
import requests
import json
from config import MODELARTS_ENDPOINT, DEEPSEEK_API_KEY

class ModelArtsClient:
    def __init__(self):
        self.endpoint = MODELARTS_ENDPOINT
        self.api_key = DEEPSEEK_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": self.api_key
        }
    
    def invoke_deepseek(self, prompt: str, temperature: float = 0.2, max_tokens: int = 2048):
        """Invoke DeepSeek v3.1 model via ModelArts"""
        url = f"{self.endpoint}/v1/chat/completions"
        
        payload = {
            "model": "deepseek-v3.1",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ModelArts API error: {e}")
            return None
```

#### 3. Ascend Chip Acceleration

**Ascend NPU Kullanımı:**
- ModelArts otomatik olarak Ascend chip'leri kullanır
- Özel optimizasyon gerekmez
- Performance: ~2-3x faster than CPU

#### 4. Fallback Mechanism

```python
# rag_service.py içinde
def generate_response(self, prompt: str):
    # Try ModelArts DeepSeek first
    response = self.modelarts_client.invoke_deepseek(prompt)
    
    if response:
        return response
    
    # Fallback to Google Gemini
    logger.warning("ModelArts unavailable, using Gemini fallback")
    return self.gemini_client.generate(prompt)
```

---

## 🔒 External Access ve Güvenlik

### External Access Yapılandırması

#### 1. Elastic IP (EIP) Yapılandırması

```yaml
Elastic IPs:
  EIP-1:
    Name: huaweict-eip-app-1
    Bandwidth: 5 Mbps (adjust based on traffic)
    Type: Dedicated
    Attached to: ECS Instance 1
  
  EIP-2:
    Name: huaweict-eip-app-2
    Bandwidth: 5 Mbps
    Attached to: ECS Instance 2
  
  EIP-NAT:
    Name: huaweict-eip-nat
    Bandwidth: 10 Mbps
    Attached to: NAT Gateway
```

#### 2. Domain Name Configuration

**DNS Setup:**
```
A Record: yourdomain.com → ELB IP Address
CNAME: www.yourdomain.com → ELB DNS Name
```

**Huawei Cloud DNS Service:**
1. Huawei Cloud Console → DNS Service
2. Create hosted zone: `yourdomain.com`
3. Add A record pointing to ELB
4. Update nameservers at domain registrar

#### 3. Security Enhancements

**a) Web Application Firewall (WAF)**
```yaml
WAF Configuration:
  Service: Huawei Cloud WAF
  Protection Rules:
    - SQL Injection Protection
    - XSS Protection
    - DDoS Protection
    - Rate Limiting
    - Bot Protection
  
  Attached to: ELB
```

**b) DDoS Protection**
```yaml
Anti-DDoS:
  Service: Huawei Cloud Anti-DDoS
  Protection Level: Standard (5 Gbps)
  Auto-scaling: Enabled
```

**c) Security Groups Best Practices**
- Least privilege principle
- Only allow necessary ports
- Regular security group audits
- Use security group references instead of IPs

**d) Secrets Management**
```yaml
Huawei Cloud Secrets Manager:
  Secrets:
    - DEEPSEEK_API_KEY
    - MILVUS_API_KEY
    - OBS_ACCESS_KEY
    - OBS_SECRET_KEY
    - GOOGLE_API_KEY
  
  Rotation: Enabled (90 days)
  Access: Via IAM roles
```

#### 4. Monitoring ve Logging

**Cloud Eye (Monitoring):**
```yaml
Metrics to Monitor:
  - ECS CPU Utilization
  - ECS Memory Usage
  - Network In/Out
  - ELB Request Count
  - ELB Error Rate
  - Milvus Query Latency
  - OBS Request Count
  - ModelArts API Latency
  
Alerts:
  - CPU > 80% for 5 minutes
  - Memory > 85% for 5 minutes
  - Error rate > 5%
  - Response time > 5 seconds
```

**Cloud Log Service (LTS):**
```yaml
Log Groups:
  - Application Logs: /opt/huaweict/app/logs
  - System Logs: /var/log
  - Access Logs: ELB access logs
  
Log Retention: 30 days (Standard), 90 days (Premium)
```

---

## 🔄 Milvus Transfer Süreci

### Milvus Migration Planı

#### Phase 1: Pre-Migration Assessment

**1.1 Mevcut Milvus Inventory**
```bash
# Mevcut Milvus'tan bilgi toplama
- Collection sayısı
- Toplam data size
- Index tipleri
- Milvus version
- Network configuration
```

**1.2 Compatibility Check**
- Milvus version compatibility (2.x → 2.x recommended)
- Schema compatibility
- Index compatibility

#### Phase 2: Target Environment Setup

**2.1 Huawei Cloud Milvus Instance Oluşturma**
```yaml
Steps:
  1. Huawei Cloud Console → Vector Database Service
  2. Create Milvus Instance
  3. Select region (same as VPC)
  4. Configure network (Private Subnet)
  5. Set instance specs
  6. Configure security groups
  7. Get connection endpoint and credentials
```

**2.2 Network Configuration**
- VPC peering (if needed)
- Security group rules
- Private endpoint configuration

#### Phase 3: Data Export

**3.1 Export Script**
```python
# export_milvus_data.py
from pymilvus import connections, Collection
import json
import csv

def export_collection_data(collection_name: str, output_file: str):
    # Connect to source Milvus
    connections.connect(
        alias="source",
        host="source-milvus-host",
        port="19530"
    )
    
    collection = Collection(collection_name)
    collection.load()
    
    # Export all data
    results = collection.query(
        expr="id >= 0",  # Get all
        output_fields=["id", "question", "response", "combined_embedding", "related_nodes", "metadata"]
    )
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Exported {len(results)} records to {output_file}")
```

**3.2 Batch Export**
```bash
# Large collections için batch export
python export_milvus_data.py --collection medical_knowledge_base --batch-size 10000
```

#### Phase 4: Data Transformation (if needed)

**4.1 Schema Mapping**
```python
# Transform data if schema differs
def transform_data(source_data: dict) -> dict:
    return {
        "id": source_data["id"],
        "question": source_data["question"],
        "response": source_data["response"],
        "combined_embedding": source_data["combined_embedding"],
        "related_nodes": source_data.get("related_nodes", []),
        "metadata": source_data.get("metadata", {})
    }
```

#### Phase 5: Data Import

**5.1 Import Script**
```python
# import_milvus_data.py
from pymilvus import connections, Collection, utility
import json
from config import MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY

def import_collection_data(collection_name: str, data_file: str):
    # Connect to target Milvus (Huawei Cloud)
    connections.connect(
        alias="target",
        host=MILVUS_HOST,
        port=MILVUS_PORT,
        token=MILVUS_API_KEY,
        secure=True
    )
    
    # Create collection if not exists
    if not utility.has_collection(collection_name):
        # Create collection with schema (see schema section above)
        # ...
        pass
    
    collection = Collection(collection_name)
    collection.load()
    
    # Load data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    # Batch insert
    batch_size = 1000
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        collection.insert(batch)
        print(f"Inserted batch {i//batch_size + 1}")
    
    # Flush and create index
    collection.flush()
    # Create index...
    
    print(f"Import completed: {len(data)} records")
```

**5.2 Batch Import with Progress**
```bash
# Progress tracking ile import
python import_milvus_data.py --collection medical_knowledge_base --data exported_data.json --batch-size 1000
```

#### Phase 6: Index Recreation

**6.1 Index Creation**
```python
# create_indexes.py (update for Huawei Cloud)
from pymilvus import Collection, Index

collection = Collection("medical_knowledge_base")
collection.load()

# Create vector index
index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 1024}
}

collection.create_index(
    field_name="combined_embedding",
    index_params=index_params
)

print("Index created successfully")
```

#### Phase 7: Validation

**7.1 Data Validation**
```python
# validate_migration.py
def validate_migration():
    # Compare record counts
    source_count = get_source_count()
    target_count = get_target_count()
    
    assert source_count == target_count, "Record count mismatch"
    
    # Sample data validation
    sample_ids = get_random_sample(100)
    for id in sample_ids:
        source_data = get_source_data(id)
        target_data = get_target_data(id)
        assert source_data == target_data, f"Data mismatch for {id}"
    
    print("Validation passed!")
```

**7.2 Performance Testing**
```python
# Test query performance
def test_query_performance():
    query_embedding = generate_test_embedding()
    
    start_time = time.time()
    results = collection.search(
        data=[query_embedding],
        anns_field="combined_embedding",
        limit=10
    )
    latency = time.time() - start_time
    
    assert latency < 0.1, f"Query latency too high: {latency}s"
    print(f"Query latency: {latency}s")
```

#### Phase 8: Cutover

**8.1 Cutover Plan**
```yaml
Cutover Steps:
  1. Stop writes to source Milvus
  2. Final data sync (delta export/import)
  3. Update application config (.env) to point to Huawei Cloud Milvus
  4. Test application with new Milvus
  5. Monitor for 24 hours
  6. Decommission source Milvus
```

**8.2 Rollback Plan**
```yaml
Rollback Steps:
  1. Revert .env to source Milvus
  2. Restart application
  3. Investigate issues
  4. Fix and retry migration
```

### Migration Timeline

```
Week 1: Assessment and Planning
Week 2: Target Environment Setup
Week 3: Data Export and Transformation
Week 4: Data Import and Index Creation
Week 5: Validation and Testing
Week 6: Cutover and Monitoring
```

---

## 🚀 Deployment Adımları

### Step-by-Step Deployment Guide

#### 1. Infrastructure Setup

**1.1 VPC ve Network**
```bash
# Huawei Cloud Console'da:
1. Create VPC (10.0.0.0/16)
2. Create Public Subnet (10.0.1.0/24)
3. Create Private Subnet 1 (10.0.2.0/24)
4. Create Private Subnet 2 (10.0.3.0/24)
5. Create Internet Gateway
6. Create NAT Gateway (optional)
7. Configure Route Tables
8. Create Security Groups
```

**1.2 ECS Instances**
```bash
# Create ECS instances:
1. Launch ECS in Public Subnet
2. Attach Elastic IPs
3. Configure Security Groups
4. Install dependencies (see ECS section)
5. Deploy application
```

**1.3 ELB Setup**
```bash
# Create ELB:
1. Create Application Load Balancer
2. Configure HTTPS listener
3. Configure HTTP → HTTPS redirect
4. Create Target Group
5. Register ECS instances
6. Configure Health Checks
7. Upload SSL Certificate
```

#### 2. Database Setup

**2.1 Milvus Deployment**
```bash
# Option 1: Managed Milvus
1. Create Milvus instance in Huawei Cloud
2. Configure network (Private Subnet)
3. Get connection credentials
4. Update .env file

# Option 2: Self-managed
1. Launch ECS in Private Subnet
2. Install Docker
3. Deploy Milvus via docker-compose
4. Configure security groups
```

**2.2 Milvus Collection Setup**
```bash
# Run initialization script
python create_indexes.py
python build_graphrag.py  # If using GraphRAG
```

#### 3. Storage Setup

**3.1 OBS Bucket**
```bash
# Create OBS bucket:
1. Create bucket: medical-documents-prod
2. Configure access policies
3. Set up IAM roles
4. Test upload/download
```

#### 4. AI/ML Setup

**4.1 ModelArts Configuration**
```bash
# Configure ModelArts:
1. Create ModelArts endpoint
2. Deploy DeepSeek v3.1 model
3. Get API credentials
4. Update .env file
```

#### 5. Application Configuration

**5.1 Environment Variables**
```bash
# .env file on ECS instances
# Milvus
MILVUS_HOST=<huawei-cloud-milvus-endpoint>
MILVUS_PORT=19530
MILVUS_USE_CLOUD=true
MILVUS_API_KEY=<api-key>
MILVUS_COLLECTION_NAME=medical_knowledge_base

# OBS
OBS_ACCESS_KEY=<access-key>
OBS_SECRET_KEY=<secret-key>
OBS_ENDPOINT=obs.ap-southeast-1.myhuaweicloud.com
OBS_BUCKET_NAME=medical-documents-prod

# ModelArts
MODELARTS_ENDPOINT=https://modelarts.ap-southeast-1.myhuaweicloud.com
DEEPSEEK_API_KEY=<api-key>
MODELARTS_MODEL_NAME=deepseek-v3.1

# Application
LLM_MODEL=deepseek-v3.1
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
```

#### 6. Monitoring Setup

**6.1 Cloud Eye**
```bash
# Configure monitoring:
1. Create monitoring dashboard
2. Set up alerts
3. Configure notification channels
```

**6.2 Log Service**
```bash
# Configure logging:
1. Create log group
2. Configure log collection agents
3. Set up log queries
```

#### 7. Testing

**7.1 Health Checks**
```bash
# Test endpoints:
curl https://yourdomain.com/health
curl https://yourdomain.com/api/test
```

**7.2 Integration Tests**
```bash
# Run integration tests:
python test_connection.py
python test_rag.py
```

#### 8. Go Live

**8.1 DNS Update**
```bash
# Update DNS:
1. Point domain to ELB
2. Wait for DNS propagation
3. Test public access
```

**8.2 Final Checks**
```bash
# Verify:
1. Application accessible
2. Milvus queries working
3. OBS upload/download working
4. ModelArts API calls successful
5. Monitoring active
```

---

## 📊 Cost Estimation (Yaklaşık)

### Monthly Costs (USD)

```yaml
Infrastructure:
  ECS Instances (2x s6.xlarge.2): ~$150/month
  ELB: ~$20/month
  EIPs (3x): ~$15/month
  NAT Gateway: ~$35/month (if used)
  VPC: Free

Database:
  Managed Milvus (Medium): ~$200/month
  OR Self-managed Milvus ECS: ~$100/month

Storage:
  OBS Storage (100 GB): ~$2/month
  OBS Requests: ~$5/month

AI/ML:
  ModelArts API Calls: Pay-per-use (~$0.01-0.02 per 1K tokens)
  Estimated: ~$50-100/month (depending on usage)

Monitoring:
  Cloud Eye: Free tier + ~$10/month
  Log Service: ~$5/month

Total Estimated: ~$500-600/month (with managed Milvus)
                 ~$400-500/month (with self-managed Milvus)
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Milvus Connection Issues**
- Check security group rules
- Verify VPC peering (if using managed Milvus)
- Check API key validity
- Verify network connectivity

**2. OBS Access Denied**
- Check IAM policies
- Verify access keys
- Check bucket policies

**3. ModelArts API Errors**
- Verify API key
- Check endpoint URL
- Check rate limits
- Verify model availability

**4. ELB Health Check Failures**
- Check application health endpoint
- Verify security group rules
- Check ECS instance status
- Review application logs

---

## 📚 Additional Resources

- [Huawei Cloud ECS Documentation](https://support.huaweicloud.com/intl/en-us/productdesc-ecs/)
- [Huawei Cloud VPC Documentation](https://support.huaweicloud.com/intl/en-us/productdesc-vpc/)
- [Huawei Cloud OBS Documentation](https://support.huaweicloud.com/intl/en-us/productdesc-obs/)
- [Huawei Cloud ModelArts Documentation](https://support.huaweicloud.com/intl/en-us/productdesc-modelarts/)
- [Milvus Documentation](https://milvus.io/docs/)

---

**Son Güncelleme:** 2024  
**Dokümantasyon Versiyonu:** 1.0  
**Durum:** Production Ready

