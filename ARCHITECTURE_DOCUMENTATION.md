# 🏗️ Huawei Cloud AI Health Assistant - Backend Mimari Dokümantasyonu

## 📋 Genel Bakış

Bu dokümantasyon, Huawei Cloud AI Health Assistant uygulamasının **tam backend mimarisini** uçtan uca açıklamaktadır. Cloud mimarisi çizimi için gerekli tüm bileşenler, veri akışları ve servisler detaylı olarak belgelenmiştir.

---

## 🎯 Mimari Katmanları

### 1. **Kullanıcı Katmanı (User Layer)**
- **Bileşenler:**
  - Doktorlar ve tıp öğrencileri (kullanıcılar)
  - Web tarayıcıları (Streamlit UI)
  
- **Özellikler:**
  - Streamlit tabanlı web arayüzü
  - Chat-based etkileşim
  - Çoklu chat session yönetimi
  - Gerçek zamanlı yanıt gösterimi

---

### 2. **Load Balancer Katmanı (ELB - Elastic Load Balancer)**
- **Bileşenler:**
  - Huawei Cloud ELB (Elastic Load Balancer)
  - Health Check Endpoint (Port 8080)
  - SSL/TLS Termination (opsiyonel)

- **Özellikler:**
  - Trafik dağıtımı ve yük dengeleme
  - Health check monitoring (`/health` endpoint)
  - Auto-scaling desteği
  - SSL sertifikası yönetimi

- **Portlar:**
  - **8501**: Streamlit uygulaması
  - **8080**: Health check servisi (Flask)

- **Health Check Detayları:**
  ```python
  # health_check.py
  - Endpoint: GET /health
  - Response: {"status": "healthy", "service": "huaweict-health-assistant"}
  - Status Codes: 200 (healthy), 503 (unhealthy)
  ```

---

### 3. **Application Server Katmanı (ECS - Elastic Cloud Server)**

#### 3.1. **Ana Uygulama (app.py)**
- **Teknoloji:** Streamlit Framework
- **Port:** 8501
- **Özellikler:**
  - Chat UI yönetimi
  - Session state yönetimi
  - Kullanıcı etkileşimi koordinasyonu
  - RAG servisi entegrasyonu

- **Ana Fonksiyonlar:**
  - `generate_medical_response()`: Kullanıcı sorgusunu RAG servisine yönlendirir
  - Chat history yönetimi
  - GraphRAG metadata gösterimi
  - Source citation gösterimi

#### 3.2. **RAG Service (rag_service.py)** - CORE ORCHESTRATOR
- **Rol:** Tüm RAG pipeline'ını koordine eden ana servis
- **Bağımlılıklar:**
  - InputProcessor
  - AgenticOrchestrator
  - ContextIntegrator
  - ModelArtsClient
  - Embedding Model (HuggingFace)

- **İşlem Akışı:**
  ```
  1. Input Processing
     ↓
  2. Query Embedding Generation
     ↓
  3. Agentic Orchestration (opsiyonel) VEYA GraphRAG Retrieval
     ↓
  4. Context Integration
     ↓
  5. LLM Response Generation (ModelArts DeepSeek v3.1 veya Gemini)
     ↓
  6. Response Formatting & Metadata Extraction
  ```

- **Özellikler:**
  - Dual LLM desteği (ModelArts DeepSeek v3.1 → Gemini fallback)
  - GraphRAG ve Agentic RAG modları
  - Context enrichment
  - Source extraction ve citation

#### 3.3. **Input Processing (input_processing.py)**
- **Rol:** Kullanıcı girdisini temizleme ve ön işleme
- **Fonksiyonlar:**
  - Text cleaning ve normalization
  - Medical keyword extraction
  - Entity recognition (temel)
  - Input type classification (question, diagnostic_query, treatment_query, symptom_description)
  - Urgency detection

