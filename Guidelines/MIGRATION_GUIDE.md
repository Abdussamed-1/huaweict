# 📦 Veritabanı Migration Kılavuzu - Milvus'a Veri Aktarımı

Bu kılavuz, farklı veritabanlarından veya dosyalardan Milvus vector veritabanına veri aktarımı için adım adım talimatlar içerir.

---

## 🎯 Desteklenen Kaynaklar

1. **SQL Veritabanları** (PostgreSQL, MySQL, SQLite, SQL Server, Oracle)
2. **CSV Dosyaları**
3. **JSON Dosyaları**
4. **Excel Dosyaları** (.xlsx, .xls)

---

## 📋 Ön Hazırlık

### 1. Milvus Collection Hazırlığı

Migration'dan önce Milvus collection'ın oluşturulmuş olması gerekir:

```bash
# Collection oluştur (eğer yoksa)
python build_graphrag.py

# Veya create_indexes.py ile kontrol et
python create_indexes.py
```

### 2. Gerekli Paketler

```bash
pip install pandas sqlalchemy openpyxl
```

**Not:** `pymilvus`, `langchain-huggingface` zaten requirements.txt'te mevcut.

---

## 🚀 Migration Senaryoları

### Senaryo 1: CSV Dosyasından Migration

**CSV Format Örneği:**
```csv
id,question,answer,category,source
1,"What is hypertension?","Hypertension is high blood pressure...","Cardiology","Textbook"
2,"What causes diabetes?","Diabetes is caused by...","Endocrinology","Journal"
```

**Migration Komutu:**
```bash
python migrate_to_milvus.py \
  --source csv \
  --input data/medical_qa.csv \
  --question question \
  --response answer \
  --id id \
  --metadata category source \
  --batch-size 50
```

**Parametreler:**
- `--source csv`: Kaynak tipi
- `--input`: CSV dosya yolu
- `--question`: Soru kolonu adı
- `--response`: Cevap kolonu adı
- `--id`: ID kolonu (opsiyonel, yoksa UUID oluşturulur)
- `--metadata`: Metadata'ya eklenecek kolonlar
- `--batch-size`: Her batch'te işlenecek kayıt sayısı

---

### Senaryo 2: SQL Veritabanından Migration

**PostgreSQL Örneği:**
```bash
python migrate_to_milvus.py \
  --source sql \
  --input "postgresql://user:password@localhost:5432/medical_db" \
  --query "SELECT id, question, answer, category FROM medical_qa WHERE category = 'Cardiology'" \
  --question question \
  --response answer \
  --id id \
  --metadata category \
  --batch-size 100
```

**MySQL Örneği:**
```bash
python migrate_to_milvus.py \
  --source sql \
  --input "mysql+pymysql://user:password@localhost:3306/medical_db" \
  --query "SELECT * FROM medical_qa" \
  --question question \
  --response answer \
  --batch-size 100
```

**SQLite Örneği:**
```bash
python migrate_to_milvus.py \
  --source sql \
  --input "sqlite:///medical.db" \
  --query "SELECT * FROM medical_qa" \
  --question question \
  --response answer \
  --batch-size 100
```

**Connection String Formatları:**
- PostgreSQL: `postgresql://user:pass@host:port/dbname`
- MySQL: `mysql+pymysql://user:pass@host:port/dbname`
- SQLite: `sqlite:///path/to/database.db`
- SQL Server: `mssql+pyodbc://user:pass@host:port/dbname?driver=ODBC+Driver+17+for+SQL+Server`

---

### Senaryo 3: JSON Dosyasından Migration

**JSON Format Örneği:**
```json
[
  {
    "id": "1",
    "question": "What is hypertension?",
    "answer": "Hypertension is high blood pressure...",
    "category": "Cardiology",
    "source": "Textbook"
  },
  {
    "id": "2",
    "question": "What causes diabetes?",
    "answer": "Diabetes is caused by...",
    "category": "Endocrinology"
  }
]
```

