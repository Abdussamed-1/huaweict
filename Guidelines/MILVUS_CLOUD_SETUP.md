# Milvus Cloud Cluster Bağlantı Kılavuzu

Bu dokümantasyon, Milvus Cloud free cluster'ınızı projeye nasıl bağlayacağınızı açıklar.

## 📋 Milvus Cloud'dan Alınacak Bilgiler

Milvus Cloud console'dan şu bilgileri almanız gerekiyor:

### 1. Public Endpoint (Host)
- **Nerede bulunur:** Milvus Cloud Console > Cluster Details > Connection Info
- **Format:** `xxx.gcp-us-west1.vectordb.zillizcloud.com` veya benzeri
- **Örnek:** `in01-abc123.gcp-us-west1.vectordb.zillizcloud.com`

### 2. Port
- **Genellikle:** `443` (HTTPS) veya `19530`
- Cloud cluster'lar için genellikle `443` kullanılır

### 3. API Key (Token)
- **Nerede bulunur:** Milvus Cloud Console > API Keys > Create API Key
- **Önemli:** API key oluşturduktan sonra bir daha gösterilmez, güvenli bir yerde saklayın!
- **Format:** Uzun bir string (örn: `db_admin:xxxxx...`)

### 4. Username & Password (Opsiyonel)
- Bazı Milvus versiyonlarında username/password kullanılabilir
- Genellikle API key tercih edilir

## 🔧 Yapılandırma

### .env Dosyasına Ekleme

`.env` dosyanıza şu bilgileri ekleyin:

```env
# Milvus Cloud Configuration
MILVUS_USE_CLOUD=true
MILVUS_HOST=xxx.gcp-us-west1.vectordb.zillizcloud.com
MILVUS_PORT=443
MILVUS_API_KEY=db_admin:your_api_key_here
MILVUS_COLLECTION_NAME=medical_knowledge_base

# Eğer username/password kullanıyorsanız:
# MILVUS_USER=your_username
# MILVUS_PASSWORD=your_password
```

### Örnek .env Dosyası

```env
# Milvus Cloud Free Cluster
MILVUS_USE_CLOUD=true
MILVUS_HOST=in01-abc123.gcp-us-west1.vectordb.zillizcloud.com
MILVUS_PORT=443
MILVUS_API_KEY=db_admin:AbCdEf1234567890XyZ
MILVUS_COLLECTION_NAME=medical_knowledge_base

# Embedding Model
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2

# GraphRAG Settings
GRAPH_SIMILARITY_THRESHOLD=0.7
GRAPH_MAX_DEPTH=2
RETRIEVAL_TOP_K=5

# LLM Configuration
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL=gemini-2.5-flash
```

## 🔍 Milvus Cloud Console'dan Bilgileri Alma

### Adım 1: Cluster Details Sayfasına Gidin
1. Milvus Cloud Console'a giriş yapın
2. Cluster'ınızı seçin
3. "Connection Info" veya "Details" sekmesine gidin

### Adım 2: Public Endpoint'i Kopyalayın
- "Public Endpoint" veya "Host" bilgisini kopyalayın
- Bu genellikle şu formatta olur: `xxx.region.vectordb.zillizcloud.com`

### Adım 3: API Key Oluşturun
1. Console'da "API Keys" veya "Security" sekmesine gidin
2. "Create API Key" butonuna tıklayın
3. Key'i kopyalayın ve `.env` dosyasına ekleyin
4. **ÖNEMLİ:** Key'i bir daha göremeyeceğiniz için güvenli bir yerde saklayın!

### Adım 4: Port Bilgisini Kontrol Edin
- Genellikle `443` (HTTPS) kullanılır
- Bazı durumlarda `19530` olabilir
- Connection Info sayfasında belirtilir

## ✅ Bağlantı Testi

Bağlantıyı test etmek için:

```python
from pymilvus import connections, utility

# Connect to Milvus Cloud
connections.connect(
    alias="default",
    host="your-endpoint.vectordb.zillizcloud.com",
    port=443,
    token="db_admin:your_api_key"
)

# List collections
collections = utility.list_collections()
print(f"Collections: {collections}")
```

## 🚀 GraphRAG Build

Milvus Cloud'a bağlandıktan sonra GraphRAG'ı build edin:

```bash
python build_graphrag.py
```

Bu script:
1. Milvus Cloud'a bağlanır
2. Collection oluşturur
3. Dataset'i yükler ve işler
4. GraphRAG yapısını oluşturur

## 🔒 Güvenlik Notları

1. **API Key'i Güvenli Tutun**
   - `.env` dosyasını git'e commit etmeyin
   - `.gitignore` dosyanıza `.env` ekleyin
   - Production'da environment variables kullanın

2. **Rate Limits**
   - Free cluster'larda rate limit olabilir
   - Büyük dataset'ler için batch processing kullanın

3. **Connection Pooling**
   - Milvus Cloud otomatik connection pooling yapar
   - Her request'te yeni connection açmaya gerek yok

## 🐛 Troubleshooting

### Bağlantı Hatası: "Connection refused"
**Çözüm:**
- Port'un doğru olduğundan emin olun (genellikle 443)
- Firewall'ın 443 portunu engellemediğinden emin olun
- Public endpoint'in doğru olduğunu kontrol edin

### Authentication Hatası: "Invalid token"
**Çözüm:**
- API key'in doğru kopyalandığından emin olun
- API key'in expire olmadığını kontrol edin
- Console'dan yeni bir API key oluşturun

### Collection Bulunamadı Hatası
**Çözüm:**
- Collection'ın oluşturulduğundan emin olun
- Collection name'in doğru olduğunu kontrol edin
- `build_graphrag.py` script'ini çalıştırın

### Timeout Hatası
**Çözüm:**
- Network bağlantınızı kontrol edin
- Free cluster'da rate limit'e takılmış olabilirsiniz
- Batch size'ı azaltın

## 📊 Milvus Cloud Free Tier Limitleri

Free cluster genellikle şu limitlere sahiptir:
- **Storage:** ~5GB
- **Collections:** Sınırlı sayıda
- **Rate Limit:** Dakikada belirli sayıda request
- **Region:** Belirli bir region'da

Bu limitler için Milvus Cloud dokümantasyonunu kontrol edin.

## 🔄 Local Milvus'tan Cloud'a Geçiş

Eğer local Milvus kullanıyordunuz ve cloud'a geçiyorsanız:

1. `.env` dosyasını güncelleyin:
   ```env
   MILVUS_USE_CLOUD=true
   MILVUS_HOST=your-cloud-endpoint
   MILVUS_PORT=443
   MILVUS_API_KEY=your_api_key
   ```

2. Collection'ı yeniden oluşturun:
   ```bash
   python build_graphrag.py
   ```

3. Data'yı yeniden yükleyin (local'den export edip cloud'a import edebilirsiniz)

## 📚 İlgili Dosyalar

- `config.py` - Milvus configuration
- `context_integration.py` - Milvus connection logic
- `graphrag_builder.py` - GraphRAG build with Milvus Cloud
- `build_graphrag.py` - Build script

## 💡 İpuçları

1. **API Key Rotation:** Düzenli olarak API key'leri rotate edin
2. **Monitoring:** Milvus Cloud console'dan cluster'ınızı monitor edin
3. **Backup:** Önemli data için backup stratejisi oluşturun
4. **Optimization:** Free tier'da batch size'ı optimize edin