- **Çıktı Formatı:**
  ```python
  {
    "original_text": "...",
    "processed_text": "...",
    "medical_context": {
      "medical_keywords": [...],
      "is_urgent": bool,
      "is_question": bool,
      "has_medical_context": bool
    },
    "input_type": "diagnostic_query",
    "entities": [...],
    "length": int,
    "word_count": int
  }
  ```

#### 3.4. **Agentic Orchestrator (agentic_orchestrator.py)**
- **Rol:** Görev planlama ve agentic reasoning koordinasyonu
- **Task Types:**
  - `SIMPLE_RETRIEVAL`: Basit vektör araması
  - `GRAPH_RAG`: Graph traversal gerektiren sorgular
  - `MULTI_STEP_REASONING`: Çok adımlı akıl yürütme
  - `COMPARATIVE_ANALYSIS`: Karşılaştırmalı analiz

- **Özellikler:**
  - Task type determination
  - Execution plan creation
  - Multi-iteration reasoning
  - LLM-based decision making
  - Reasoning trace logging

- **Execution Flow:**
  ```
  1. Plan Task (determine task type)
     ↓
  2. Create Execution Steps
     ↓
  3. Execute with Reasoning (iterative)
     ↓
  4. Agentic Decision Making (continue/stop)
     ↓
  5. Final Context Assembly
  ```

#### 3.5. **Context Integration (context_integration.py)**
- **Rol:** Milvus ve RDS'den context retrieval ve entegrasyonu
- **Özellikler:**
  - GraphRAG retrieval (PRIMARY METHOD)
  - Vector similarity search
  - Graph traversal (max_depth configurable)
  - RDS metadata enrichment
  - Context merging ve ranking

- **GraphRAG Retrieval Process:**
  ```
  1. Initial Vector Search (top_k Q&A pairs)
     ↓
  2. Extract Initial Nodes
     ↓
  3. Graph Traversal (BFS-like, max_depth)
     ↓
  4. Related Nodes Discovery
     ↓
  5. Context String Building
     ↓
  6. RDS Metadata Enrichment (optional)
  ```

- **Milvus Collection Schema:**
  ```python
  Fields:
  - id (VARCHAR, Primary Key)
  - question (VARCHAR, max 5000)
  - response (VARCHAR, max 10000)
  - question_embedding (FLOAT_VECTOR, dim=768)
  - response_embedding (FLOAT_VECTOR, dim=768)
  - combined_embedding (FLOAT_VECTOR, dim=768)  # Primary search field
  - metadata (JSON)
  - related_nodes (JSON)  # Graph edges
  ```

#### 3.6. **ModelArts Client (modelarts_client.py)**
- **Rol:** Huawei Cloud ModelArts API entegrasyonu
- **Model:** DeepSeek v3.1
- **API Format:**
  - Endpoint: `{MODELARTS_ENDPOINT}/v1/chat/completions`
  - Method: POST
  - Headers: `X-Auth-Token: {DEEPSEEK_API_KEY}`
  - Payload: OpenAI-compatible format

- **Özellikler:**
  - Temperature control
  - Max tokens limit
  - System prompt support
  - Error handling ve fallback

#### 3.7. **Embedding Model**
- **Model:** `sentence-transformers/all-mpnet-base-v2`
- **Dimension:** 768
- **Device:** Auto-detect (CUDA/CPU)
- **Kullanım:** Query embedding generation

---

### 4. **Intelligence Layer (ModelArts)**

#### 4.1. **LLM Servisi**
- **Primary Model:** DeepSeek v3.1 (Huawei ModelArts)
- **Fallback Model:** Google Gemini 2.5 Flash
- **Acceleration:** Ascend Chips (Huawei AI chips)

- **Model Selection Logic:**
  ```
  IF ModelArts DeepSeek v3.1 available AND configured:
    → Use ModelArts DeepSeek v3.1
  ELSE IF Gemini API key available:
    → Use Google Gemini 2.5 Flash
  ELSE:
    → Return error
  ```