**Migration Komutu:**
```bash
python migrate_to_milvus.py \
  --source json \
  --input data/medical_qa.json \
  --question question \
  --response answer \
  --id id \
  --metadata category source \
  --batch-size 50
```

**Nested JSON Örneği:**
```json
{
  "medical_qa": [
    {
      "q": "What is hypertension?",
      "a": "Hypertension is...",
      "cat": "Cardiology"
    }
  ]
}
```

Bu durumda script otomatik olarak nested structure'ı handle eder.

---

### Senaryo 4: Excel Dosyasından Migration

**Excel Format:**
- Sheet'te `question`, `answer`, `category` kolonları olmalı

**Migration Komutu:**
```bash
python migrate_to_milvus.py \
  --source excel \
  --input data/medical_qa.xlsx \
  --sheet "Sheet1" \
  --question question \
  --response answer \
  --metadata category \
  --batch-size 50
```

**Sheet Seçimi:**
- Sheet adı: `--sheet "Sheet1"`
- Sheet index: `--sheet 0` (ilk sheet)

---

## 🔧 Python Script ile Migration

Migration'ı Python script olarak da yapabilirsiniz:

```python
from migrate_to_milvus import DatabaseMigrator

# Initialize migrator
migrator = DatabaseMigrator()

# CSV'den migration
migrator.migrate_from_csv(
    csv_path="data/medical_qa.csv",
    question_column="question",
    response_column="answer",
    id_column="id",
    metadata_columns=["category", "source"],
    batch_size=100
)

# SQL'den migration
migrator.migrate_from_sql(
    connection_string="postgresql://user:pass@localhost/db",
    query="SELECT * FROM medical_qa",
    question_column="question",
    response_column="answer",
    id_column="id",
    metadata_columns=["category"],
    batch_size=100
)

# JSON'dan migration
migrator.migrate_from_json(
    json_path="data/medical_qa.json",
    question_key="question",
    response_key="answer",
    id_key="id",
    metadata_keys=["category"],
    batch_size=100
)
```

---

## 📊 Migration Süreci

### 1. Veri Hazırlama
- Kaynak verileriniz `question` ve `response` formatında olmalı
- ID kolonu varsa kullanılır, yoksa otomatik UUID oluşturulur

### 2. Embedding Oluşturma
- Her kayıt için 3 embedding oluşturulur:
  - `question_embedding`: Soru için embedding
  - `response_embedding`: Cevap için embedding
  - `combined_embedding`: Soru + Cevap kombinasyonu (GraphRAG için)

### 3. Milvus'a Insert
- Batch'ler halinde insert edilir (default: 100 kayıt/batch)
- Her batch sonrası progress gösterilir

### 4. Graph Relationships
- Tüm kayıtlar insert edildikten sonra:
  - Cosine similarity hesaplanır
  - Similarity threshold (default: 0.7) üzerindeki kayıtlar `related_nodes` olarak işaretlenir
  - Her kayıt için en fazla 20 related node saklanır

---

## ⚙️ Konfigürasyon

### Environment Variables (.env)

Migration script'i `config.py`'deki ayarları kullanır:

```env
# Milvus Configuration
MILVUS_HOST=your_milvus_host
MILVUS_PORT=443
MILVUS_API_KEY=your_api_key
MILVUS_COLLECTION_NAME=medical_knowledge_base
MILVUS_USE_CLOUD=true

# Embedding Configuration
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768
```

### Batch Size Optimizasyonu

- **Küçük veri setleri (<1000 kayıt):** `--batch-size 50`
- **Orta veri setleri (1000-10000):** `--batch-size 100`
- **Büyük veri setleri (>10000):** `--batch-size 200`

**Not:** Batch size büyüdükçe memory kullanımı artar, ama işlem hızı da artar.

---

## 🔍 Migration Sonrası Kontrol

### 1. Kayıt Sayısını Kontrol Et

