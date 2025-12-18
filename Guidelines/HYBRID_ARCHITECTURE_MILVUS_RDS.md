# 🏗️ Hibrit Mimari: Milvus + RDS Uçtan Uca Mimari Dokümantasyonu

**Proje:** Huawei Cloud AI Health Assistant  
**Mimari:** Hybrid Architecture (Milvus Vector DB + RDS Relational DB)  
**Durum:** Production Ready

---

## 📋 İçindekiler

1. [Genel Mimari Genel Bakış](#genel-mimari-genel-bakış)
2. [Veri Katmanı Stratejisi](#veri-katmanı-stratejisi)
3. [Milvus Vector Database](#milvus-vector-database)
4. [RDS Relational Database](#rds-relational-database)
5. [Veri Akışı ve Senkronizasyon](#veri-akışı-ve-senkronizasyon)
6. [Export ve Backup Stratejileri](#export-ve-backup-stratejileri)
7. [Uçtan Uca Veri Akışı](#uçtan-uca-veri-akışı)
8. [Deployment ve Yapılandırma](#deployment-ve-yapılandırma)

---

## 🎯 Genel Mimari Genel Bakış

### Hibrit Veritabanı Mimarisi

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Streamlit App (ECS)                                             │  │
│  │  • RAG Service                                                   │  │
│  │  • Query Processing                                              │  │
│  │  • Response Generation                                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Context Integrator                                               │  │
│  │  • Milvus Client (Vector Search)                                 │  │
│  │  • RDS Client (Metadata & Relations)                              │  │
│  │  • Data Synchronization Service                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────────────┐      ┌───────────────────────────┐
│   MILVUS VECTOR DB        │      │   RDS RELATIONAL DB       │
│  ┌─────────────────────┐  │      │  ┌─────────────────────┐ │
│  │ Vector Embeddings   │  │      │  │ Metadata            │ │
│  │ • question_embedding│  │      │  │ • Categories        │ │
│  │ • response_embedding│  │      │  │ • Sources           │ │
│  │ • combined_embedding│  │      │  │ • Timestamps         │ │
│  └─────────────────────┘  │      │  │ • User interactions │ │
│  ┌─────────────────────┐  │      │  └─────────────────────┘ │
│  │ Q&A Pairs           │  │      │  ┌─────────────────────┐ │
│  │ • question          │  │      │  │ Relations           │ │
│  │ • response          │  │      │  │ • Document links    │ │
│  │ • id                │  │      │  │ • Entity relations  │ │
│  └─────────────────────┘  │      │  │ • Graph edges        │ │
│  ┌─────────────────────┐  │      │  └─────────────────────┘ │
│  │ Graph Structure     │  │      │  ┌─────────────────────┐ │
│  │ • related_nodes     │  │      │  │ Analytics           │ │
│  │ • similarity scores │  │      │  │ • Query logs        │ │
│  └─────────────────────┘  │      │  │ • Usage stats       │ │
└───────────────────────────┘      │  │ • Performance       │ │
                                   │  └─────────────────────┘ │
                                   └───────────────────────────┘
```

---

## 📊 Veri Katmanı Stratejisi

### Veri Bölümleme (Data Partitioning)

**Milvus'ta Saklananlar:**
- ✅ Vector embeddings (question, response, combined)
- ✅ Q&A pair metinleri (question, response)
- ✅ Graph relationships (related_nodes)
- ✅ Temel metadata (JSON formatında)

**RDS'de Saklananlar:**
- ✅ Detaylı metadata (structured)
- ✅ Kategoriler ve etiketler
- ✅ Kaynak bilgileri (source documents)
- ✅ Kullanıcı etkileşimleri (query logs)
- ✅ İstatistikler ve analitikler
- ✅ İlişkiler ve referanslar
- ✅ Timestamps ve audit logs

### Veri İlişkisi

```
Milvus Record (id: "abc123")
    │
    ├──> RDS: medical_qa_metadata (id: "abc123")
    │         • category: "Cardiology"
    │         • source: "Textbook"
    │         • author: "Dr. Smith"
    │         • created_at: "2024-01-01"
    │
    ├──> RDS: medical_qa_relations (source_id: "abc123")
    │         • target_id: "def456"
    │         • relation_type: "symptom_of"
    │         • confidence: 0.85
    │
    └──> RDS: query_logs (qa_id: "abc123")
            • query_text: "What is hypertension?"
            • response_time: 1.2s
            • user_feedback: "helpful"
```

---

## 🗄️ Milvus Vector Database

### Milvus Collection Schema

```python
Collection: medical_knowledge_base

Fields:
  - id (VARCHAR, PRIMARY KEY)
  - question (VARCHAR, max_length=5000)
  - response (VARCHAR, max_length=10000)
  - question_embedding (FLOAT_VECTOR, dim=768)
  - response_embedding (FLOAT_VECTOR, dim=768)
  - combined_embedding (FLOAT_VECTOR, dim=768)
  - metadata (JSON) - Minimal metadata
  - related_nodes (JSON) - Graph relationships
```

### Milvus Kullanım Senaryoları

**1. Vector Similarity Search:**
```python
# Query embedding ile benzer Q&A'ları bul
results = collection.search(
    data=[query_embedding],
    anns_field="combined_embedding",
    limit=10
)
```

**2. Graph Traversal:**
```python
# Related nodes üzerinden graph traversal
related_ids = record["related_nodes"]
related_records = collection.query(
    expr=f"id in {related_ids}",
    output_fields=["question", "response"]
)
```

**3. Hybrid Search:**
```python
# Vector search + metadata filtering
results = collection.search(
    data=[query_embedding],
    anns_field="combined_embedding",
    expr='metadata["category"] == "Cardiology"',
    limit=10
)
```

---

## 🗃️ RDS Relational Database

### RDS Schema Tasarımı

#### 1. medical_qa_metadata Table

```sql
CREATE TABLE medical_qa_metadata (
    id VARCHAR(100) PRIMARY KEY,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    source VARCHAR(255),
    source_type VARCHAR(50), -- 'textbook', 'journal', 'clinical_guideline'
    author VARCHAR(255),
    publication_date DATE,
    language VARCHAR(10) DEFAULT 'en',
    difficulty_level VARCHAR(20), -- 'beginner', 'intermediate', 'advanced'
    tags TEXT[], -- Array of tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id) REFERENCES milvus_reference(id)
);

CREATE INDEX idx_category ON medical_qa_metadata(category);
CREATE INDEX idx_source ON medical_qa_metadata(source);
CREATE INDEX idx_tags ON medical_qa_metadata USING GIN(tags);
```

#### 2. medical_qa_relations Table

```sql
CREATE TABLE medical_qa_relations (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) NOT NULL,
    target_id VARCHAR(100) NOT NULL,
    relation_type VARCHAR(50), -- 'symptom_of', 'treatment_for', 'related_to'
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES medical_qa_metadata(id),
    FOREIGN KEY (target_id) REFERENCES medical_qa_metadata(id),
    UNIQUE(source_id, target_id, relation_type)
);

CREATE INDEX idx_source_relation ON medical_qa_relations(source_id);
CREATE INDEX idx_target_relation ON medical_qa_relations(target_id);
CREATE INDEX idx_relation_type ON medical_qa_relations(relation_type);
```

#### 3. query_logs Table

```sql
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    qa_id VARCHAR(100),
    query_text TEXT NOT NULL,
    response_text TEXT,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    response_time FLOAT, -- seconds
    similarity_score FLOAT,
    user_feedback VARCHAR(20), -- 'helpful', 'not_helpful', 'neutral'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qa_id) REFERENCES medical_qa_metadata(id)
);

CREATE INDEX idx_qa_logs ON query_logs(qa_id);
CREATE INDEX idx_user_logs ON query_logs(user_id);
CREATE INDEX idx_created_logs ON query_logs(created_at);
```

#### 4. document_sources Table

```sql
CREATE TABLE document_sources (
    id SERIAL PRIMARY KEY,
    qa_id VARCHAR(100) NOT NULL,
    document_name VARCHAR(255),
    document_path VARCHAR(500), -- OBS path
    page_number INTEGER,
    section VARCHAR(255),
    excerpt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qa_id) REFERENCES medical_qa_metadata(id)
);

CREATE INDEX idx_doc_qa ON document_sources(qa_id);
```

#### 5. analytics Table

```sql
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    qa_id VARCHAR(100),
    date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qa_id) REFERENCES medical_qa_metadata(id)
);

CREATE INDEX idx_metric ON analytics(metric_name, date);
```

---

## 🔄 Veri Akışı ve Senkronizasyon

### 1. Veri Ekleme Akışı

```
┌─────────────────────────────────────────────────────────────┐
│  New Q&A Pair Insertion                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────┐                  ┌──────────────────┐
│  1. Milvus       │                  │  2. RDS           │
│  Insert          │                  │  Insert          │
│  • Embeddings    │                  │  • Metadata       │
│  • Q&A text      │                  │  • Relations      │
│  • Graph nodes   │                  │  • Sources        │
└──────────────────┘                  └──────────────────┘
        │                                       │
        └───────────────────┬───────────────────┘
                            │
                            ▼
                ┌───────────────────┐
                │ 3. Sync Service   │
                │ • Verify sync     │
                │ • Handle conflicts│
                └───────────────────┘
```

### 2. Veri Okuma Akışı

```
┌─────────────────────────────────────────────────────────────┐
│  User Query                                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────┐
                │ 1. Generate       │
                │    Query Embedding│
                └─────────┬─────────┘
                          │
                          ▼
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│ 2a. Milvus       │              │ 2b. RDS           │
│ Vector Search    │              │ Metadata Query    │
│ • Find similar   │              │ • Filter by       │
│   Q&A pairs      │              │   category        │
│ • Get top K      │              │ • Get relations   │
└────────┬─────────┘              │ • Get sources     │
         │                        └────────┬──────────┘
         │                                 │
         └─────────────┬───────────────────┘
                       │
                       ▼
            ┌───────────────────┐
            │ 3. Merge Results  │
            │ • Combine vector  │
            │   and metadata    │
            │ • Rank by         │
            │   relevance       │
            └─────────┬─────────┘
                      │
                      ▼
            ┌───────────────────┐
            │ 4. Generate       │
            │    Response       │
            └───────────────────┘
```

### 3. Senkronizasyon Stratejisi

**Real-time Sync (Önerilen):**
```python
# Her insert'te hem Milvus hem RDS'e yaz
def insert_qa_pair(question, response, metadata):
    # 1. Generate embeddings
    embeddings = generate_embeddings(question, response)
    
    # 2. Insert to Milvus
    milvus_id = insert_to_milvus(question, response, embeddings)
    
    # 3. Insert to RDS (transactional)
    with rds_transaction():
        insert_metadata(milvus_id, metadata)
        insert_relations(milvus_id, relations)
        insert_sources(milvus_id, sources)
    
    # 4. Verify sync
    verify_sync(milvus_id)
```

**Batch Sync (Büyük veri setleri için):**
```python
# Batch'ler halinde sync
def batch_sync():
    # 1. Get unsynced records from Milvus
    unsynced = get_unsynced_milvus_records()
    
    # 2. Batch insert to RDS
    for batch in chunks(unsynced, 100):
        insert_batch_to_rds(batch)
        mark_as_synced(batch)
```

---

## 📤 Export ve Backup Stratejileri

### 1. Milvus'tan Export

**CSV Export:**
```bash
python export_from_milvus.py \
  --format csv \
  --output backup/milvus_export_20241217.csv \
  --batch-size 1000
```

**JSON Export:**
```bash
python export_from_milvus.py \
  --format json \
  --output backup/milvus_export_20241217.json \
  --include-embeddings
```

**SQL Export (RDS'e):**
```bash
python export_from_milvus.py \
  --format sql \
  --output "postgresql://user:pass@rds-endpoint:5432/medical_db" \
  --table-name milvus_backup \
  --batch-size 500
```

**Excel Export:**
```bash
python export_from_milvus.py \
  --format excel \
  --output backup/milvus_export_20241217.xlsx
```

### 2. RDS Backup Stratejileri

**Automated Daily Backup:**
```sql
-- PostgreSQL pg_dump
pg_dump -h rds-endpoint -U user -d medical_db \
  -F c -f backup/rds_backup_$(date +%Y%m%d).dump

-- MySQL mysqldump
mysqldump -h rds-endpoint -u user -p medical_db \
  > backup/rds_backup_$(date +%Y%m%d).sql
```

**Huawei Cloud RDS Automated Backup:**
- RDS Console → Backup Management
- Enable automated daily backups
- Retention: 7-30 days
- Backup window: Low traffic hours

### 3. Combined Backup Strategy

```bash
#!/bin/bash
# Full backup script: Milvus + RDS

BACKUP_DIR="backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 1. Export Milvus
echo "Exporting Milvus..."
python export_from_milvus.py \
  --format json \
  --output $BACKUP_DIR/milvus_backup.json \
  --include-embeddings

# 2. Backup RDS
echo "Backing up RDS..."
pg_dump -h $RDS_HOST -U $RDS_USER -d $RDS_DB \
  -F c -f $BACKUP_DIR/rds_backup.dump

# 3. Upload to OBS
echo "Uploading to OBS..."
obsutil cp $BACKUP_DIR obs://backup-bucket/backups/$(date +%Y%m%d)/

echo "✅ Backup completed!"
```

---

## 🔄 Uçtan Uca Veri Akışı

### Senaryo 1: Yeni Veri Ekleme

```
1. User/Admin uploads medical document
   │
   ▼
2. Document Processing Service
   • Extract Q&A pairs
   • Generate embeddings
   • Extract metadata
   │
   ▼
3. Parallel Insertion
   ├──> Milvus Insert
   │    • question, response
   │    • embeddings (3 types)
   │    • related_nodes (empty initially)
   │    • basic metadata (JSON)
   │
   └──> RDS Insert (Transaction)
        • medical_qa_metadata
        • medical_qa_relations
        • document_sources
        • analytics (initial stats)
   │
   ▼
4. Graph Relationship Building
   • Calculate similarities
   • Update related_nodes in Milvus
   • Insert relations in RDS
   │
   ▼
5. Verification
   • Check sync status
   • Validate data integrity
   • Update indexes
```

### Senaryo 2: Query Processing

```
1. User submits query
   "What are the symptoms of hypertension?"
   │
   ▼
2. Query Processing
   • Generate query embedding
   • Extract keywords
   • Determine intent
   │
   ▼
3. Parallel Search
   ├──> Milvus Vector Search
   │    • Find similar Q&A pairs
   │    • Get top 10 results
   │    • Return: ids, questions, responses, similarities
   │
   └──> RDS Metadata Filter
        • Filter by category (if specified)
        • Get relations
        • Get sources
        • Get usage stats
   │
   ▼
4. Result Merging
   • Combine vector results with metadata
   • Apply filters from RDS
   • Re-rank by combined relevance
   • Enrich with RDS metadata
   │
   ▼
5. Graph Traversal (GraphRAG)
   • Get related_nodes from Milvus
   • Get relation details from RDS
   • Traverse graph
   • Build context
   │
   ▼
6. Response Generation
   • LLM generates response
   • Include sources from RDS
   • Include metadata
   │
   ▼
7. Logging
   • Log query to RDS query_logs
   • Update analytics
   • Track user feedback
```

### Senaryo 3: Veri Güncelleme

```
1. Admin updates Q&A pair
   │
   ▼
2. Update Milvus
   • Update question/response text
   • Regenerate embeddings
   • Update related_nodes
   │
   ▼
3. Update RDS
   • Update metadata
   • Update relations
   • Update timestamps
   │
   ▼
4. Invalidate Cache
   • Clear related caches
   • Rebuild indexes if needed
```

---

## 🏗️ Deployment ve Yapılandırma

### 1. RDS Instance Yapılandırması

**Huawei Cloud RDS PostgreSQL:**
```yaml
RDS Configuration:
  Engine: PostgreSQL 14+
  Instance Type: rds.pg.n1.large.2
    - vCPU: 2
    - RAM: 4 GB
    - Storage: 100 GB SSD
  
  High Availability: Multi-AZ (optional)
  Backup: Daily automated backups
  Network: Private Subnet (10.0.2.0/24)
  Security Group: sg-rds-private
```

**Connection String:**
```env
RDS_HOST=rds-xxx.huaweicloud.com
RDS_PORT=5432
RDS_DB=medical_db
RDS_USER=admin
RDS_PASSWORD=<secure-password>
```

### 2. Application Code Integration

**RDS Client Implementation:**
```python
# rds_client.py
import psycopg2
from psycopg2.extras import RealDictCursor
from config import RDS_HOST, RDS_PORT, RDS_DB, RDS_USER, RDS_PASSWORD

class RDSClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            database=RDS_DB,
            user=RDS_USER,
            password=RDS_PASSWORD
        )
    
    def get_metadata(self, qa_id: str):
        """Get metadata for Q&A pair."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM medical_qa_metadata WHERE id = %s",
                (qa_id,)
            )
            return cur.fetchone()
    
    def get_relations(self, qa_id: str):
        """Get relations for Q&A pair."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM medical_qa_relations 
                WHERE source_id = %s OR target_id = %s
                """,
                (qa_id, qa_id)
            )
            return cur.fetchall()
    
    def log_query(self, qa_id: str, query_text: str, response_time: float):
        """Log user query."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO query_logs (qa_id, query_text, response_time)
                VALUES (%s, %s, %s)
                """,
                (qa_id, query_text, response_time)
            )
            self.conn.commit()
```

**Enhanced Context Integrator:**
```python
# context_integration.py (enhanced)
from rds_client import RDSClient

class ContextIntegrator:
    def __init__(self):
        self.milvus_client = MilvusClient()
        self.rds_client = RDSClient()
    
    def retrieve_enhanced_context(self, query_embedding, top_k=5):
        # 1. Vector search in Milvus
        milvus_results = self.milvus_client.search(query_embedding, top_k)
        
        # 2. Enrich with RDS metadata
        enriched_results = []
        for result in milvus_results:
            qa_id = result['id']
            
            # Get metadata from RDS
            metadata = self.rds_client.get_metadata(qa_id)
            relations = self.rds_client.get_relations(qa_id)
            sources = self.rds_client.get_sources(qa_id)
            
            enriched_result = {
                **result,
                'metadata': metadata,
                'relations': relations,
                'sources': sources
            }
            enriched_results.append(enriched_result)
        
        return enriched_results
```

### 3. Environment Configuration

**.env additions:**
```env
# RDS Configuration
RDS_HOST=rds-xxx.huaweicloud.com
RDS_PORT=5432
RDS_DB=medical_db
RDS_USER=admin
RDS_PASSWORD=<secure-password>

# Sync Configuration
SYNC_ENABLED=true
SYNC_INTERVAL=300  # seconds
```

---

## 📊 Maliyet Analizi (Hibrit Mimari)

### Aylık Maliyet

| Servis | Spec | Aylık Maliyet |
|--------|------|---------------|
| **VPC** | Free tier | $0 |
| **ECS Instance** | s6.medium.2 | ~$30-40 |
| **EIP** | 1 adet | ~$5 |
| **Milvus Cloud** | Free tier (Zilliz) | $0 |
| **RDS PostgreSQL** | rds.pg.n1.large.2 | ~$50-70 |
| **OBS Storage** | 50 GB | ~$2-5 |
| **ModelArts API** | Pay-per-use | ~$10-20 |
| **Bandwidth** | ~100 GB | ~$5-10 |
| **TOTAL** | | **~$102-150/ay** |

**Not:** RDS eklenince maliyet artar, ama structured data ve analytics için gerekli.

---

## 🔍 Veri Bütünlüğü ve Consistency

### Consistency Strategies

**1. Eventual Consistency (Önerilen):**
- Milvus insert → immediate
- RDS insert → async (background job)
- Acceptable delay: <5 seconds

**2. Strong Consistency:**
- Transactional insert (both Milvus and RDS)
- Slower but guaranteed consistency
- Use for critical data

**3. Read Consistency:**
- Always read from both sources
- Merge results
- Handle missing data gracefully

---

## 🚀 Deployment Checklist

- [ ] RDS instance oluşturuldu
- [ ] RDS schema oluşturuldu (tüm tablolar)
- [ ] RDS security group yapılandırıldı
- [ ] RDS client kodları eklendi
- [ ] Context integrator güncellendi
- [ ] Sync service implement edildi
- [ ] Backup scriptleri hazırlandı
- [ ] Monitoring yapılandırıldı
- [ ] Test edildi (insert, query, sync)

---

**Son Güncelleme:** 2024  
**Durum:** Production Ready  
**Mimari Tipi:** Hybrid (Milvus + RDS)

