# Environment Variables Template

Bu dosya `.env` dosyası için tüm gerekli environment variable'ları içerir.

## Kullanım

```bash
# .env dosyasını oluştur
cp ENV_TEMPLATE.md .env

# Sonra .env dosyasını düzenle ve gerçek değerlerinizi girin
```

---

## Tam .env Template

```env
# ============================================
# Huawei Cloud AI Health Assistant
# Environment Variables Configuration
# ============================================

# ============================================
# API Keys
# ============================================
# Google Gemini API Key (fallback LLM)
GOOGLE_API_KEY=your_google_api_key_here

# ============================================
# DeepSeek v3.1 API Configuration
# ============================================
# DeepSeek API Key (required for DeepSeek v3.1)
# Get your API key from: https://platform.deepseek.com/api_keys
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# DeepSeek API Base URL (default: https://api.deepseek.com)
# Use this for direct DeepSeek API access
DEEPSEEK_API_BASE=https://api.deepseek.com

# DeepSeek Model Name
# Options: "deepseek-chat" (default) or "deepseek-v3.1"
DEEPSEEK_MODEL_NAME=deepseek-chat

# Use Direct DeepSeek API instead of Huawei ModelArts
# Set to "true" to use direct DeepSeek API (https://api.deepseek.com)
# Set to "false" to use Huawei ModelArts endpoint
DEEPSEEK_USE_DIRECT_API=false

# ============================================
# Milvus Vector Database Configuration
# ============================================
# For Milvus Cloud (Zilliz Cloud) or Huawei Cloud Milvus
MILVUS_USE_CLOUD=true
MILVUS_HOST=your_milvus_host_here
# Port: 443 for serverless/cloud, 19530 for standard
MILVUS_PORT=443
MILVUS_API_KEY=your_milvus_api_key_here
# Optional: Username/Password (if not using API key)
MILVUS_USER=
MILVUS_PASSWORD=
MILVUS_COLLECTION_NAME=medical_knowledge_base

# ============================================
# RDS (Relational Database) Configuration
# ============================================
# Huawei Cloud RDS (PostgreSQL or MySQL)
RDS_HOST=rds-xxx.huaweicloud.com
RDS_PORT=5432
RDS_DB=medical_db
RDS_USER=admin
RDS_PASSWORD=your_rds_password_here
RDS_ENGINE=postgresql
# Options: postgresql or mysql

# ============================================
# OBS (Object Storage Service) Configuration
# ============================================
# Huawei Cloud OBS credentials
OBS_ACCESS_KEY=your_obs_access_key_here
OBS_SECRET_KEY=your_obs_secret_key_here
# OBS endpoint format: obs.{region}.myhuaweicloud.com
OBS_ENDPOINT=obs.ap-southeast-1.myhuaweicloud.com
OBS_BUCKET_NAME=medical-documents-prod

# ============================================
# ModelArts Configuration (Huawei Cloud)
# ============================================
# Huawei Cloud ModelArts endpoint for DeepSeek v3.1
# Only required if DEEPSEEK_USE_DIRECT_API=false
MODELARTS_ENDPOINT=https://modelarts.ap-southeast-1.myhuaweicloud.com
MODELARTS_PROJECT_ID=your_project_id_here
MODELARTS_MODEL_NAME=deepseek-v3.1

# ============================================
# Embedding Model Configuration
# ============================================
# Using all-mpnet-base-v2 for better medical text understanding (768 dimensions)
# Alternative: "sentence-transformers/all-MiniLM-L6-v2" (384 dimensions, faster)
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
# GPU Configuration: 'cuda' for GPU, 'cpu' for CPU, 'auto' to auto-detect
EMBEDDING_DEVICE=auto

# ============================================
# LLM Configuration
# ============================================
# LLM Model: "gemini-2.5-flash" or "deepseek-chat" or "deepseek-v3.1"
# Note: If using direct DeepSeek API, model name should match DEEPSEEK_MODEL_NAME
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048

# ============================================
# RAG Configuration
# ============================================
RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=0.7

# ============================================
# GraphRAG Configuration
# ============================================
GRAPH_RAG_ENABLED=true
GRAPH_MAX_NODES=10
GRAPH_MAX_DEPTH=2
GRAPH_SIMILARITY_THRESHOLD=0.7

# ============================================
# Agentic RAG Configuration
# ============================================
AGENTIC_RAG_ENABLED=true
AGENT_MAX_ITERATIONS=5
AGENT_REASONING_ENABLED=true

# ============================================
# Application Configuration
# ============================================
VECTORSTORE_DIR=./medical_vectorstore
LOG_LEVEL=INFO

# ============================================
# Sync Configuration (for Milvus-RDS sync)
# ============================================
SYNC_ENABLED=true
SYNC_INTERVAL=300
```

---

## Önemli Notlar

1. **RDS Opsiyonel:** RDS kullanmıyorsanız, RDS_* değişkenlerini boş bırakabilirsiniz
2. **Milvus Zorunlu:** Milvus configuration mutlaka doldurulmalı
3. **API Keys:** En az bir LLM API key'i gerekli (ModelArts veya Gemini)
4. **OBS Opsiyonel:** OBS kullanmıyorsanız boş bırakabilirsiniz

