# 🏗️ Uçtan Uca Hibrit Mimari: Milvus + RDS Detaylı Kılavuz

**Proje:** Huawei Cloud AI Health Assistant  
**Mimari:** Hybrid Architecture (Milvus Vector DB + RDS Relational DB)  
**Durum:** Production Ready - Complete Guide

---

## 📋 İçindekiler

1. [Mimari Genel Bakış](#mimari-genel-bakış)
2. [Veri Katmanları Detayı](#veri-katmanları-detayı)
3. [Milvus Vector Database](#milvus-vector-database)
4. [RDS Relational Database](#rds-relational-database)
5. [Veri Akışı: Ekleme, Okuma, Güncelleme](#veri-akışı)
6. [Export ve Backup](#export-ve-backup)
7. [Senkronizasyon Stratejileri](#senkronizasyon-stratejileri)
8. [Deployment](#deployment)

---

## 🎯 Mimari Genel Bakış

### Tam Mimari Diyagramı

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTERNET / EXTERNAL USERS                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ECS Instance (Application Layer)                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Streamlit App (Port 8501)                                       │  │
│  │  • RAG Service                                                    │  │
│  │  • Query Processing                                               │  │
│  │  • Response Generation                                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Health Check (Port 8080)                                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                                     │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Context Integrator                                               │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  Milvus Client                                             │  │  │
│  │  │  • Vector Search                                           │  │  │
│  │  │  • Graph Traversal                                         │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  RDS Client                                                │  │  │
│  │  │  • Metadata Queries                                        │  │  │
│  │  │  • Relation Queries                                        │  │  │
│  │  │  • Analytics                                               │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │  OBS Client                                                │  │  │
│  │  │  • Document Storage                                        │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
┌───────────────────────────┐              ┌───────────────────────────┐
│   MILVUS VECTOR DB        │              │   RDS RELATIONAL DB       │
│  (Zilliz Cloud / Huawei)  │              │   (Huawei Cloud RDS)      │
│                           │              │                           │
│  Collection:              │              │  Tables:                  │
│  medical_knowledge_base   │              │  • medical_qa_metadata    │
│                           │              │  • medical_qa_relations   │
│  Fields:                  │              │  • query_logs             │
│  • id (PK)                │              │  • document_sources       │
│  • question               │              │  • analytics               │
│  • response               │              │  • sync_status            │
│  • question_embedding    │              │                           │
│  • response_embedding    │              │  Views:                   │
│  • combined_embedding    │              │  • qa_with_stats          │
│  • metadata (JSON)       │              │  • popular_qa             │
│  • related_nodes (JSON)  │              │                           │
└───────────────────────────┘              └───────────────────────────┘
        │                                               │
        └───────────────────────┬───────────────────────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │  OBS Storage       │
                    │  • Raw documents   │
                    │  • Processed files  │
                    │  • Backups          │
                    └───────────────────┘
```

---

## 📊 Veri Katmanları Detayı

### Milvus'ta Ne Saklanır?

**1. Vector Embeddings:**
- `question_embedding`: 768 boyutlu float vector
- `response_embedding`: 768 boyutlu float vector  
- `combined_embedding`: 768 boyutlu float vector (GraphRAG için)

**2. Q&A Metinleri:**
- `question`: Soru metni (max 5000 karakter)
- `response`: Cevap metni (max 10000 karakter)

**3. Graph Structure:**
- `related_nodes`: İlişkili node ID'leri (JSON array)
- Similarity scores (hesaplanan, saklanmaz)

**4. Temel Metadata (JSON):**
```json
{
  "category": "Cardiology",
  "source": "Textbook",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### RDS'de Ne Saklanır?

**1. Detaylı Metadata (`medical_qa_metadata`):**
- Kategoriler ve alt kategoriler
- Kaynak bilgileri (detaylı)
- Yazar bilgileri
- Yayın tarihi
- Dil bilgisi
- Zorluk seviyesi
- Etiketler (tags array)
- Timestamps (created_at, updated_at)
- Aktiflik durumu (is_active)

**2. İlişkiler (`medical_qa_relations`):**
- Source → Target ilişkileri
- İlişki tipleri (symptom_of, treatment_for, etc.)
- Confidence scores
- Timestamps

**3. Query Logs (`query_logs`):**
- Kullanıcı sorguları
- Dönen cevaplar
- Response time
- Similarity scores
- User feedback
- Session tracking

**4. Document Sources (`document_sources`):**
- OBS'deki kaynak dosyalar
- Sayfa numaraları
- Bölüm bilgileri
- Excerpt'ler

**5. Analytics (`analytics`):**
- Metrikler (query_count, avg_response_time, etc.)
- Tarih bazlı istatistikler
- Performance metrikleri

---

## 🔄 Veri Akışı: Uçtan Uca Senaryolar

### Senaryo 1: Yeni Veri Ekleme (End-to-End)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DATA INGESTION                                           │
│    Admin uploads medical document (PDF/DOCX)                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. DOCUMENT PROCESSING                                      │
│    • Extract text from document                             │
│    • Parse into Q&A pairs                                   │
│    • Extract metadata (category, source, etc.)              │
│    • Generate embeddings (3 types)                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PARALLEL INSERTION                                       │
│                                                              │
│    ┌────────────────────┐      ┌────────────────────┐     │
│    │ 3a. Milvus Insert  │      │ 3b. RDS Insert     │     │
│    │                    │      │                    │     │
│    │ • question         │      │ • metadata        │     │
│    │ • response         │      │ • relations        │     │
│    │ • embeddings (3)   │      │ • sources          │     │
│    │ • basic metadata   │      │ • analytics        │     │
│    │ • related_nodes=[] │      │                    │     │
│    └─────────┬──────────┘      └─────────┬──────────┘     │
│              │                            │                │
│              └────────────┬───────────────┘                │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. GRAPH RELATIONSHIP BUILDING                              │
│    • Calculate similarities with existing records           │
│    • Find related Q&A pairs                                 │
│    • Update related_nodes in Milvus                        │
│    • Insert relations in RDS                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. VERIFICATION & SYNC                                     │
│    • Verify both Milvus and RDS have data                  │
│    • Update sync_status table                               │
│    • Rebuild indexes if needed                             │
└─────────────────────────────────────────────────────────────┘
```

**Kod Örneği:**
```python
def insert_new_qa_pair(question, response, metadata):
    # 1. Generate embeddings
    question_emb = embedding_model.embed_query(question)
    response_emb = embedding_model.embed_query(response)
    combined_emb = embedding_model.embed_query(f"{question} {response}")
    
    # 2. Generate ID
    qa_id = str(uuid.uuid4())
    
    # 3. Insert to Milvus
    milvus_record = {
        "id": qa_id,
        "question": question,
        "response": response,
        "question_embedding": question_emb,
        "response_embedding": response_emb,
        "combined_embedding": combined_emb,
        "metadata": {"category": metadata.get("category")},
        "related_nodes": []
    }
    collection.insert([milvus_record])
    collection.flush()
    
    # 4. Insert to RDS (transactional)
    with rds_client.conn:
        rds_client.insert_metadata(
            qa_id=qa_id,
            category=metadata.get("category"),
            source=metadata.get("source"),
            source_type=metadata.get("source_type"),
            author=metadata.get("author"),
            tags=metadata.get("tags", [])
        )
        
        # Insert document sources
        for source in metadata.get("sources", []):
            rds_client.insert_source(
                qa_id=qa_id,
                document_name=source["name"],
                document_path=source["path"],
                page_number=source.get("page"),
                section=source.get("section")
            )
    
    # 5. Build graph relationships (async)
    build_graph_relationships(qa_id)
    
    return qa_id
```

---

### Senaryo 2: Query Processing (End-to-End)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER QUERY                                              │
│    "What are the symptoms of hypertension?"                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. QUERY PROCESSING                                        │
│    • Preprocess query text                                 │
│    • Generate query embedding                              │
│    • Extract keywords                                      │
│    • Determine intent                                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PARALLEL SEARCH                                         │
│                                                              │
│    ┌────────────────────┐      ┌────────────────────┐     │
│    │ 3a. Milvus Search │      │ 3b. RDS Query     │     │
│    │                    │      │                    │     │
│    │ Vector Search:     │      │ Metadata Filter:  │     │
│    │ • Find similar     │      │ • category filter │     │
│    │   Q&A pairs        │      │ • Get relations   │     │
│    │ • Top 10 results   │      │ • Get sources     │     │
│    │ • Similarity scores│      │ • Get analytics   │     │
│    └─────────┬──────────┘      └─────────┬──────────┘     │
│              │                            │                │
│              └────────────┬───────────────┘                │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. RESULT MERGING & ENRICHMENT                             │
│    • Combine Milvus results with RDS metadata               │
│    • Apply RDS filters                                      │
│    • Re-rank by combined relevance                         │
│    • Enrich with RDS relations and sources                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. GRAPH TRAVERSAL (GraphRAG)                              │
│    • Get related_nodes from Milvus                         │
│    • Get relation details from RDS                         │
│    • Traverse graph (max_depth=2)                          │
│    • Build enriched context                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. RESPONSE GENERATION                                      │
│    • LLM generates response                                 │
│    • Include sources from RDS                               │
│    • Include metadata                                       │
│    • Format response                                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. LOGGING & ANALYTICS                                     │
│    • Log query to RDS query_logs                           │
│    • Update analytics                                       │
│    • Track user feedback (if provided)                     │
└─────────────────────────────────────────────────────────────┘
```

**Kod Örneği:**
```python
def process_query(user_query: str):
    start_time = time.time()
    
    # 1. Generate query embedding
    query_embedding = embedding_model.embed_query(user_query)
    
    # 2. Parallel search
    # Milvus vector search
    milvus_results = context_integrator.retrieve_graphrag_context(
        query_embedding,
        top_k=10,
        max_depth=2,
        enrich_with_rds=True  # Enable RDS enrichment
    )
    
    # 3. Enrich with RDS data
    enriched_results = []
    for result in milvus_results["qa_pairs"]:
        qa_id = result["id"]
        
        # Get additional data from RDS
        rds_metadata = rds_client.get_metadata(qa_id)
        relations = rds_client.get_relations(qa_id)
        sources = rds_client.get_sources(qa_id)
        
        enriched_result = {
            **result,
            "rds_metadata": rds_metadata,
            "relations": relations,
            "sources": sources
        }
        enriched_results.append(enriched_result)
    
    # 4. Generate response
    context = build_context_string(enriched_results)
    response = llm.generate(user_query, context)
    
    # 5. Log query
    response_time = time.time() - start_time
    rds_client.log_query(
        qa_id=enriched_results[0]["id"] if enriched_results else None,
        query_text=user_query,
        response_text=response,
        response_time=response_time,
        similarity_score=enriched_results[0].get("similarity") if enriched_results else None
    )
    
    return {
        "response": response,
        "sources": enriched_results,
        "metadata": {
            "response_time": response_time,
            "results_count": len(enriched_results)
        }
    }
```

---

### Senaryo 3: Veri Güncelleme

```
┌─────────────────────────────────────────────────────────────┐
│ 1. UPDATE REQUEST                                           │
│    Admin updates Q&A pair (id: "abc123")                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PARALLEL UPDATE                                          │
│                                                              │
│    ┌────────────────────┐      ┌────────────────────┐     │
│    │ 2a. Milvus Update  │      │ 2b. RDS Update     │     │
│    │                    │      │                    │     │
│    │ • Update text      │      │ • Update metadata  │     │
│    │ • Regenerate       │      │ • Update relations │     │
│    │   embeddings       │      │ • Update sources   │     │
│    │ • Update           │      │ • Update           │     │
│    │   related_nodes    │      │   timestamps       │     │
│    └─────────┬──────────┘      └─────────┬──────────┘     │
│              │                            │                │
│              └────────────┬───────────────┘                │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. GRAPH REBUILD                                            │
│    • Recalculate similarities                               │
│    • Update related_nodes                                   │
│    • Update relations in RDS                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. VERIFICATION                                             │
│    • Verify sync                                            │
│    • Update sync_status                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📤 Export ve Backup

### Milvus'tan Export

**1. CSV Export:**
```bash
python export_from_milvus.py \
  --format csv \
  --output backup/milvus_export.csv \
  --batch-size 1000
```

**2. JSON Export (Embedding'ler dahil):**
```bash
python export_from_milvus.py \
  --format json \
  --output backup/milvus_full.json \
  --include-embeddings
```

**3. RDS'e Direkt Export:**
```bash
python export_from_milvus.py \
  --format sql \
  --output "postgresql://user:pass@rds-endpoint:5432/medical_db" \
  --table-name milvus_backup
```

### RDS Backup

**1. PostgreSQL Backup:**
```bash
pg_dump -h $RDS_HOST -U $RDS_USER -d $RDS_DB \
  -F c -f backup/rds_backup.dump
```

**2. MySQL Backup:**
```bash
mysqldump -h $RDS_HOST -u $RDS_USER -p$RDS_PASSWORD $RDS_DB \
  > backup/rds_backup.sql
```

**3. Huawei Cloud RDS Automated Backup:**
- RDS Console → Backup Management
- Enable automated backups
- Retention: 7-30 days

### Combined Backup

**Full Backup Script:**
```bash
./backup_full.sh
```

Bu script:
1. Milvus'u JSON'a export eder
2. RDS'i dump eder
3. OBS'e upload eder (opsiyonel)
4. Manifest oluşturur

---

## 🔄 Senkronizasyon Stratejileri

### Strateji 1: Real-time Sync (Önerilen)

**Avantajlar:**
- ✅ Anında consistency
- ✅ Data integrity garantisi
- ✅ Transactional safety

**Dezavantajlar:**
- ❌ Daha yavaş (her insert'te 2 DB'ye yazma)
- ❌ Daha kompleks error handling

**Kullanım:**
- Critical data için
- Yüksek consistency gerektiren durumlar

### Strateji 2: Eventual Consistency

**Avantajlar:**
- ✅ Daha hızlı (async insert)
- ✅ Better performance
- ✅ Fault tolerant

**Dezavantajlar:**
- ❌ Kısa süreli inconsistency (<5 saniye)
- ❌ Background job gerektirir

**Kullanım:**
- Non-critical data için
- Yüksek performans gerektiren durumlar

### Strateji 3: Batch Sync

**Avantajlar:**
- ✅ En yüksek performans
- ✅ Resource efficient

**Dezavantajlar:**
- ❌ Daha uzun delay (dakikalar/saatler)
- ❌ Batch processing gerektirir

**Kullanım:**
- Büyük veri setleri için
- Offline processing

---

## 🚀 Deployment Adımları

### Phase 1: Milvus Setup

```bash
# 1. Milvus Cloud (Zilliz) kullan veya Huawei Cloud Milvus
# 2. Collection oluştur
python build_graphrag.py

# 3. Indexes oluştur
python create_indexes.py

# 4. Test connection
python test_connection.py
```

### Phase 2: RDS Setup

```bash
# 1. Huawei Cloud RDS instance oluştur
#    - Engine: PostgreSQL 14+
#    - Instance: rds.pg.n1.large.2
#    - Storage: 100 GB SSD

# 2. Schema oluştur
psql -h $RDS_HOST -U $RDS_USER -d $RDS_DB -f create_rds_schema.sql

# 3. Test connection
python -c "from rds_client import RDSClient; client = RDSClient(); print('✅ RDS connected')"
```

### Phase 3: Application Integration

```bash
# 1. Update .env with RDS credentials
# 2. Install RDS dependencies
pip install psycopg2-binary  # PostgreSQL
# veya
pip install pymysql  # MySQL

# 3. Test integration
python test_rds_integration.py
```

---

## 📊 Maliyet Analizi

### Hibrit Mimari Maliyeti

| Servis | Spec | Aylık Maliyet |
|--------|------|---------------|
| **VPC** | Free | $0 |
| **ECS** | s6.medium.2 | ~$30-40 |
| **EIP** | 1 adet | ~$5 |
| **Milvus** | Free tier (Zilliz) | $0 |
| **RDS PostgreSQL** | rds.pg.n1.large.2 | ~$50-70 |
| **OBS** | 50 GB | ~$2-5 |
| **ModelArts** | Pay-per-use | ~$10-20 |
| **Bandwidth** | ~100 GB | ~$5-10 |
| **TOTAL** | | **~$102-150/ay** |

**100$ Bütçe İçin:**
- RDS olmadan: ~$53-82/ay ✅
- RDS ile: ~$102-150/ay ❌ (bütçe aşılır)

**Öneri:** İlk aşamada RDS olmadan başla, gerektiğinde ekle.

---

## ✅ Deployment Checklist

- [ ] Milvus collection oluşturuldu ve test edildi
- [ ] RDS instance oluşturuldu (opsiyonel)
- [ ] RDS schema oluşturuldu (create_rds_schema.sql)
- [ ] RDS client test edildi
- [ ] Context integrator RDS entegrasyonu test edildi
- [ ] Export scriptleri test edildi
- [ ] Backup stratejisi belirlendi
- [ ] Sync stratejisi belirlendi
- [ ] Monitoring yapılandırıldı

---

**Son Güncelleme:** 2024  
**Durum:** Production Ready  
**Dokümantasyon:** Complete

