# Zilliz Cloud Connection Setup - Detaylı Kılavuz

Collection oluşturulduktan sonra Python script'inizin Milvus Cloud'a bağlanabilmesi için gerekli adımlar.

## 📍 Adım 1: Connection Info'yu Alın

### 1.1. Zilliz Cloud Console'da Connection Bilgilerini Bulun

1. **Zilliz Cloud Console'a giriş yapın**
   - https://cloud.zilliz.com adresine gidin
   - Login olun

2. **Cluster'ınızı seçin**
   - Dashboard'da oluşturduğunuz cluster'ı bulun
   - Cluster'ın üzerine tıklayın veya "View Details" butonuna tıklayın

3. **Connection Info sekmesine gidin**
   - Cluster detay sayfasında "Connection Info" veya "Connect" sekmesine tıklayın
   - Veya sol menüden "Connection" seçeneğine tıklayın

4. **Bilgileri kopyalayın:**
   ```
   Public Endpoint: xxx.gcp-us-west1.vectordb.zillizcloud.com
   Port: 443
   ```

### 1.2. Connection Info Örneği

Ekranda şuna benzer bir bilgi göreceksiniz:

```
┌─────────────────────────────────────────────────┐
│ Connection Information                           │
├─────────────────────────────────────────────────┤
│ Public Endpoint:                                 │
│ in01-abc123.gcp-us-west1.vectordb.zillizcloud.com│
│                                                  │
│ Port:                                            │
│ 443                                              │
│                                                  │
│ [Copy] button                                    │
└─────────────────────────────────────────────────┘
```

**ÖNEMLİ:** Bu bilgileri bir yere not edin!

---

## 🔑 Adım 2: API Key Oluşturun

### 2.1. API Keys Sekmesine Gidin

1. **Zilliz Cloud Console'da**
   - Sol menüden "API Keys" veya "Security" sekmesine tıklayın
   - Veya cluster detay sayfasında "API Keys" sekmesine gidin

2. **"Create API Key" butonuna tıklayın**

### 2.2. API Key Oluşturma

1. **Key adı verin** (opsiyonel):
   - Örnek: `medical_rag_key` veya `graphrag_api_key`
   - Bu sadece sizin için bir etiket

2. **"Create" butonuna tıklayın**

3. **⚠️ ÇOK ÖNEMLİ: API Key'i kopyalayın!**
   ```
   Örnek format:
   db_admin:AbCdEf1234567890XyZ...
   ```
   
   **UYARI:** Bu key'i bir daha göremeyeceksiniz! 
   - Hemen kopyalayın
   - Güvenli bir yerde saklayın
   - `.env` dosyasına ekleyin

### 2.3. API Key Formatı

API key genellikle şu formatta olur:
```
db_admin:AbCdEf1234567890XyZaBcDeFgHiJkLmNoPqRsTuVwXyZ
```

Tamamı tek bir string'dir, boşluk yoktur.

---

## 📝 Adım 3: .env Dosyasını Güncelleyin

### 3.1. .env Dosyasını Bulun

Proje klasörünüzde `.env` dosyası olmalı. Eğer yoksa oluşturun:

```bash
# Proje klasöründe
touch .env
# veya Windows'ta
type nul > .env
```

### 3.2. .env Dosyasına Bilgileri Ekleyin

`.env` dosyanızı açın ve şu bilgileri ekleyin:

```env
# Milvus Cloud Configuration
MILVUS_USE_CLOUD=true
MILVUS_HOST=in01-abc123.gcp-us-west1.vectordb.zillizcloud.com
MILVUS_PORT=443
MILVUS_API_KEY=db_admin:AbCdEf1234567890XyZ...
MILVUS_COLLECTION_NAME=medical_knowledge_base

# Embedding Model
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2

# GraphRAG Settings
GRAPH_SIMILARITY_THRESHOLD=0.7
GRAPH_MAX_DEPTH=2
RETRIEVAL_TOP_K=5

# LLM Configuration (eğer kullanıyorsanız)
GOOGLE_API_KEY=your_google_api_key_here
LLM_MODEL=gemini-2.5-flash
```

