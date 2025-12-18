# ✅ Deployment Checklist - 100$ Kupon Deployment

Bu checklist'i deployment sırasında takip edin.

## 📋 Pre-Deployment Checklist

### 1. Huawei Cloud Hesap Hazırlığı
- [ ] Huawei Cloud hesabı aktif
- [ ] 100$ kupon tanımlı ve aktif
- [ ] Billing bilgileri doğru
- [ ] Region seçildi (ap-southeast-1 önerilir)

### 2. Credentials Hazırlığı
- [ ] Milvus Cloud (Zilliz) credentials hazır
  - [ ] MILVUS_HOST
  - [ ] MILVUS_API_KEY
  - [ ] MILVUS_COLLECTION_NAME
- [ ] Huawei Cloud OBS credentials hazır
  - [ ] OBS_ACCESS_KEY
  - [ ] OBS_SECRET_KEY
  - [ ] OBS_ENDPOINT
  - [ ] OBS_BUCKET_NAME
- [ ] Huawei Cloud ModelArts credentials hazır
  - [ ] MODELARTS_ENDPOINT
  - [ ] DEEPSEEK_API_KEY
- [ ] Google Gemini API key (fallback için, opsiyonel)
  - [ ] GOOGLE_API_KEY

### 3. Code Hazırlığı
- [ ] Repository clone edildi veya hazır
- [ ] .env.example dosyası mevcut
- [ ] Tüm dependencies requirements.txt'te listelenmiş
- [ ] Kod test edildi (local'de)

---

## 🚀 Deployment Checklist

### Phase 1: Infrastructure Setup

#### VPC Setup
- [ ] VPC oluşturuldu (huaweict-vpc-prod)
- [ ] CIDR: 10.0.0.0/16
- [ ] Public subnet oluşturuldu (10.0.1.0/24)
- [ ] Internet Gateway oluşturuldu ve VPC'ye bağlandı
- [ ] Route table yapılandırıldı

#### Security Group Setup
- [ ] Security group oluşturuldu (sg-app-public)
- [ ] SSH (22) - Sadece kendi IP'den
- [ ] HTTP (80) - 0.0.0.0/0
- [ ] HTTPS (443) - 0.0.0.0/0
- [ ] Custom TCP (8501) - 0.0.0.0/0 (Streamlit)
- [ ] Custom TCP (8080) - 0.0.0.0/0 (Health check)
- [ ] Outbound: All traffic

#### ECS Instance Setup
- [ ] ECS instance oluşturuldu
  - [ ] Instance type: s6.medium.2 (2 vCPU, 4GB RAM)
  - [ ] Image: Ubuntu 22.04 LTS Server
  - [ ] System disk: 40 GB SSD
  - [ ] Network: Public subnet
  - [ ] Security group: sg-app-public
- [ ] Elastic IP oluşturuldu ve instance'a atandı
- [ ] EIP bandwidth: 5 Mbps
- [ ] SSH ile bağlantı test edildi

#### OBS Setup
- [ ] OBS bucket oluşturuldu (medical-documents-prod)
- [ ] Region: ap-southeast-1
- [ ] Storage class: Standard
- [ ] Access: Private
- [ ] IAM policy yapılandırıldı (opsiyonel)

---

### Phase 2: Application Deployment

#### ECS Instance Preparation
- [ ] SSH ile instance'a bağlanıldı
- [ ] System update yapıldı (`sudo apt update && sudo apt upgrade -y`)
- [ ] Python 3.11 kuruldu
- [ ] Git kuruldu
- [ ] Application directory oluşturuldu (/opt/huaweict)

#### Code Deployment
- [ ] Repository clone edildi veya SCP ile upload edildi
- [ ] Virtual environment oluşturuldu
- [ ] Dependencies kuruldu (`pip install -r requirements.txt`)
- [ ] .env dosyası oluşturuldu ve dolduruldu
- [ ] .env dosyası doğrulandı (tüm credentials mevcut)

#### Service Configuration
- [ ] Systemd service dosyaları oluşturuldu
  - [ ] huaweict-streamlit.service
  - [ ] huaweict-health.service
- [ ] Services enable edildi
- [ ] Services başlatıldı
- [ ] Service status kontrol edildi

#### Firewall Configuration
- [ ] UFW firewall yapılandırıldı
- [ ] Port 22, 8501, 8080 açıldı
- [ ] Firewall aktif edildi

---

### Phase 3: Testing ve Validation

#### Health Check Test
- [ ] Health check endpoint test edildi
  ```bash
  curl http://<EIP>:8080/health
  ```
- [ ] Response: `{"status": "healthy", ...}`

#### Application Test
- [ ] Streamlit app erişilebilir
  ```bash
  curl http://<EIP>:8501
  ```
- [ ] Browser'da açıldı ve UI görünüyor

#### Milvus Connection Test
- [ ] Milvus connection test scripti çalıştırıldı
  ```bash
  python3 test_connection.py
  ```
- [ ] Connection başarılı
- [ ] Collection yüklü ve erişilebilir

#### OBS Connection Test
- [ ] OBS client test edildi
  ```python
  from obs_client import OBSClient
  client = OBSClient()
  client.list_documents()
  ```
- [ ] OBS bağlantısı başarılı

#### ModelArts API Test
- [ ] ModelArts API test edildi
  ```python
  from modelarts_client import ModelArtsClient
  client = ModelArtsClient()
  response = client.invoke_deepseek("Test prompt")
  ```
- [ ] API call başarılı

#### End-to-End Test
- [ ] Test query gönderildi
- [ ] RAG pipeline çalışıyor
- [ ] Response alındı ve doğru format
- [ ] Sources gösteriliyor
- [ ] GraphRAG metadata görünüyor

---

### Phase 4: Monitoring ve Optimization

#### Log Monitoring
- [ ] Streamlit logs kontrol edildi
  ```bash
  sudo journalctl -u huaweict-streamlit -f
  ```
- [ ] Health check logs kontrol edildi
  ```bash
  sudo journalctl -u huaweict-health -f
  ```
- [ ] Hata yok

#### Performance Check
- [ ] Response time < 5 saniye
- [ ] Memory usage < 3 GB (4GB RAM'den)
- [ ] CPU usage < 70% (normal load'da)

#### Cost Monitoring
- [ ] Huawei Cloud Console'da maliyet kontrol edildi
- [ ] Beklenen maliyet: ~$50-80/ay
- [ ] Budget alert ayarlandı (opsiyonel)

---

## 🔍 Troubleshooting Checklist

### ECS Instance'a Bağlanamıyorum
- [ ] Security group'da SSH (22) açık mı?
- [ ] EIP doğru mu?
- [ ] Instance running durumunda mı?
- [ ] Firewall (UFW) SSH'ı engelliyor mu?

### Application Başlamıyor
- [ ] .env dosyası doğru mu?
- [ ] Dependencies kurulu mu?
- [ ] Virtual environment aktif mi?
- [ ] Port 8501 kullanımda mı? (`sudo lsof -i :8501`)
- [ ] Logs kontrol edildi mi? (`sudo journalctl -u huaweict-streamlit`)

### Milvus Connection Error
- [ ] MILVUS_HOST doğru mu?
- [ ] MILVUS_API_KEY doğru mu?
- [ ] Network connectivity var mı? (`curl -v https://<milvus-host>:443`)
- [ ] Collection mevcut mu?

### ModelArts API Error
- [ ] MODELARTS_ENDPOINT doğru mu?
- [ ] DEEPSEEK_API_KEY doğru mu?
- [ ] API key aktif mi?
- [ ] Rate limit aşıldı mı?

### OBS Error
- [ ] OBS credentials doğru mu?
- [ ] Bucket mevcut mu?
- [ ] IAM permissions doğru mu?

---

## ✅ Final Checklist

- [ ] Tüm servisler çalışıyor
- [ ] Health check başarılı
- [ ] Application erişilebilir
- [ ] Tüm testler geçti
- [ ] Logs temiz (hata yok)
- [ ] Maliyet beklenen aralıkta
- [ ] Documentation güncel

---

## 📊 Success Metrics

- ✅ Application uptime > 95%
- ✅ Response time < 5 seconds
- ✅ Error rate < 1%
- ✅ Monthly cost < $100
- ✅ All services healthy

---

**Deployment Tamamlandı! 🎉**

Eğer tüm checklist'ler tamamlandıysa, deployment başarılıdır.

