# 🚀 Turkcell Fatura Asistanı - Backend Özeti

## 📋 Proje Durumu: **HAZIR** ✅

Backend API sunucusu tamamen hazır ve çalışır durumda. Frontend ekibi bu API'yi kullanarak fatura asistanı uygulamasını geliştirebilir.

## 🎯 Ana Özellikler

### ✅ Tamamlanan Özellikler
1. **Fatura Açıklama** - Her kalem için detaylı açıklama + LLM özeti
2. **Anomali Tespiti** - Z-score ve % artış bazlı anomali tespiti
3. **What-If Simülasyonu** - Plan değişikliği, ek paket, VAS iptali
4. **En İyi 3 Senaryo** - Otomatik en düşük maliyetli seçenekler
5. **LLM Entegrasyonu** - OpenAI ChatGPT ile akıllı özetler
6. **REST API** - FastAPI tabanlı, CORS destekli
7. **Mock Checkout** - Gerçek entegrasyon için hazır

## 🔧 Teknik Detaylar

### API Base URL
```
http://localhost:8000
```

### Ana Endpoint'ler
- `GET /health` - Sunucu durumu
- `GET /api/users` - Kullanıcı listesi
- `GET /api/bills/{user_id}` - Kullanıcı faturaları
- `POST /api/explain` - Fatura açıklama
- `POST /api/anomalies` - Anomali tespiti
- `POST /api/whatif` - What-if simülasyonu
- `GET /api/whatif/top3/{user_id}` - En iyi 3 senaryo
- `POST /api/checkout` - Mock checkout

### Engine'ler
1. **Data Prep Engine** - CSV verilerini işler
2. **Anomaly Engine** - Anomali tespiti yapar
3. **What-If Engine** - Simülasyon hesaplar
4. **LLM Client** - OpenAI ChatGPT entegrasyonu

## 🚀 Başlatma

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Veri özetlerini oluştur
python general_scripts/data_prep.py --data data --out artifacts

# 3. Sunucuyu başlat
python api_server.py

# 4. Test et
python test_api.py
```

## 📊 Veri Gereksinimleri

### Zorunlu CSV Dosyaları
- `users.csv` - Kullanıcı bilgileri
- `plans.csv` - Plan kataloğu
- `bill_headers.csv` - Fatura başlıkları
- `bill_items.csv` - Fatura kalemleri
- `usage_daily.csv` - Günlük kullanım
- `add_on_packs.csv` - Ek paketler

### Opsiyonel CSV Dosyaları
- `vas_catalog.csv` - VAS kataloğu
- `premium_sms_catalog.csv` - Premium SMS kataloğu

## 🔑 Konfigürasyon

### Ortam Değişkenleri (Opsiyonel)
```bash
# LLM için
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini

# API için
export API_HOST=0.0.0.0
export API_PORT=8000
```

## 🧪 Test

### Otomatik Test
```bash
python test_api.py
```

### Manuel Test
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/users
```

## 📁 Dosya Yapısı

```
turkcell_codenight/
├── api_server.py              # Ana FastAPI sunucusu
├── general_scripts/           # Engine'ler
│   ├── data_prep.py          # Veri hazırlama
│   ├── anomaly_engine.py     # Anomali tespiti
│   ├── whatif_engine.py      # What-if simülasyonu
│   └── llm_client.py         # LLM entegrasyonu
├── data/                     # CSV verileri
├── artifacts/                # İşlenmiş veriler
├── requirements.txt          # Bağımlılıklar
├── test_api.py              # API testi
├── llm_test.py              # LLM testi
└── backend_README.md         # Detaylı dokümantasyon
```

## 🎯 Frontend Entegrasyonu

### JavaScript Örneği
```javascript
const API_BASE = 'http://localhost:8000';

// Kullanıcı bilgilerini getir
async function getUser(userId) {
  const response = await fetch(`${API_BASE}/api/users/${userId}`);
  return await response.json();
}

// Faturayı açıkla
async function explainBill(billId) {
  const response = await fetch(`${API_BASE}/api/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bill_id: billId })
  });
  return await response.json();
}

// What-if simülasyonu
async function whatIfSimulation(userId, period, scenario) {
  const response = await fetch(`${API_BASE}/api/whatif`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      period: period,
      scenario: scenario
    })
  });
  return await response.json();
}
```

## 🔒 Güvenlik Notları

- CORS ayarları yapılandırılmış
- Production'da spesifik domain'ler belirtilmeli
- OpenAI API key güvenli şekilde saklanmalı
- Authentication eklenebilir

## 📞 Destek

- **Detaylı Dokümantasyon**: `backend_README.md`
- **API Testi**: `test_api.py`
- **LLM Testi**: `llm_test.py`
- **Örnek Kullanım**: README dosyalarında

## 🎉 Sonuç

Backend API sunucusu tamamen hazır ve test edilmiş durumda. Frontend ekibi bu API'yi kullanarak fatura asistanı uygulamasını geliştirebilir. Tüm endpoint'ler çalışır durumda ve dokümante edilmiş.

**Durum**: ✅ **PRODUCTION'A HAZIR**