### 3.3. .env Dosyası Örneği

**Gerçek değerlerinizle doldurun:**

```env
# ============================================
# Milvus Cloud Configuration
# ============================================
MILVUS_USE_CLOUD=true
MILVUS_HOST=in01-abc123.gcp-us-west1.vectordb.zillizcloud.com
MILVUS_PORT=443
MILVUS_API_KEY=db_admin:AbCdEf1234567890XyZaBcDeFgHiJkLmNoPqRsTuVwXyZ
MILVUS_COLLECTION_NAME=medical_knowledge_base

# ============================================
# Embedding Configuration
# ============================================
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
EMBEDDING_DIMENSION=768

# ============================================
# GraphRAG Configuration
# ============================================
GRAPH_RAG_ENABLED=true
GRAPH_SIMILARITY_THRESHOLD=0.7
GRAPH_MAX_DEPTH=2
RETRIEVAL_TOP_K=5

# ============================================
# LLM Configuration
# ============================================
GOOGLE_API_KEY=your_google_api_key_here
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.2
```

### 3.4. Önemli Notlar

- ✅ **Tırnak işareti kullanmayın:** `MILVUS_HOST="..."` ❌ YANLIŞ
- ✅ **Doğru format:** `MILVUS_HOST=in01-abc123...` ✅ DOĞRU
- ✅ **API Key'in tamamını kopyalayın:** `db_admin:` ile başlayan tüm string
- ✅ **Boşluk olmamalı:** `MILVUS_API_KEY=db_admin:...` (eşittir işaretinden sonra boşluk yok)

---

## 🚀 Adım 4: Python Script'ini Çalıştırın

### 4.1. Terminal/Command Prompt'u Açın

Proje klasörünüze gidin:

```bash
cd c:\Users\samet\OneDrive\Belgeler\GitHub\huaweict
```

### 4.2. Virtual Environment Aktif Edin (Eğer kullanıyorsanız)

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4.3. Gerekli Paketlerin Yüklü Olduğundan Emin Olun

```bash
pip install -r requirements.txt
```

### 4.4. Script'i Çalıştırın

```bash
python build_graphrag.py
```

### 4.5. Script Çalışırken Ne Olacak?

Script şu adımları gerçekleştirecek:

1. **Dataset'i yükler:**
   ```
   Loading dataset: FreedomIntelligence/medical-o1-reasoning-SFT
   Dataset loaded successfully. Size: 19700
   ```

2. **Q&A çiftlerini işler:**
   ```
   Processing 19700 Q&A pairs...
   Successfully processed 19700 Q&A pairs
   ```

3. **Milvus'a bağlanır:**
   ```
   Connected to Milvus at xxx.vectordb.zillizcloud.com:443
   Using API key authentication for Milvus Cloud
   ```

4. **Collection'ı kontrol eder:**
   ```
   Collection medical_knowledge_base already exists.
   ```

5. **Embedding'leri oluşturur:**
   ```
   Loading embedding model: sentence-transformers/all-mpnet-base-v2
   Generating embeddings...
   Generated embeddings for 500 pairs...
   ```

6. **Graph yapısını oluşturur:**
   ```
   Building similarity graph...
   Computing similarity matrix...
   Built graph with 150000 edges
   ```

7. **Milvus'a kaydeder:**
   ```
   Inserting 19700 records into Milvus...
   Inserted batch 1 (50 records)
   ...
   All data inserted and flushed successfully
   ```

8. **Tamamlanır:**
   ```
   GraphRAG build completed successfully!
   ```

### 4.6. İlk Çalıştırmada Beklenen Süre

- **Dataset indirme:** 2-5 dakika (ilk kez)
- **Embedding oluşturma:** 30-60 dakika (19,700 Q&A çifti için)
- **Graph oluşturma:** 10-20 dakika
- **Milvus'a kaydetme:** 5-10 dakika

**Toplam:** Yaklaşık 1-2 saat (dataset boyutuna bağlı)

---

## ✅ Bağlantı Testi

### Test Script'i Oluşturun

`test_connection.py` dosyası oluşturun:

