# Milvus Cloud Bağlantı Sorunları ve Çözümleri

## ❌ Hata: "illegal connection params or server unavailable"

Bu hata genellikle şu nedenlerden kaynaklanır:

### 1. Port String Olarak Gönderiliyor
**Sorun:** `.env` dosyasından okunan port string olarak geliyor, integer olmalı.

**Çözüm:** ✅ Düzeltildi - `config.py` dosyasında port artık integer'a çevriliyor.

### 2. API Key Eksik veya Yanlış
**Sorun:** `.env` dosyasında `MILVUS_API_KEY` eksik veya yanlış.

**Kontrol:**
```bash
# .env dosyanızı kontrol edin
cat .env | grep MILVUS_API_KEY
```

**Çözüm:**
1. Zilliz Cloud Console'a gidin
2. "API Keys" sekmesine tıklayın
3. Yeni API Key oluşturun
4. Key'i kopyalayın (bir daha gösterilmez!)
5. `.env` dosyasına ekleyin:
   ```env
   MILVUS_API_KEY=db_admin:your_full_api_key_here
   ```

### 3. Host Formatı Yanlış
**Sorun:** Public Endpoint'te `https://` var veya yanlış format.

**Doğru Format:**
```env
# ✅ DOĞRU
MILVUS_HOST=in03-0c05f97230ebf99.serverless.aws-eu-central-1.cloud.zilliz.com

# ❌ YANLIŞ
MILVUS_HOST=https://in03-0c05f97230ebf99.serverless.aws-eu-central-1.cloud.zilliz.com
MILVUS_HOST=in03-0c05f97230ebf99.serverless.aws-eu-central-1.cloud.zilliz.com:443
```

### 4. Serverless Milvus için Özel Durumlar

**Serverless Milvus** için bazı ek kontroller:

1. **Port mutlaka 443 olmalı:**
   ```env
   MILVUS_PORT=443
   ```

2. **API Key mutlaka olmalı:**
   ```env
   MILVUS_USE_CLOUD=true
   MILVUS_API_KEY=db_admin:your_key
   ```

3. **Host formatı:**
   - `serverless` kelimesi içeren endpoint'ler için özel bir format gerekebilir
   - Endpoint'i olduğu gibi kopyalayın (https:// olmadan)

## 🔍 Debug Adımları

### Adım 1: .env Dosyasını Kontrol Edin

```bash
# Windows PowerShell
Get-Content .env

# Linux/Mac
cat .env
```

Şunların olduğundan emin olun:
```env
MILVUS_USE_CLOUD=true
MILVUS_HOST=in03-0c05f97230ebf99.serverless.aws-eu-central-1.cloud.zilliz.com
MILVUS_PORT=443
MILVUS_API_KEY=db_admin:your_full_api_key
MILVUS_COLLECTION_NAME=medical_knowledge_base
```

### Adım 2: Test Connection Script'ini Çalıştırın

```bash
python test_connection.py
```

Bu script size şunları gösterecek:
- Host, Port, API Key değerlerini
- Bağlantı durumunu
- Hata mesajlarını

### Adım 3: Manuel Bağlantı Testi

Python'da direkt test edin:

```python
from pymilvus import connections

try:
    connections.connect(
        alias="default",
        host="in03-0c05f97230ebf99.serverless.aws-eu-central-1.cloud.zilliz.com",
        port=443,
        token="db_admin:your_api_key_here"
    )
    print("✅ Bağlantı başarılı!")
except Exception as e:
    print(f"❌ Hata: {e}")
```

## ✅ Düzeltmeler Yapıldı

1. ✅ Port artık integer'a çevriliyor (`config.py`)
2. ✅ Bağlantı kodlarında port integer kontrolü eklendi
3. ✅ Daha detaylı hata mesajları eklendi
4. ✅ API key kontrolü eklendi

## 🚀 Tekrar Deneyin

Düzeltmelerden sonra:

```bash
# 1. Önce test edin
python test_connection.py

# 2. Test başarılıysa build edin
python build_graphrag.py
```

## 📋 Kontrol Listesi

- [ ] `.env` dosyasında `MILVUS_USE_CLOUD=true`
- [ ] `.env` dosyasında `MILVUS_HOST` doğru (https:// yok)
- [ ] `.env` dosyasında `MILVUS_PORT=443` (integer)
- [ ] `.env` dosyasında `MILVUS_API_KEY` var ve doğru
- [ ] API Key'in tamamını kopyaladınız (`db_admin:` ile başlayan)
- [ ] `python test_connection.py` çalıştırdınız
- [ ] Test başarılı oldu

## 💡 İpuçları

1. **API Key Formatı:**
   - `db_admin:` ile başlamalı
   - Çok uzun bir string (50+ karakter)
   - Boşluk içermemeli

2. **Host Formatı:**
   - `https://` olmamalı
   - `:443` olmamalı
   - Sadece domain adı

3. **Port:**
   - Serverless için mutlaka `443`
   - String değil, integer olmalı

4. **Environment Variables:**
   - `.env` dosyasını değiştirdikten sonra Python script'ini yeniden başlatın
   - IDE'yi yeniden başlatmanız gerekebilir