- **Prompt Template:**
  - Medical assistant role
  - Structured response format (3 paragraphs):
    1. Diagnosis
    2. Clinical Reasoning
    3. Interpretation
  - Content guidelines ve safety checks

---

### 5. **Data & Memory Layer**

#### 5.1. **Milvus Vector & Graph Database**
- **Rol:** Vector ve graph database (hybrid storage)
- **Deployment:** Milvus Cloud (Zilliz Cloud) veya Self-hosted
- **Connection:**
  - Host: `MILVUS_HOST` (cloud endpoint)
  - Port: 443 (HTTPS) veya 19530
  - Authentication: API Key (`MILVUS_API_KEY`) veya Username/Password

- **Collection Structure:**
  - **Name:** `medical_knowledge_base`
  - **Schema:** Q&A pairs with embeddings ve graph relationships
  - **Indexes:** IVF_FLAT indexes on all vector fields (COSINE similarity)

- **GraphRAG Structure:**
  - **Nodes:** Q&A pairs (her pair bir node)
  - **Edges:** Semantic similarity relationships (`related_nodes` field)
  - **Traversal:** BFS-like graph traversal (max_depth configurable)

- **Data Flow:**
  ```
  Dataset (HuggingFace) 
    → GraphRAG Builder 
    → Embedding Generation 
    → Similarity Graph Building 
    → Milvus Storage
  ```

#### 5.2. **RDS (Relational Database Service)**
- **Rol:** Metadata, relations, ve analytics storage
- **Engine:** PostgreSQL veya MySQL (configurable)
- **Tables:**
  - `medical_qa_metadata`: Q&A metadata (category, source, author, etc.)
  - `medical_qa_relations`: Explicit relations between Q&A pairs
  - `query_logs`: User query logging ve analytics
  - `document_sources`: Source document tracking
  - `analytics`: Performance metrics

- **Özellikler:**
  - Metadata enrichment for Milvus results
  - Query logging ve analytics
  - Source tracking
  - Performance monitoring

- **Connection:**
  - Host: `RDS_HOST`
  - Port: 5432 (PostgreSQL) veya 3306 (MySQL)
  - Database: `medical_db`
  - Authentication: Username/Password

#### 5.3. **OBS (Object Storage Service)**
- **Rol:** Büyük dokümanlar için object storage
- **Özellikler:**
  - Document upload/download
  - Temporary URL generation
  - Bucket management
  - Document listing ve filtering

- **Kullanım Senaryoları:**
  - Raw medical documents storage
  - PDF/Image storage
  - Dataset files
  - Backup storage

- **Connection:**
  - Endpoint: `OBS_ENDPOINT`
  - Bucket: `OBS_BUCKET_NAME`
  - Authentication: Access Key / Secret Key

---

## 🔄 Veri Akışı (End-to-End Flow)

### Senaryo 1: Basit Tıbbi Sorgu (GraphRAG Mode)

```
1. User Input
   ↓
2. ELB (Load Balancer)
   ↓
3. ECS - Streamlit App (app.py)
   ↓
4. RAG Service (rag_service.py)
   ├─→ Input Processing (preprocess, extract metadata)
   ├─→ Embedding Generation (HuggingFace model)
   ↓
5. Context Integration (context_integration.py)
   ├─→ Milvus Vector Search (top_k=5)
   ├─→ Graph Traversal (max_depth=2)
   ├─→ RDS Metadata Enrichment (optional)
   ↓
6. Context Assembly
   ↓
7. LLM Generation
   ├─→ Try ModelArts DeepSeek v3.1
   └─→ Fallback to Gemini if failed
   ↓
8. Response Formatting
   ├─→ Extract sources
   ├─→ Add GraphRAG metadata
   └─→ Format for UI
   ↓
9. Streamlit UI Display
   ↓
10. User sees response with sources
```