```python
from pymilvus import Collection, connections
from config import MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY, MILVUS_COLLECTION_NAME

connections.connect(
    alias="default",
    host=MILVUS_HOST,
    port=MILVUS_PORT,
    token=MILVUS_API_KEY
)

collection = Collection(MILVUS_COLLECTION_NAME)
collection.load()

print(f"Total records: {collection.num_entities}")
```

### 2. Örnek Kayıt Kontrolü

```python
# İlk 5 kaydı getir
results = collection.query(
    expr="id >= \"\"",
    limit=5,
    output_fields=["id", "question", "response", "metadata"]
)

for r in results:
    print(f"ID: {r['id']}")
    print(f"Question: {r['question'][:100]}...")
    print(f"Metadata: {r['metadata']}")
    print("---")
```

### 3. Graph Relationships Kontrolü

```python
# Related nodes kontrolü
results = collection.query(
    expr="id == \"your_record_id\"",
    output_fields=["id", "related_nodes"]
)

if results:
    print(f"Related nodes: {results[0]['related_nodes']}")
```

---

## 🐛 Troubleshooting

### Hata: "Collection does not exist"

**Çözüm:**
```bash
# Önce collection oluştur
python build_graphrag.py
```

### Hata: "Column not found"

**Çözüm:**
- CSV/Excel'de kolon adlarını kontrol et
- JSON'da key isimlerini kontrol et
- SQL query'de kolon isimlerini kontrol et

### Hata: "Embedding dimension mismatch"

**Çözüm:**
- `.env` dosyasında `EMBEDDING_DIMENSION` değerini kontrol et
- Collection schema'daki dimension ile eşleşmeli (genellikle 768)

### Hata: "Memory error" (büyük veri setleri için)

**Çözüm:**
- Batch size'ı küçült (`--batch-size 50`)
- Embedding model'i daha küçük bir model ile değiştir (`all-MiniLM-L6-v2` - 384 dimensions)

### Hata: "SQL connection failed"

**Çözüm:**
- Connection string formatını kontrol et
- Database erişim izinlerini kontrol et
- Network connectivity kontrol et

---

## 📈 Performance İpuçları

1. **GPU Kullanımı:** Eğer GPU varsa, embedding oluşturma çok daha hızlı olur
2. **Batch Processing:** Büyük veri setleri için batch size'ı optimize et
3. **Parallel Processing:** Çok büyük veri setleri için script'i paralel çalıştırabilirsiniz (farklı batch'ler için)

---

## 📝 Örnek Kullanım Senaryoları

### Senaryo: Mevcut PostgreSQL Veritabanından Migration

```bash
# 1. PostgreSQL'den tüm medical Q&A'ları çek
python migrate_to_milvus.py \
  --source sql \
  --input "postgresql://user:pass@localhost:5432/medical_db" \
  --query "SELECT id, question, answer, category, source FROM medical_qa" \
  --question question \
  --response answer \
  --id id \
  --metadata category source \
  --batch-size 100

# 2. Kontrol et
python test_connection.py
```

### Senaryo: CSV'den Incremental Migration

```bash
# İlk migration
python migrate_to_milvus.py \
  --source csv \
  --input data/batch1.csv \
  --question question \
  --response answer \
  --batch-size 100

# İkinci batch (aynı collection'a eklenir)
python migrate_to_milvus.py \
  --source csv \
  --input data/batch2.csv \
  --question question \
  --response answer \
  --batch-size 100
```

---

## ✅ Migration Checklist

- [ ] Milvus collection oluşturuldu
- [ ] `.env` dosyası doğru yapılandırıldı
- [ ] Gerekli paketler kuruldu (`pandas`, `sqlalchemy`, `openpyxl`)
- [ ] Kaynak veri formatı kontrol edildi
- [ ] Test migration yapıldı (küçük bir sample ile)
- [ ] Full migration çalıştırıldı
- [ ] Kayıt sayısı kontrol edildi
- [ ] Graph relationships kontrol edildi
- [ ] RAG service test edildi

---

**Son Güncelleme:** 2024  
**Script:** `migrate_to_milvus.py`  
**Durum:** Production Ready

