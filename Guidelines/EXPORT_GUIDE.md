# 📤 Milvus Export Kılavuzu - Veritabanını İndirme

Bu kılavuz, Milvus vector veritabanından verileri nasıl export edeceğinizi ve farklı formatlara nasıl aktaracağınızı açıklar.

---

## 🎯 Export Senaryoları

### Senaryo 1: CSV'ye Export

**Kullanım:**
```bash
python export_from_milvus.py \
  --format csv \
  --output backup/milvus_export_20241217.csv \
  --batch-size 1000
```

**Embedding'ler dahil:**
```bash
python export_from_milvus.py \
  --format csv \
  --output backup/milvus_full_export.csv \
  --include-embeddings \
  --batch-size 500
```

**Çıktı Formatı:**
```csv
id,question,response,metadata,related_nodes
abc123,"What is hypertension?","Hypertension is...","{\"category\":\"Cardiology\"}","[\"def456\",\"ghi789\"]"
```

---

### Senaryo 2: JSON'a Export

**Kullanım:**
```bash
python export_from_milvus.py \
  --format json \
  --output backup/milvus_export.json \
  --batch-size 1000
```

**Embedding'ler dahil:**
```bash
python export_from_milvus.py \
  --format json \
  --output backup/milvus_full_export.json \
  --include-embeddings
```

**Çıktı Formatı:**
```json
[
  {
    "id": "abc123",
    "question": "What is hypertension?",
    "response": "Hypertension is...",
    "metadata": {
      "category": "Cardiology"
    },
    "related_nodes": ["def456", "ghi789"],
    "question_embedding": [0.123, 0.456, ...],
    "response_embedding": [0.789, 0.012, ...],
    "combined_embedding": [0.345, 0.678, ...]
  }
]
```

---

### Senaryo 3: SQL Veritabanına Export (RDS'e)

**PostgreSQL:**
```bash
python export_from_milvus.py \
  --format sql \
  --output "postgresql://user:pass@rds-endpoint:5432/medical_db" \
  --table-name milvus_backup \
  --batch-size 500
```

**MySQL:**
```bash
python export_from_milvus.py \
  --format sql \
  --output "mysql+pymysql://user:pass@rds-endpoint:3306/medical_db" \
  --table-name milvus_backup \
  --batch-size 500
```

**Oluşturulan Tablo:**
```sql
CREATE TABLE milvus_backup (
    id VARCHAR(100) PRIMARY KEY,
    question TEXT,
    response TEXT,
    metadata JSON,
    related_nodes JSON,
    exported_at TIMESTAMP
);
```

---

### Senaryo 4: Excel'e Export

**Kullanım:**
```bash
python export_from_milvus.py \
  --format excel \
  --output backup/milvus_export.xlsx \
  --batch-size 1000
```

---

## 📊 Collection İstatistikleri

**Sadece istatistikleri görmek için:**
```bash
python export_from_milvus.py --stats
```

**Çıktı:**
```
============================================================
Collection Statistics
============================================================
total_records: 1250
collection_name: medical_knowledge_base
sample_size: 10
has_metadata: True
has_related_nodes: True
```

---

## 🔄 Export Sonrası İşlemler

### 1. Export'u Kontrol Et

**CSV Kontrolü:**
```bash
# Satır sayısını kontrol et
wc -l backup/milvus_export.csv

# İlk birkaç satırı göster
head -5 backup/milvus_export.csv
```

**JSON Kontrolü:**
```python
import json

with open('backup/milvus_export.json', 'r') as f:
    data = json.load(f)

print(f"Total records: {len(data)}")
print(f"First record: {data[0]}")
```

### 2. Export'u RDS'e Aktar

**Eğer SQL export kullanmadıysanız:**
```bash
# CSV'den RDS'e import
python migrate_to_milvus.py \
  --source csv \
  --input backup/milvus_export.csv \
  --question question \
  --response response \
  --id id \
  --batch-size 100
```

---

## 💾 Backup Stratejileri

### Strateji 1: Düzenli Otomatik Backup

**Cron Job (Linux):**
```bash
# Her gün saat 02:00'de backup al
0 2 * * * cd /opt/huaweict && python export_from_milvus.py --format json --output backup/milvus_backup_$(date +\%Y\%m\%d).json
```

**Systemd Timer (Linux):**
```ini
# /etc/systemd/system/milvus-backup.timer
[Unit]
Description=Daily Milvus Backup

[Timer]
OnCalendar=daily
OnCalendar=02:00

[Install]
WantedBy=timers.target
```

### Strateji 2: OBS'e Yedekleme

```bash
#!/bin/bash
# backup_to_obs.sh

BACKUP_FILE="backup/milvus_backup_$(date +%Y%m%d).json"

# Export Milvus
python export_from_milvus.py \
  --format json \
  --output $BACKUP_FILE \
  --batch-size 1000

# Upload to OBS
obsutil cp $BACKUP_FILE obs://backup-bucket/milvus-backups/

# Cleanup local file (optional)
# rm $BACKUP_FILE
```

---

## 🔍 Export Format Karşılaştırması

| Format | Embedding Desteği | Boyut | Kullanım |
|--------|-------------------|-------|----------|
| **CSV** | ✅ (JSON string) | Orta | Excel ile açılabilir |
| **JSON** | ✅ (Array) | Büyük | Programatik işleme |
| **SQL** | ✅ (JSON/Text) | Orta | Veritabanına direkt import |
| **Excel** | ✅ (JSON string) | Büyük | Manuel inceleme |

---

## ⚠️ Önemli Notlar

1. **Embedding'ler çok büyük:** Embedding'leri dahil ederseniz dosya boyutu çok artar (her embedding 768 float = ~3KB)
2. **Batch processing:** Büyük collection'lar için batch-size kullanın
3. **Memory:** Export sırasında memory kullanımı artar
4. **Network:** Milvus Cloud'tan export yaparken network bandwidth önemli

---

**Script:** `export_from_milvus.py`  
**Durum:** Production Ready