```python
"""Test Milvus Cloud Connection"""
import logging
from pymilvus import connections, utility
from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY,
    MILVUS_COLLECTION_NAME, MILVUS_USE_CLOUD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Milvus Cloud connection."""
    try:
        # Connect
        connection_params = {
            "alias": "default",
            "host": MILVUS_HOST,
            "port": MILVUS_PORT
        }
        
        if MILVUS_USE_CLOUD and MILVUS_API_KEY:
            connection_params["token"] = MILVUS_API_KEY
        
        connections.connect(**connection_params)
        logger.info(f"✅ Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
        
        # List collections
        collections = utility.list_collections()
        logger.info(f"✅ Collections: {collections}")
        
        # Check our collection
        if MILVUS_COLLECTION_NAME in collections:
            logger.info(f"✅ Collection '{MILVUS_COLLECTION_NAME}' exists!")
            
            from pymilvus import Collection
            collection = Collection(MILVUS_COLLECTION_NAME)
            collection.load()
            
            # Get entity count
            num_entities = collection.num_entities
            logger.info(f"✅ Collection has {num_entities} entities")
        else:
            logger.warning(f"⚠️ Collection '{MILVUS_COLLECTION_NAME}' not found")
        
        logger.info("✅ Connection test successful!")
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_connection()
```

### Test Script'ini Çalıştırın

```bash
python test_connection.py
```

**Başarılı çıktı:**
```
✅ Connected to Milvus at xxx.vectordb.zillizcloud.com:443
✅ Collections: ['medical_knowledge_base']
✅ Collection 'medical_knowledge_base' exists!
✅ Collection has 19700 entities
✅ Connection test successful!
```

---

## 🐛 Sorun Giderme

### Hata: "Connection refused"

**Sebep:** Port veya host yanlış

**Çözüm:**
- `.env` dosyasında `MILVUS_PORT=443` olduğundan emin olun
- `MILVUS_HOST` değerinin doğru olduğunu kontrol edin
- Zilliz Cloud console'dan connection info'yu tekrar kontrol edin

### Hata: "Invalid token" veya "Authentication failed"

**Sebep:** API key yanlış veya eksik

**Çözüm:**
- `.env` dosyasında `MILVUS_API_KEY` değerini kontrol edin
- API key'in tamamını kopyaladığınızdan emin olun (`db_admin:` ile başlayan tüm string)
- Zilliz Cloud console'dan yeni bir API key oluşturun

### Hata: "Collection not found"

**Sebep:** Collection adı yanlış veya collection oluşturulmamış

**Çözüm:**
- `.env` dosyasında `MILVUS_COLLECTION_NAME=medical_knowledge_base` olduğundan emin olun
- Zilliz Cloud console'da collection'ın oluşturulduğunu kontrol edin

### Hata: "Module not found" veya "Import error"

**Sebep:** Gerekli paketler yüklü değil

**Çözüm:**
```bash
pip install -r requirements.txt
```

---

## 📋 Kontrol Listesi

Collection oluşturduktan sonra:

- [ ] Zilliz Cloud console'dan Public Endpoint'i kopyaladım
- [ ] Port bilgisini not ettim (genellikle 443)
- [ ] API Key oluşturdum ve kopyaladım
- [ ] `.env` dosyasını oluşturdum/güncelledim
- [ ] `MILVUS_USE_CLOUD=true` ayarladım
- [ ] `MILVUS_HOST` değerini ekledim
- [ ] `MILVUS_PORT` değerini ekledim
- [ ] `MILVUS_API_KEY` değerini ekledim
- [ ] `MILVUS_COLLECTION_NAME` değerini ekledim
- [ ] `test_connection.py` ile bağlantıyı test ettim
- [ ] `python build_graphrag.py` script'ini çalıştırdım

---

## 🎯 Sonraki Adımlar

Bağlantı başarılı olduktan ve GraphRAG build edildikten sonra:

1. ✅ RAG service'i kullanmaya başlayabilirsiniz
2. ✅ `app.py` ile Streamlit uygulamasını çalıştırabilirsiniz
3. ✅ Medical sorular sorabilir ve GraphRAG'dan cevaplar alabilirsiniz