### Senaryo 2: Kompleks Sorgu (Agentic RAG Mode)

```
1. User Input
   ↓
2. RAG Service
   ├─→ Input Processing
   ├─→ Embedding Generation
   ↓
3. Agentic Orchestrator
   ├─→ Task Type Determination
   ├─→ Execution Plan Creation
   ├─→ Multi-iteration Reasoning:
   │   ├─→ Step 1: Initial Retrieval
   │   ├─→ Step 2: Agentic Reasoning (LLM)
   │   ├─→ Step 3: Refined Retrieval
   │   └─→ Step 4: Context Integration
   ↓
4. Final Context Assembly
   ↓
5. LLM Generation
   ↓
6. Response with Execution Trace
```

---

## 🔌 Servis Bağlantıları ve Portlar

### ECS Instance İçinde:
- **Port 8501:** Streamlit uygulaması
- **Port 8080:** Health check servisi (Flask)

### Dış Servisler:
- **Milvus:** `MILVUS_HOST:MILVUS_PORT` (443 veya 19530)
- **RDS:** `RDS_HOST:RDS_PORT` (5432 veya 3306)
- **OBS:** `OBS_ENDPOINT` (HTTPS)
- **ModelArts:** `MODELARTS_ENDPOINT` (HTTPS)
- **Google Gemini API:** `generativelanguage.googleapis.com` (HTTPS)

---

## 📊 Veri Yapıları

### Milvus Collection Schema:
```python
{
  "id": "qa_123",  # VARCHAR, Primary Key
  "question": "What causes headaches?",  # VARCHAR(5000)
  "response": "Headaches can be caused by...",  # VARCHAR(10000)
  "question_embedding": [0.123, 0.456, ...],  # FLOAT_VECTOR(768)
  "response_embedding": [0.789, 0.012, ...],  # FLOAT_VECTOR(768)
  "combined_embedding": [0.234, 0.567, ...],  # FLOAT_VECTOR(768) - PRIMARY SEARCH FIELD
  "metadata": {
    "dataset_index": 123,
    "source": "FreedomIntelligence/medical-o1-reasoning-SFT"
  },
  "related_nodes": ["qa_124", "qa_125", ...]  # JSON array - Graph edges
}
```

### RDS Tables:

