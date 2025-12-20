# DeepSeek v3.1 API Kurulum Rehberi

Bu rehber, DeepSeek v3.1 API'sini projeye entegre etmek için gerekli adımları açıklar.

## 📋 İçindekiler

1. [API Key Alma](#api-key-alma)
2. [Environment Variables Yapılandırması](#environment-variables-yapılandırması)
3. [İki Kullanım Modu](#iki-kullanım-modu)
4. [Test Etme](#test-etme)
5. [Sorun Giderme](#sorun-giderme)

---

## 🔑 API Key Alma

### Adım 1: DeepSeek Platform'a Kaydolun

1. [DeepSeek Platform](https://platform.deepseek.com) adresine gidin
2. Hesap oluşturun veya giriş yapın

### Adım 2: API Key Oluşturun

1. Platform'da **"API Keys"** veya **"API Anahtarları"** sekmesine gidin
2. **"Create API Key"** veya **"Yeni API Anahtarı"** butonuna tıklayın
3. API key'inizi kopyalayın ve güvenli bir yerde saklayın

**⚠️ ÖNEMLİ:** API key'i bir daha göremeyeceksiniz! Hemen kopyalayın.

---

## ⚙️ Environment Variables Yapılandırması

### Seçenek 1: Direct DeepSeek API (Önerilen)

Direct DeepSeek API kullanmak için `.env` dosyanıza şu değişkenleri ekleyin:

```env
# DeepSeek API Configuration
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat
DEEPSEEK_USE_DIRECT_API=true

# LLM Configuration
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048
```

### Seçenek 2: Huawei ModelArts Üzerinden

Huawei ModelArts üzerinden DeepSeek kullanmak için:

```env
# DeepSeek API Configuration
DEEPSEEK_API_KEY=your_modelarts_api_key_here
DEEPSEEK_USE_DIRECT_API=false

# ModelArts Configuration
MODELARTS_ENDPOINT=https://modelarts.ap-southeast-1.myhuaweicloud.com
MODELARTS_PROJECT_ID=your_project_id_here
MODELARTS_MODEL_NAME=deepseek-v3.1

# LLM Configuration
LLM_MODEL=deepseek-v3.1
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=2048
```

---

## 🔄 İki Kullanım Modu

### Mod 1: Direct DeepSeek API

**Avantajlar:**
- ✅ Daha basit kurulum
- ✅ Doğrudan DeepSeek API'sine erişim
- ✅ Daha hızlı yanıt süreleri
- ✅ OpenAI-compatible format

**Yapılandırma:**
```env
DEEPSEEK_USE_DIRECT_API=true
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat
```

**Endpoint Format:**
```
POST https://api.deepseek.com/v1/chat/completions
Authorization: Bearer {DEEPSEEK_API_KEY}
```

### Mod 2: Huawei ModelArts

**Avantajlar:**
- ✅ Huawei Cloud entegrasyonu
- ✅ Ascend chip hızlandırma
- ✅ Enterprise-grade güvenlik

**Yapılandırma:**
```env
DEEPSEEK_USE_DIRECT_API=false
MODELARTS_ENDPOINT=https://modelarts.{region}.myhuaweicloud.com
MODELARTS_MODEL_NAME=deepseek-v3.1
```

**Endpoint Format:**
```
POST {MODELARTS_ENDPOINT}/v1/chat/completions
X-Auth-Token: {DEEPSEEK_API_KEY}
```

---

## 🧪 Test Etme

### Python ile Test

```python
from modelarts_client import ModelArtsClient

# Initialize client
client = ModelArtsClient()

# Check if available
if client.is_available():
    print("✅ DeepSeek API client is ready")
    
    # Test API call
    response = client.invoke_deepseek(
        prompt="What is artificial intelligence?",
        temperature=0.7,
        max_tokens=100
    )
    
    if response:
        text = client.extract_response_text(response)
        print(f"Response: {text}")
    else:
        print("❌ API call failed")
else:
    print("❌ DeepSeek API client not configured")
```

### Streamlit App ile Test

1. `.env` dosyanızı yapılandırın
2. Uygulamayı başlatın:
   ```bash
   streamlit run app.py
   ```
3. Chat sayfasına gidin ve bir soru sorun
4. Console loglarında DeepSeek API çağrılarını kontrol edin

---

## 📝 API Request Format

### Direct DeepSeek API

```json
{
  "model": "deepseek-chat",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is AI?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

### Response Format

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "AI stands for Artificial Intelligence..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

---

## 🔧 Sorun Giderme

### Problem 1: "DeepSeek API client not enabled"

**Çözüm:**
- `.env` dosyasında `DEEPSEEK_API_KEY` değişkeninin doğru ayarlandığından emin olun
- API key'in geçerli olduğunu kontrol edin

### Problem 2: "401 Unauthorized"

**Çözüm:**
- API key'in doğru olduğundan emin olun
- Direct API kullanıyorsanız `DEEPSEEK_USE_DIRECT_API=true` olduğundan emin olun
- ModelArts kullanıyorsanız `MODELARTS_ENDPOINT` ve `MODELARTS_PROJECT_ID` doğru olmalı

### Problem 3: "Model not found"

**Çözüm:**
- `DEEPSEEK_MODEL_NAME` veya `MODELARTS_MODEL_NAME` değerini kontrol edin
- Desteklenen modeller: `deepseek-chat`, `deepseek-v3.1`
- Direct API için: `deepseek-chat` kullanın
- ModelArts için: `deepseek-v3.1` kullanın

### Problem 4: "Connection timeout"

**Çözüm:**
- İnternet bağlantınızı kontrol edin
- Firewall ayarlarını kontrol edin
- ModelArts endpoint'in erişilebilir olduğundan emin olun

### Problem 5: Response extraction failed

**Çözüm:**
- API response formatını kontrol edin
- Log dosyalarında hata mesajlarını kontrol edin
- `extract_response_text()` metodunun doğru çalıştığından emin olun

---

## 📊 Model Karşılaştırması

| Model | Endpoint | Model Name | Özellikler |
|-------|----------|------------|------------|
| deepseek-chat | Direct API | `deepseek-chat` | Genel amaçlı, OpenAI-compatible |
| deepseek-v3.1 | ModelArts | `deepseek-v3.1` | Enterprise, Ascend acceleration |

---

## 🔐 Güvenlik Notları

1. **API Key Güvenliği:**
   - API key'inizi asla public repository'lere commit etmeyin
   - `.env` dosyasını `.gitignore`'a ekleyin
   - Production'da environment variables kullanın

2. **Rate Limiting:**
   - DeepSeek API rate limit'leri vardır
   - Çok fazla istek göndermemeye dikkat edin
   - Error handling ekleyin

3. **HTTPS:**
   - Tüm API çağrıları HTTPS üzerinden yapılır
   - Certificate validation otomatik yapılır

---

## 📚 Ek Kaynaklar

- [DeepSeek Platform](https://platform.deepseek.com)
- [DeepSeek API Documentation](https://api-docs.deepseek.com)
- [Huawei ModelArts Documentation](https://support.huaweicloud.com/modelarts/)

---

## ✅ Kurulum Kontrol Listesi

- [ ] DeepSeek Platform hesabı oluşturuldu
- [ ] API key alındı ve kopyalandı
- [ ] `.env` dosyası oluşturuldu
- [ ] `DEEPSEEK_API_KEY` ayarlandı
- [ ] `DEEPSEEK_USE_DIRECT_API` seçildi (true/false)
- [ ] ModelArts kullanılıyorsa `MODELARTS_ENDPOINT` ayarlandı
- [ ] `LLM_MODEL` değişkeni doğru model adıyla ayarlandı
- [ ] Test scripti çalıştırıldı
- [ ] Streamlit app'te test edildi

---

**Son Güncelleme:** 2024
**Versiyon:** 1.0
