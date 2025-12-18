# GraphRAG Build Sonrası Adımlar

GraphRAG build'i başarıyla tamamlandı! Şimdi sistemi test edip kullanmaya başlayabilirsiniz.

## ✅ Tamamlanan İşlemler

- ✅ Dataset yüklendi (19,704 Q&A çifti)
- ✅ Embedding'ler oluşturuldu
- ✅ Graph yapısı oluşturuldu
- ✅ Milvus'a kaydedildi
- ✅ Collection hazır

## 🚀 Şimdi Yapılacaklar

### Adım 1: Bağlantıyı Test Edin

Collection'ın doğru yüklendiğini kontrol edin:

```bash
python test_connection.py
```

**Beklenen çıktı:**
```
✅ Connected to Milvus at ...
✅ Available collections: ['medical_knowledge_base']
✅ Collection 'medical_knowledge_base' exists!
✅ Collection has 19704 entities
✅ Collection schema:
   - id: VARCHAR
   - question: VARCHAR
   - response: VARCHAR
   ...
```

### Adım 2: RAG Service'i Test Edin

Basit bir Python script ile test edin:

**`test_rag.py` dosyası oluşturun:**

```python
"""Test RAG Service"""
from rag_service import RAGService

# Initialize RAG service
rag = RAGService()

# Test query
query = "What is the treatment for pneumonia?"
print(f"Query: {query}\n")
print("=" * 60)

# Process query
result = rag.process_query(query)

# Display results
print("\n📋 Response:")
print(result["response"])

print("\n📚 Sources:")
for i, source in enumerate(result["sources"][:3], 1):
    print(f"\n[{i}] {source[:200]}...")

print("\n✅ RAG Service test completed!")
```

**Çalıştırın:**
```bash
python test_rag.py
```

### Adım 3: Streamlit Uygulamasını Başlatın

Web arayüzü ile kullanmak için:

```bash
streamlit run app.py
```

Tarayıcınızda otomatik açılacak: `http://localhost:8501`

### Adım 4: İlk Query'yi Test Edin

Streamlit uygulamasında veya Python script'inde şu soruları deneyin:

**Örnek Sorular:**
1. "What is pneumonia?"
2. "What are the symptoms of diabetes?"
3. "How is hypertension treated?"
4. "What causes chest pain?"

## 📊 Sistem Durumu Kontrolü

### Collection Bilgilerini Kontrol Edin

```python
from pymilvus import Collection, utility
from config import MILVUS_COLLECTION_NAME, MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY, MILVUS_USE_CLOUD
from pymilvus import connections

# Connect
port = int(MILVUS_PORT) if isinstance(MILVUS_PORT, str) else MILVUS_PORT
connection_params = {
    "alias": "default",
    "host": MILVUS_HOST,
    "port": port
}
if MILVUS_USE_CLOUD and MILVUS_API_KEY:
    connection_params["token"] = MILVUS_API_KEY
    if "serverless" in MILVUS_HOST.lower():
        connection_params["secure"] = True

connections.connect(**connection_params)

# Check collection
collection = Collection(MILVUS_COLLECTION_NAME)
collection.load()

print(f"✅ Collection: {MILVUS_COLLECTION_NAME}")
print(f"✅ Entities: {collection.num_entities}")
print(f"✅ Schema fields: {len(collection.schema.fields)}")
```

## 🎯 Kullanım Senaryoları

### Senaryo 1: Python Script ile Kullanım

```python
from rag_service import RAGService

rag = RAGService()
result = rag.process_query("What is the diagnosis for chest pain?")
print(result["response"])
```

### Senaryo 2: Streamlit Web Arayüzü

```bash
streamlit run app.py
```

Web arayüzünde:
1. Medical soru yazın
2. "Submit" butonuna tıklayın
3. GraphRAG'dan gelen cevabı görün
4. Kaynakları inceleyin

### Senaryo 3: API Endpoint (Gelecekte)

REST API ekleyebilirsiniz (FastAPI/Flask)

## 🔍 Sistem Özellikleri

### GraphRAG Özellikleri

1. **Semantic Search:** Query'ye en benzer Q&A çiftlerini bulur
2. **Graph Traversal:** İlgili Q&A çiftlerini graph üzerinden gezinir
3. **Context Integration:** Bulunan bilgileri birleştirir
4. **LLM Response:** Context ile birlikte cevap üretir

### Performans

- **19,704 Q&A çifti** Milvus'ta hazır
- **Graph edges** semantic similarity ile oluşturuldu
- **Query response time:** ~1-3 saniye (GPU ile embedding)
- **Retrieval:** Top 5 Q&A çifti + graph traversal

## 📝 Örnek Test Queries

### Basit Sorular:
- "What is diabetes?"
- "Explain hypertension"
- "What causes fever?"

### Karmaşık Sorular:
- "A patient presents with chest pain and shortness of breath. What could be the diagnosis?"
- "What are the treatment options for pneumonia in elderly patients?"
- "What is the relationship between diabetes and heart disease?"

## 🐛 Sorun Giderme

### Hata: "Collection not found"

**Çözüm:**
```bash
python test_connection.py
```

Collection'ın yüklü olduğundan emin olun.

### Hata: "No response generated"

**Sebep:** LLM API key eksik veya yanlış

**Çözüm:**
`.env` dosyasında `GOOGLE_API_KEY` olduğundan emin olun.

### Hata: "Empty context"

**Sebep:** Query embedding'i ile eşleşen Q&A bulunamadı

**Çözüm:**
- Query'yi daha spesifik yapın
- Medical terimler kullanın
- Benzer soruları deneyin

## 🎉 Başarı!

GraphRAG sistemi hazır ve çalışıyor! Artık:

1. ✅ Medical sorular sorabilirsiniz
2. ✅ GraphRAG'dan cevaplar alabilirsiniz
3. ✅ Kaynak Q&A çiftlerini görebilirsiniz
4. ✅ Web arayüzü ile kullanabilirsiniz

## 📚 Sonraki Geliştirmeler (Opsiyonel)

1. **Fine-tuning:** Daha iyi sonuçlar için model fine-tuning
2. **Caching:** Sık sorulan sorular için cache
3. **Analytics:** Query analytics ve monitoring
4. **Multi-language:** Türkçe soru desteği
5. **API:** REST API endpoint ekleme

## 🚀 Hızlı Başlangıç

```bash
# 1. Test connection
python test_connection.py

# 2. Test RAG service
python test_rag.py

# 3. Start web app
streamlit run app.py
```

**Hepsi bu kadar! Sistem kullanıma hazır! 🎉**