**medical_qa_metadata:**
```sql
- id (VARCHAR, PK)
- category (VARCHAR)
- subcategory (VARCHAR)
- source (VARCHAR)
- source_type (VARCHAR)
- author (VARCHAR)
- publication_date (DATE)
- tags (JSON/ARRAY)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

**medical_qa_relations:**
```sql
- source_id (VARCHAR, FK)
- target_id (VARCHAR, FK)
- relation_type (VARCHAR)
- confidence (FLOAT)
- created_at (TIMESTAMP)
```

**query_logs:**
```sql
- id (SERIAL, PK)
- qa_id (VARCHAR, FK)
- query_text (TEXT)
- response_text (TEXT)
- user_id (VARCHAR)
- session_id (VARCHAR)
- response_time (FLOAT)
- similarity_score (FLOAT)
- user_feedback (VARCHAR)
- created_at (TIMESTAMP)
```

---

## 🔐 Güvenlik ve Kimlik Doğrulama

### API Keys ve Credentials:
- **Google API Key:** `GOOGLE_API_KEY` (Gemini için)
- **DeepSeek API Key:** `DEEPSEEK_API_KEY` (ModelArts için)
- **Milvus API Key:** `MILVUS_API_KEY` (Milvus Cloud için)
- **OBS Access Key/Secret:** `OBS_ACCESS_KEY`, `OBS_SECRET_KEY`
- **RDS Credentials:** `RDS_USER`, `RDS_PASSWORD`

### Network Security:
- VPC isolation
- Security groups
- HTTPS for external APIs
- Private endpoints (where possible)

---

## ⚙️ Konfigürasyon Parametreleri

### RAG Configuration:
- `RETRIEVAL_TOP_K`: 5 (default)
- `RETRIEVAL_SCORE_THRESHOLD`: 0.7
- `GRAPH_RAG_ENABLED`: true
- `GRAPH_MAX_DEPTH`: 2
- `GRAPH_SIMILARITY_THRESHOLD`: 0.7

### Agentic RAG Configuration:
- `AGENTIC_RAG_ENABLED`: true
- `AGENT_MAX_ITERATIONS`: 5
- `AGENT_REASONING_ENABLED`: true

### LLM Configuration:
- `LLM_MODEL`: "deepseek-v3.1" veya "gemini-2.5-flash"
- `LLM_TEMPERATURE`: 0.2
- `LLM_MAX_TOKENS`: 2048

### Embedding Configuration:
- `EMBEDDING_MODEL_NAME`: "sentence-transformers/all-mpnet-base-v2"
- `EMBEDDING_DIMENSION`: 768
- `EMBEDDING_DEVICE`: "auto" (cuda/cpu/auto)

---

## 🚀 Deployment Mimarisi

### ECS Instance:
- **OS:** Ubuntu 22.04
- **Instance Type:** s6.medium.2 veya daha yüksek
- **Services:**
  - `huaweict-streamlit.service` (systemd)
  - `huaweict-health.service` (systemd)

### ELB Configuration:
- **Health Check:** `GET /health` on port 8080
- **Backend:** ECS instance(s)
- **Port Mapping:** 8501 → 8501

### Auto-scaling:
- ELB-based load balancing
- Health check-based instance management
- Future: ECS auto-scaling groups

---

## 📈 Performance Optimizations

1. **Caching:**
   - RAG service cached with `@st.cache_resource`
   - Embedding model cached

2. **Batch Processing:**
   - GPU-accelerated embedding generation
   - Batch similarity computation

3. **Indexing:**
   - Milvus IVF_FLAT indexes
   - Multiple vector field indexes

4. **Connection Pooling:**
   - RDS connection reuse
   - Milvus connection persistence

---

## 🔍 Monitoring ve Logging

### Health Checks:
- Application health: `/health` endpoint
- Service status: systemd service status
- Connection checks: Milvus, RDS, OBS

### Logging:
- Python logging module
- Log levels: INFO, WARNING, ERROR
- Structured logging for debugging

### Analytics:
- Query logging in RDS
- Performance metrics
- User feedback tracking

---

## 🎨 Cloud Mimari Diyagramı İçin Notlar

### Katmanlar (Layers):
1. **User Layer** (En üst)
2. **ELB Layer** (Load Balancer)
3. **Application Layer** (ECS - Streamlit + Services)
4. **Intelligence Layer** (ModelArts)
5. **Data Layer** (Milvus + RDS + OBS)

### Bağlantılar:
- User → ELB (HTTPS)
- ELB → ECS (HTTP/HTTPS)
- ECS → ModelArts (HTTPS API)
- ECS → Milvus (HTTPS/TCP)
- ECS → RDS (TCP - PostgreSQL/MySQL)
- ECS → OBS (HTTPS API)
- ECS → Google Gemini API (HTTPS)

### Veri Akışı:
- Request: User → ELB → ECS → Services → External APIs
- Response: External APIs → Services → ECS → ELB → User

---

## 📝 Önemli Notlar

1. **Dual LLM Strategy:** ModelArts DeepSeek v3.1 primary, Gemini fallback
2. **GraphRAG Primary:** GraphRAG retrieval ana yöntem, vector search ikincil
3. **Hybrid Storage:** Milvus (vector+graph) + RDS (relational metadata)
4. **Agentic Capability:** Opsiyonel agentic reasoning modu
5. **Cloud-Native:** Tüm servisler Huawei Cloud üzerinde

---

**Son Güncelleme:** 2024
**Versiyon:** 1.0
**Hazırlayan:** AI Assistant
