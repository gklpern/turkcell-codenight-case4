# 🚀 Turkcell Fatura Asistanı - GUI Uygulaması

Modern ve kullanıcı dostu arayüz ile Turkcell Fatura Asistanı API'sini test edin!

## 📋 Özellikler

### 🎨 Modern Arayüz
- **Dark Mode** - Göz yormayan koyu tema
- **Tab Sistemi** - Organize edilmiş kategoriler
- **Responsive Design** - Yeniden boyutlandırılabilir pencere
- **Real-time Updates** - Anlık server durumu kontrolü

### 📊 Tab Kategorileri

#### 📱 Dashboard (Mobil Giriş)
- **Tek tıkla tüm bilgileri getir**
- User ID gir, otomatik analiz
- Fatura özeti, detaylar ve öneriler
- Mobil uygulama deneyimi

#### 👥 Kullanıcılar
- Tüm kullanıcıları listele
- Kullanıcı detayı getir
- Katalog bilgileri

#### 📊 Faturalar
- Fatura bilgileri getir
- LLM ile fatura açıklaması

#### 🔍 Analiz
- Anomali tespiti
- Kohort kıyası
- Vergi analizi

#### 🎯 What-If
- Tek senaryo simülasyonu
- En iyi 3 senaryo
- Autofix önerisi

#### ⭐ Bonus
- Kohort kıyası
- Vergi ayrıştırma
- Autofix önerisi
- Mock checkout

#### 🧪 Test
- Tüm endpoint'leri test et
- Server durumu kontrolü

## 🚀 Kurulum

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Server'ı Başlat
```bash
python api_server.py
```

### 3. GUI'yi Başlat
```bash
python gui_app.py
```

## 🎯 Kullanım

### 📱 Dashboard Kullanımı (Önerilen)

1. **📱 Dashboard** tab'ına geç
2. **👤 Kullanıcı ID** gir (örn: 1001, 1012, 1025)
3. **📅 Dönem** seç (2025-05, 2025-06, 2025-07, 2025-08)
4. **🚀 Fatura Bilgilerini Getir** butonuna tıkla
5. **Otomatik olarak tüm analizler yapılır:**
   - 📊 Fatura özeti
   - 🔍 Detaylı analiz (anomaliler, kohort, vergi)
   - 💡 Tasarruf önerileri

### 📝 Örnek Test Senaryoları

#### Normal Kullanıcı (1001)
- **User ID:** 1001
- **Period:** 2025-07
- **Bill ID:** 700007

#### Yüksek Faturalı Kullanıcı (1012)
- **User ID:** 1012
- **Period:** 2025-05
- **Bill ID:** 700049 (2149 TL!)

#### Youth Kullanıcı (1025)
- **User ID:** 1025
- **Period:** 2025-05
- **Bill ID:** 700101

#### Corporate Kullanıcı (1026)
- **User ID:** 1026
- **Period:** 2025-05
- **Bill ID:** 700105

### 🔧 Plan ID'leri
- **1** - GB10 + 500dk + 100SMS (329 TL)
- **2** - GB20 + 750dk + 250SMS (429 TL)
- **3** - GB30 + 1000dk + 500SMS (529 TL)
- **4** - GB50 + 1500dk + 1000SMS (699 TL)
- **5** - Sınırsız Sosyal + GB15 + 750dk (479 TL)

### 📦 Ek Paket ID'leri
- **101** - Sosyal 5GB (79 TL)
- **102** - Video 10GB (129 TL)
- **103** - Konuşma 250dk (49 TL)
- **104** - SMS 500 (39 TL)

## 🎨 Arayüz Özellikleri

### 🌙 Dark Mode
- Göz yormayan koyu tema
- Modern görünüm
- Profesyonel tasarım

### 📱 Responsive
- Pencere boyutu değiştirilebilir
- Tab'lar otomatik düzenlenir
- Mobil uyumlu tasarım

### ⚡ Real-time
- Server durumu anlık kontrol
- Threading ile non-blocking işlemler
- Hızlı API yanıtları

### 🎯 Kullanıcı Dostu
- Sezgisel navigasyon
- Açık etiketler
- Emoji destekli ikonlar

## 🔧 Teknik Detaylar

### 🏗️ Mimari
- **CustomTkinter** - Modern GUI framework
- **Threading** - Non-blocking API calls
- **JSON** - Veri formatı
- **REST API** - Backend iletişimi

### 📦 Bağımlılıklar
```
customtkinter>=5.2.0
requests>=2.31.0
```

### 🎨 Tema Ayarları
```python
ctk.set_appearance_mode("dark")  # dark, light, system
ctk.set_default_color_theme("blue")  # blue, green, dark-blue
```

## 🚨 Sorun Giderme

### Server Bağlantı Hatası
```
🔴 Server bağlantısı kurulamadı!
```
**Çözüm:** `python api_server.py` komutunu çalıştırın

### Import Hatası
```
ModuleNotFoundError: No module named 'customtkinter'
```
**Çözüm:** `pip install customtkinter` komutunu çalıştırın

### API Timeout
```
❌ Hata: Server bağlantısı kurulamadı. Server çalışıyor mu?
```
**Çözüm:** Server'ın çalıştığından emin olun

## 📊 Performans

### ⚡ Hızlı Yanıt
- Threading ile paralel işlemler
- Non-blocking UI
- Optimize edilmiş API calls

### 🎯 Doğru Sonuçlar
- JSON formatında veri
- Hata yönetimi
- Başarı/hata durumları

### 🔄 Real-time Updates
- Server durumu kontrolü
- Anlık sonuçlar
- Dinamik güncellemeler

## 🎉 Özellikler

### ✅ Tamamlanan
- [x] Modern GUI arayüzü
- [x] **📱 Dashboard (Mobil giriş)**
- [x] **🚀 Tek tıkla otomatik analiz**
- [x] Tab sistemi
- [x] API entegrasyonu
- [x] Threading desteği
- [x] Dark mode
- [x] Responsive design
- [x] Real-time server kontrolü
- [x] Tüm endpoint'ler için arayüz
- [x] Hata yönetimi
- [x] JSON formatında sonuçlar

### 🚀 Gelecek Özellikler
- [ ] Light mode toggle
- [ ] Sonuçları kaydetme
- [ ] Grafik görselleştirme
- [ ] Batch işlemler
- [ ] Export özellikleri

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Server'ın çalıştığından emin olun
2. Gereksinimlerin yüklü olduğunu kontrol edin
3. Terminal çıktılarını kontrol edin

---

**🚀 Turkcell Fatura Asistanı GUI** - Modern ve kullanıcı dostu API test arayüzü!
