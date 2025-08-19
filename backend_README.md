# Turkcell Fatura Asistanı - Backend Engine

Bu klasör, Turkcell Fatura Asistanı'nın backend engine'lerini içerir. Frontend ekibi bu API'yi kullanarak fatura açıklama, anomali tespiti ve what-if simülasyonu yapabilir.

## 🏗️ Proje Yapısı

```
turkcell_codenight/
├── api_server.py              # Ana FastAPI sunucusu
├── general_scripts/           # Engine'ler
│   ├── data_prep.py          # Veri hazırlama ve özetleme
│   ├── anomaly_engine.py     # Anomali tespiti
│   ├── whatif_engine.py      # What-if simülasyonu
│   └── llm_client.py         # OpenAI ChatGPT entegrasyonu
├── data/                     # CSV verileri
├── artifacts/                # İşlenmiş veri özetleri
├── requirements.txt          # Python bağımlılıkları
├── test_api.py              # API test scripti
└── llm_test.py              # LLM test scripti
```

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

# LLM testi (opsiyonel)
python llm_test.py
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

## 🔧 Engine'ler

### 1. Data Prep Engine (`data_prep.py`)
**Amaç**: CSV verilerini okuyup işlenmiş özetler oluşturur

**Kullanım**:
```bash
python general_scripts/data_prep.py --data data --out artifacts
```

**Çıktılar**:
- `bill_summary.csv` - Fatura özetleri
- `category_breakdown.csv` - Kategori dağılımları
- `segment_stats.csv` - Segment istatistikleri

### 2. Anomaly Engine (`anomaly_engine.py`)
**Amaç**: Fatura anomalilerini tespit eder

**Özellikler**:
- Z-score bazlı anomali tespiti
- % artış bazlı anomali tespiti
- Yeni kalem tespiti
- Kategori bazlı aksiyon önerileri

**Kullanım**:
```python
from general_scripts.anomaly_engine import detect_anomalies_for

result = detect_anomalies_for(bill_summary, category_breakdown, user_id, period)
```

### 3. What-If Engine (`whatif_engine.py`)
**Amaç**: Farklı senaryolar için maliyet simülasyonu

**Özellikler**:
- Plan değişikliği simülasyonu
- Ek paket ekleme simülasyonu
- VAS iptali simülasyonu
- Premium SMS engelleme simülasyonu
- En iyi 3 senaryo bulma

**Kullanım**:
```python
from general_scripts.whatif_engine import scenario_cost, enumerate_top3

# Tek senaryo
result = scenario_cost(user_id, period, data, plan_id=3, disable_vas=True)

# En iyi 3 senaryo
top3 = enumerate_top3(user_id, period, data)
```

### 4. LLM Client (`llm_client.py`)
**Amaç**: OpenAI ChatGPT ile fatura özeti üretir

**Özellikler**:
- OpenAI Chat Completions API
- Fallback mekanizması
- Türkçe fatura özeti

**Kullanım**:
```python
from general_scripts.llm_client import render_bill_summary_llm

summary = render_bill_summary_llm(payload)
```

## 📊 Veri Yapısı

### Gerekli CSV Dosyaları
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
```

### Veri Tipleri
- **users**: user_id, name, current_plan_id, type, msisdn
- **plans**: plan_id, plan_name, type, quota_gb, quota_min, quota_sms, monthly_price, overage_gb, overage_min, overage_sms
- **bill_headers**: bill_id, user_id, period_start, period_end, issue_date, total_amount, currency
- **bill_items**: bill_id, item_id, category, subtype, description, amount, unit_price, quantity, tax_rate, created_at

## 🔌 Konfigürasyon

### Ortam Değişkenleri
```bash
# LLM için (opsiyonel)
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
export OPENAI_BASE=https://api.openai.com

# API için
export API_HOST=0.0.0.0
export API_PORT=8000
```

### CORS Ayarları
API sunucusu CORS ayarları ile yapılandırılmıştır:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik domain'ler belirtin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Test

### API Testi
```bash
python test_api.py
```

### LLM Testi
```bash
python llm_test.py
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
```

## 🔒 Güvenlik

- **CORS**: Production'da spesifik domain'ler belirtin
- **Rate Limiting**: Büyük ölçekli kullanım için rate limiting ekleyin
- **Authentication**: Gerçek uygulamada authentication ekleyin
- **API Key**: OpenAI API key'ini güvenli şekilde saklayın

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

## 🔄 Güncellemeler

1. **Veri Güncelleme**: `data/` klasöründeki CSV'leri güncelleyin
2. **Artifacts Yenileme**: `python general_scripts/data_prep.py` çalıştırın
3. **Sunucu Yeniden Başlatma**: API sunucusunu yeniden başlatın

## 📞 Destek

- **Dokümantasyon**: Bu README dosyası
- **Test Scripti**: `test_api.py`
- **LLM Testi**: `llm_test.py`
- **Örnek Kullanım**: README dosyalarında

## 🎯 Özellikler

### ✅ Tamamlanan Özellikler
- [x] Fatura açıklama (kategori bazında)
- [x] Anomali tespiti (z-score, % artış)
- [x] What-if simülasyonu (plan, ek paket, VAS)
- [x] En iyi 3 senaryo bulma
- [x] LLM entegrasyonu (OpenAI ChatGPT)
- [x] REST API (FastAPI)
- [x] CORS desteği
- [x] Mock checkout
- [x] Test scriptleri

### 🔄 Geliştirilebilir Özellikler
- [ ] Authentication/Authorization
- [ ] Rate limiting
- [ ] Database entegrasyonu
- [ ] Real-time notifications
- [ ] Advanced analytics
- [ ] Multi-language support
