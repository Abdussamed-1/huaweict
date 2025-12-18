# Zilliz Cloud Collection Setup Guide

Bu dokümantasyon, Zilliz Cloud (Milvus Cloud) içinde collection oluştururken yapmanız gereken adımları açıklar.

## ⚠️ ÖNEMLİ: Önce Ödeme Sorununu Çözün

Ekranda görünen "Your card was declined" hatasını çözmeniz gerekiyor:
1. Sağ üstteki "Add Payment Method" butonuna tıklayın
2. Geçerli bir kredi kartı ekleyin
3. Free tier için bile ödeme yöntemi gereklidir (ücret alınmaz ama kayıt gerekir)

## 📋 Collection Schema Oluşturma Adımları

### Adım 1: Collection Bilgileri

**Create Collection** bölümünde:
- ✅ **Collection Name:** `medical_knowledge_base` (zaten doğru)
- ✅ **Description:** `medical_knowledge_base` (zaten doğru)

### Adım 2: Schema Field'larını Düzenle

**Create Schema** bölümünde şu değişiklikleri yapın:

#### ❌ Mevcut `primary_key` Field'ını SİLİN

1. `primary_key` field'ının yanındaki çöp kutusu ikonuna tıklayın
2. Bu field'ı silin (kodunuzda `id` VARCHAR kullanıyor)

#### ✅ Yeni Field'ları Ekleyin

"+ Field" butonuna tıklayarak şu field'ları sırayla ekleyin:

##### 1. `id` Field (Primary Key)
- **Field Name:** `id`
- **Field Type:** `VARCHAR`
- **Max Length:** `100`
- **Primary Key:** ✅ İşaretleyin (checkbox)
- **Auto ID:** ❌ Kapatın (checkbox'ı kaldırın)

##### 2. `question` Field
- **Field Name:** `question`
- **Field Type:** `VARCHAR`
- **Max Length:** `5000`
- **Primary Key:** ❌
- **Auto ID:** ❌

##### 3. `response` Field
- **Field Name:** `response`
- **Field Type:** `VARCHAR`
- **Max Length:** `10000`
- **Primary Key:** ❌
- **Auto ID:** ❌

##### 4. `question_embedding` Field
- **Field Name:** `question_embedding`
- **Field Type:** `FLOAT_VECTOR`
- **Dimension:** `768` ⚠️ ÇOK ÖNEMLİ!
- **Primary Key:** ❌
- **Auto ID:** ❌

##### 5. `response_embedding` Field
- **Field Name:** `response_embedding`
- **Field Type:** `FLOAT_VECTOR`
- **Dimension:** `768` ⚠️ ÇOK ÖNEMLİ!
- **Primary Key:** ❌
- **Auto ID:** ❌

##### 6. `combined_embedding` Field (EN ÖNEMLİSİ!)
- **Field Name:** `combined_embedding`
- **Field Type:** `FLOAT_VECTOR`
- **Dimension:** `768` ⚠️ ÇOK ÖNEMLİ!
- **Primary Key:** ❌
- **Auto ID:** ❌
- **Not:** Bu field GraphRAG'da similarity search için kullanılacak

##### 7. `metadata` Field
- **Field Name:** `metadata`
- **Field Type:** `JSON`
- **Primary Key:** ❌
- **Auto ID:** ❌

##### 8. `related_nodes` Field
- **Field Name:** `related_nodes`
- **Field Type:** `JSON`
- **Primary Key:** ❌
- **Auto ID:** ❌

#### ⚙️ Dynamic Field Ayarı

- **Dynamic Field:** ✅ Açık bırakabilirsiniz (opsiyonel, ama gerekli değil)

### Adım 3: Index Ayarları

**Create Index** bölümünde:

1. "Edit Index" butonuna tıklayın
2. `combined_embedding` field'ını seçin
3. Şu ayarları yapın:
   - **Index Type:** `IVF_FLAT`
   - **Metric Type:** `COSINE`
   - **nlist:** `1024`
4. "Save" butonuna tıklayın

**Not:** Diğer vector field'lar (`question_embedding`, `response_embedding`) için AUTOINDEX yeterli olacaktır.

### Adım 4: Collection'ı Oluşturun

1. Tüm field'ları ekledikten sonra
2. Index ayarlarını yaptıktan sonra
3. "Create" butonuna tıklayın

## ✅ Kontrol Listesi

Collection oluşturmadan önce kontrol edin:

- [ ] Ödeme yöntemi eklendi (card declined hatası çözüldü)
- [ ] `primary_key` (INT64) field'ı silindi
- [ ] `id` (VARCHAR, Primary Key) field'ı eklendi
- [ ] `question` (VARCHAR, 5000) field'ı eklendi
- [ ] `response` (VARCHAR, 10000) field'ı eklendi
- [ ] `question_embedding` (FLOAT_VECTOR, 768) field'ı eklendi
- [ ] `response_embedding` (FLOAT_VECTOR, 768) field'ı eklendi
- [ ] `combined_embedding` (FLOAT_VECTOR, 768) field'ı eklendi
- [ ] `metadata` (JSON) field'ı eklendi
- [ ] `related_nodes` (JSON) field'ı eklendi
- [ ] `combined_embedding` için index ayarlandı (IVF_FLAT, COSINE, nlist=1024)

## 📊 Field Özeti

| Field Name | Type | Max Length/Dimension | Primary Key | Notes |
|------------|------|---------------------|-------------|-------|
| `id` | VARCHAR | 100 | ✅ Yes | Primary key |
| `question` | VARCHAR | 5000 | ❌ No | Question text |
| `response` | VARCHAR | 10000 | ❌ No | Response text |
| `question_embedding` | FLOAT_VECTOR | 768 | ❌ No | Question embeddings |
| `response_embedding` | FLOAT_VECTOR | 768 | ❌ No | Response embeddings |
| `combined_embedding` | FLOAT_VECTOR | 768 | ❌ No | Combined embeddings (indexed) |
| `metadata` | JSON | - | ❌ No | Additional metadata |
| `related_nodes` | JSON | - | ❌ No | Related node IDs |

## 🔍 Dimension Neden 768?

Kodunuzda `sentence-transformers/all-mpnet-base-v2` modeli kullanılıyor:
- Bu model **768 boyutlu** embedding'ler üretir
- Tüm FLOAT_VECTOR field'ları için dimension **768** olmalıdır
- Yanlış dimension collection oluşturmayı engeller veya data insert sırasında hata verir

## 🚀 Collection Oluşturduktan Sonra

Collection başarıyla oluşturulduktan sonra:

1. **Connection Info'yu Alın:**
   - Public Endpoint'i kopyalayın
   - Port bilgisini not edin (genellikle 443)

2. **API Key Oluşturun:**
   - Console'da "API Keys" sekmesine gidin
   - "Create API Key" butonuna tıklayın
   - Key'i kopyalayın ve `.env` dosyanıza ekleyin

3. **Python Script'ini Çalıştırın:**
   ```bash
   python build_graphrag.py
   ```

## ⚠️ Yaygın Hatalar ve Çözümleri

### Hata: "Dimension mismatch"
**Sebep:** Vector field'ların dimension'ı yanlış
**Çözüm:** Tüm FLOAT_VECTOR field'ları için dimension'ı 768 yapın

### Hata: "Primary key field not found"
**Sebep:** `primary_key` field'ı silinmiş ama `id` field'ı primary key olarak işaretlenmemiş
**Çözüm:** `id` field'ını primary key olarak işaretleyin

### Hata: "Collection creation failed"
**Sebep:** Ödeme yöntemi sorunu veya eksik field
**Çözüm:** Önce ödeme yöntemini ekleyin, sonra tüm field'ları kontrol edin

### Hata: "Index creation failed"
**Sebep:** Index parametreleri yanlış
**Çözüm:** `combined_embedding` için IVF_FLAT, COSINE, nlist=1024 kullanın

## 📝 Örnek Schema JSON (Referans)

Eğer API ile oluşturmak isterseniz:

```json
{
  "collection_name": "medical_knowledge_base",
  "description": "Medical Q&A GraphRAG Collection",
  "fields": [
    {
      "name": "id",
      "type": "VARCHAR",
      "max_length": 100,
      "is_primary": true,
      "auto_id": false
    },
    {
      "name": "question",
      "type": "VARCHAR",
      "max_length": 5000
    },
    {
      "name": "response",
      "type": "VARCHAR",
      "max_length": 10000
    },
    {
      "name": "question_embedding",
      "type": "FLOAT_VECTOR",
      "dim": 768
    },
    {
      "name": "response_embedding",
      "type": "FLOAT_VECTOR",
      "dim": 768
    },
    {
      "name": "combined_embedding",
      "type": "FLOAT_VECTOR",
      "dim": 768
    },
    {
      "name": "metadata",
      "type": "JSON"
    },
    {
      "name": "related_nodes",
      "type": "JSON"
    }
  ]
}
```

## 🎯 Sonraki Adımlar

Collection oluşturulduktan sonra:

1. ✅ `.env` dosyanızı güncelleyin (endpoint, port, API key)
2. ✅ `python build_graphrag.py` çalıştırın
3. ✅ Dataset yüklenecek ve GraphRAG yapısı oluşturulacak
4. ✅ RAG service'i kullanmaya başlayabilirsiniz
