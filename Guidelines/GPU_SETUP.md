# GPU Setup for GraphRAG Embeddings

Bu dokümantasyon, GPU ile embedding oluşturma için gerekli kurulum adımlarını açıklar.

## 🚀 GPU Desteği

GraphRAG builder artık GPU ile embedding oluşturmayı destekliyor. GPU kullanımı embedding oluşturma süresini **10-20x** hızlandırabilir.

## ✅ GPU Kontrolü

GPU'nuzun kullanılabilir olup olmadığını kontrol edin:

```bash
python check_gpu.py
```

Bu script şunları gösterir:
- PyTorch kurulumu
- GPU varlığı
- GPU bilgileri (model, memory, CUDA version)

## 🔧 Kurulum

### 1. PyTorch Kurulumu (CUDA ile)

**CUDA 11.8 için:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**CUDA 12.1 için:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**CPU-only (GPU yoksa):**
```bash
pip install torch
```

### 2. CUDA Toolkit Kurulumu

GPU kullanmak için NVIDIA CUDA Toolkit gerekir:
- **CUDA 11.8** veya **CUDA 12.1** önerilir
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) indirin

### 3. .env Dosyasını Güncelleyin

`.env` dosyanıza şunu ekleyin:

```env
# GPU Configuration
EMBEDDING_DEVICE=cuda    # GPU kullanmak için
# EMBEDDING_DEVICE=cpu   # CPU kullanmak için
# EMBEDDING_DEVICE=auto  # Otomatik algılama (önerilen)
```

## 🎯 Kullanım

### Otomatik GPU Algılama (Önerilen)

```env
EMBEDDING_DEVICE=auto
```

Bu ayar ile:
- GPU varsa otomatik GPU kullanılır
- GPU yoksa CPU'ya geçer
- Hiçbir şey yapmanıza gerek yok!

### Manuel GPU Seçimi

```env
EMBEDDING_DEVICE=cuda
```

**Not:** GPU yoksa CPU'ya düşer ve uyarı verir.

### CPU Kullanımı

```env
EMBEDDING_DEVICE=cpu
```

## 📊 Performans Karşılaştırması

### GPU ile (NVIDIA RTX 3090 örneği)
- **Batch size:** 200
- **19,700 Q&A çifti:** ~5-10 dakika
- **Memory kullanımı:** ~2-4 GB GPU RAM

### CPU ile
- **Batch size:** 50
- **19,700 Q&A çifti:** ~60-120 dakika
- **Memory kullanımı:** ~4-8 GB RAM

**Hızlanma:** GPU ile **10-20x** daha hızlı!

## 🔍 GPU Bilgilerini Kontrol Etme

### Python'da:

```python
import torch

print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}")
print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
```

### Script ile:

```bash
python check_gpu.py
```

## ⚙️ Batch Size Optimizasyonu

GPU kullanırken batch size otomatik olarak optimize edilir:

- **GPU:** Batch size = 200 (daha büyük batch = daha hızlı)
- **CPU:** Batch size = 50 (daha küçük batch = daha stabil)

Manuel olarak ayarlamak isterseniz:

```python
builder.build_graph_from_qa_pairs(
    qa_pairs=qa_pairs,
    similarity_threshold=0.7,
    batch_size=300  # GPU için daha büyük batch
)
```

## 🐛 Sorun Giderme

### Hata: "CUDA out of memory"

**Sebep:** GPU memory yetersiz

**Çözüm:**
1. Batch size'ı azaltın:
   ```python
   batch_size=100  # 200 yerine 100
   ```

2. GPU memory'yi temizleyin:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

### Hata: "CUDA not available"

**Sebep:** PyTorch CUDA desteği yok

**Çözüm:**
1. CUDA-enabled PyTorch kurun (yukarıdaki komutlar)
2. CUDA Toolkit'in kurulu olduğundan emin olun
3. `python check_gpu.py` ile kontrol edin

### Hata: "No module named 'torch'"

**Sebep:** PyTorch kurulu değil

**Çözüm:**
```bash
pip install torch
```

## 📝 Örnek Kullanım

### GPU ile Build:

```bash
# .env dosyasında
EMBEDDING_DEVICE=cuda

# Script'i çalıştır
python build_graphrag.py
```

Çıktı:
```
✅ GPU detected: NVIDIA GeForce RTX 3090
   CUDA Version: 11.8
   GPU Memory: 24.00 GB
🚀 Using GPU acceleration for embeddings
   GPU: NVIDIA GeForce RTX 3090
   Batch size: 200
Generated embeddings: 200/19704 (1.0%) [Batch 1/99]
...
```

## 💡 İpuçları

1. **GPU Memory:** Büyük dataset'ler için en az 8GB GPU RAM önerilir
2. **Batch Size:** GPU memory'nize göre batch size'ı artırabilirsiniz
3. **Monitoring:** GPU kullanımını `nvidia-smi` ile izleyebilirsiniz
4. **Multi-GPU:** Şu anda tek GPU destekleniyor

## 🎯 Sonuç

GPU desteği eklendi! Artık embedding'ler çok daha hızlı oluşturulacak.

**Hızlı Başlangıç:**
1. `python check_gpu.py` - GPU kontrolü
2. `.env` dosyasında `EMBEDDING_DEVICE=auto` ayarlayın
3. `python build_graphrag.py` - GPU ile build edin
