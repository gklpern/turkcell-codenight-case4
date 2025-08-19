# Turkcell Fatura Asistanı - API Server

Bu proje, Turkcell Fatura Asistanı'nın backend API sunucusudur. Frontend uygulamaları bu API'yi kullanarak fatura açıklama, anomali tespiti ve what-if simülasyonu yapabilir.

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler

```bash
# Python 3.8+ gerekli
python --version

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Veri Hazırlığı

```bash
# Veri özetlerini oluştur (artifacts klasörü için)
python general_scripts/data_prep.py --data data --out artifacts
```

### 3. Sunucuyu Başlat

```bash
# Doğrudan Python ile
python api_server.py

# Veya uvicorn ile (development için)
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test Et

```bash
# API test scriptini çalıştır
python test_api.py

# Veya manuel test
curl http://localhost:8000/health
```

## 📋 API Endpoint'leri

### Temel Endpoint'ler

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/health` | Sunucu durumu |
| GET | `/api/users` | Tüm kullanıcılar |
| GET | `/api/users/{id}` | Kullanıcı detayı |
| GET | `/api/bills/{user_id}` | Kullanıcı faturaları |
| GET | `/api/catalog` | Katalog verileri |

### İş Mantığı Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/explain` | Fatura açıklama |
| POST | `/api/anomalies` | Anomali tespiti |
| POST | `/api/whatif` | What-if simülasyonu |
| GET | `/api/whatif/top3/{user_id}` | En iyi 3 senaryo |
| POST | `/api/checkout` | Mock checkout |

## 🔧 Konfigürasyon

### Ortam Değişkenleri

```bash
# LLM için (opsiyonel)
export LLM_PROVIDER=ollama
export LLM_MODEL=qwen2.5:7b
export OLLAMA_HOST=http://localhost:11434

# API için
export API_HOST=0.0.0.0
export API_PORT=8000
```

### CORS Ayarları

API sunucusu CORS ayarları ile yapılandırılmıştır. Frontend'in farklı porttan erişebilmesi için:

```python
# api_server.py içinde
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domain'ler belirtin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Veri Yapısı

### Gerekli Dosyalar

```
data/
├── users.csv              # Kullanıcı bilgileri
├── plans.csv              # Plan kataloğu
├── bill_headers.csv       # Fatura başlıkları
├── bill_items.csv         # Fatura kalemleri
├── usage_daily.csv        # Günlük kullanım
├── add_on_packs.csv       # Ek paketler
├── vas_catalog.csv        # VAS kataloğu (opsiyonel)
└── premium_sms_catalog.csv # Premium SMS kataloğu (opsiyonel)

artifacts/
├── bill_summary.csv       # Fatura özetleri
├── category_breakdown.csv # Kategori dağılımları
└── segment_stats.csv      # Segment istatistikleri
```

### Veri Tipleri

- **users**: user_id, name, current_plan_id, type, msisdn
- **plans**: plan_id, plan_name, type, quota_gb, quota_min, quota_sms, monthly_price, overage_gb, overage_min, overage_sms
- **bill_headers**: bill_id, user_id, period_start, period_end, issue_date, total_amount, currency
- **bill_items**: bill_id, item_id, category, subtype, description, amount, unit_price, quantity, tax_rate, created_at

## 🔌 Frontend Entegrasyonu

### JavaScript/TypeScript

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
```

### Python

```python
import requests

API_BASE = "http://localhost:8000"

def get_user(user_id):
    response = requests.get(f"{API_BASE}/api/users/{user_id}")
    return response.json()

def explain_bill(bill_id):
    response = requests.post(
        f"{API_BASE}/api/explain",
        json={"bill_id": bill_id}
    )
    return response.json()
```

## 🧪 Test

### Otomatik Test

```bash
python test_api.py
```

### Manuel Test

```bash
# Health check
curl http://localhost:8000/health

# Kullanıcı listesi
curl http://localhost:8000/api/users

# Fatura açıklama
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"bill_id": 700101}'

# What-if simülasyonu
curl -X POST http://localhost:8000/api/whatif \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1001,
    "period": "2025-07",
    "scenario": {
      "plan_id": 3,
      "disable_vas": true
    }
  }'
```

## 🚨 Hata Kodları

| Kod | Açıklama |
|-----|----------|
| 200 | Başarılı |
| 404 | Bulunamadı (kullanıcı, fatura, vb.) |
| 500 | Sunucu hatası |
| 503 | Veri yüklenmedi |

## 📝 Loglar

API sunucusu başladığında şu logları göreceksiniz:

```
Loading data...
Loaded 6 dataframes
Loading artifacts...
Artifacts loaded successfully
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 🔒 Güvenlik

- **CORS**: Production'da spesifik domain'ler belirtin
- **Rate Limiting**: Büyük ölçekli kullanım için rate limiting ekleyin
- **Authentication**: Gerçek uygulamada authentication ekleyin

## 🚀 Production Deployment

### Docker ile

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Production ortam değişkenleri
export API_HOST=0.0.0.0
export API_PORT=8000
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
export LOG_LEVEL=info
```

## 📞 Destek

- **Dokümantasyon**: `api_test_examples.md`
- **Test Scripti**: `test_api.py`
- **Örnek Kullanım**: README dosyalarında

## 🔄 Güncellemeler

1. **Veri Güncelleme**: `data/` klasöründeki CSV'leri güncelleyin
2. **Artifacts Yenileme**: `python general_scripts/data_prep.py` çalıştırın
3. **Sunucu Yeniden Başlatma**: API sunucusunu yeniden başlatın 