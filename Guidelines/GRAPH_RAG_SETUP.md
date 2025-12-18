# GraphRAG Setup Guide

Bu dokümantasyon, medical Q&A dataset'inden GraphRAG yapısı oluşturma ve kullanma sürecini açıklar.

## 📋 Gereksinimler

1. **Python 3.8+**
2. **Milvus** (yerel veya cloud instance)
3. **Gerekli Python paketleri** (requirements.txt'ten yüklenir)

## 🚀 Kurulum Adımları

### 1. Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Milvus Bağlantısını Yapılandırın

`.env` dosyanızda veya environment variables'da şunları ayarlayın:

```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=medical_knowledge_base
EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
GRAPH_SIMILARITY_THRESHOLD=0.7
GRAPH_MAX_DEPTH=2
```

### 3. GraphRAG Yapısını Oluşturun

```bash
python build_graphrag.py
```

Bu script:
- HuggingFace'ten medical dataset'i yükler
- Question ve Response kolonlarını işler
- Embedding'leri oluşturur
- Semantic similarity ile graph edges oluşturur
- Milvus'a kaydeder

**Not:** İlk çalıştırmada dataset'i indirmek zaman alabilir. Test için `max_samples` parametresini kullanabilirsiniz.

## 📊 Dataset Bilgileri

- **Kaynak:** `FreedomIntelligence/medical-o1-reasoning-SFT`
- **Kullanılan Kolonlar:** `Question`, `Response`
- **Subset:** `en` (English)
- **Toplam Kayıt:** ~19,700 Q&A çifti

## 🔧 Yapılandırma Seçenekleri

### Embedding Model Seçimi

Medical domain için önerilen modeller:

1. **all-mpnet-base-v2** (Önerilen - 768 boyut)
   - Daha iyi semantic understanding
   - Medical text için daha uygun

2. **all-MiniLM-L6-v2** (Hızlı - 384 boyut)
   - Daha hızlı inference
   - Daha az bellek kullanımı

### Graph Parametreleri

- **GRAPH_SIMILARITY_THRESHOLD** (0.7): Edge oluşturma için minimum similarity
- **GRAPH_MAX_DEPTH** (2): Graph traversal maksimum derinliği
- **RETRIEVAL_TOP_K** (5): İlk retrieval'da kaç node alınacak

## 🎯 Kullanım

### RAG Service ile Kullanım

GraphRAG artık varsayılan retrieval yöntemidir. `rag_service.py` otomatik olarak GraphRAG kullanır:

```python
from rag_service import RAGService

rag = RAGService()
result = rag.process_query("What is the treatment for pneumonia?")
print(result["response"])
```

### GraphRAG Özellikleri

1. **Semantic Search**: Query embedding ile en benzer Q&A çiftlerini bulur
2. **Graph Traversal**: İlgili Q&A çiftlerini graph üzerinden gezinerek bulur
3. **Context Integration**: Bulunan Q&A çiftlerini context olarak birleştirir
4. **LLM Response**: Context ile birlikte LLM'e gönderir

## 📈 Performans İpuçları

1. **Batch Size**: `build_graphrag.py` içinde `batch_size` parametresini sistem belleğinize göre ayarlayın
2. **Similarity Threshold**: Daha yüksek threshold = daha az edge = daha hızlı traversal
3. **Max Depth**: Daha düşük depth = daha hızlı ama daha az context

## 🔍 Troubleshooting

### Milvus Bağlantı Hatası

```
Error connecting to Milvus
```

**Çözüm:** Milvus'un çalıştığından emin olun:
```bash
# Docker ile
docker ps | grep milvus

# Veya Milvus'u başlatın
docker run -d --name milvus -p 19530:19530 milvusdb/milvus:latest
```

### Embedding Model Yükleme Hatası

```
Error loading embedding model
```

**Çözüm:** İnternet bağlantınızı kontrol edin. Model ilk kullanımda indirilir.

### Memory Hatası

```
Out of memory
```

**Çözüm:** `batch_size` parametresini azaltın veya daha küçük bir `max_samples` kullanın.

## 📝 Notlar

- GraphRAG build işlemi dataset boyutuna bağlı olarak 30 dakika - 2 saat sürebilir
- İlk build'den sonra collection'ı yeniden oluşturmak isterseniz `drop_existing=True` kullanın
- GraphRAG, geleneksel vector RAG'dan daha iyi context sağlar çünkü semantic relationships kullanır

## 🎓 Nasıl Çalışır?

1. **Question Embedding**: Her question embedding'e dönüştürülür
2. **Response Embedding**: Her response embedding'e dönüştürülür
3. **Combined Embedding**: Question + Response birleştirilerek combined embedding oluşturulur
4. **Similarity Graph**: Combined embedding'ler arası similarity hesaplanır ve threshold üzerindeki çiftler edge olarak eklenir
5. **Query Time**: 
   - Query embedding oluşturulur
   - En benzer Q&A çiftleri bulunur (vector search)
   - Graph üzerinden related Q&A çiftleri bulunur (graph traversal)
   - Tüm context birleştirilir ve LLM'e gönderilir

## 📚 İlgili Dosyalar

- `dataset_loader.py`: Dataset yükleme ve işleme
- `graphrag_builder.py`: GraphRAG yapısı oluşturma
- `context_integration.py`: GraphRAG retrieval implementasyonu
- `rag_service.py`: Ana RAG service (GraphRAG kullanır)
- `build_graphrag.py`: GraphRAG build script'i
