# EXFIN OPS API (Backend)

**Repository:** [https://github.com/ferhatdeveloper/api_servis](https://github.com/ferhatdeveloper/api_servis)

Hızlı Kurulum (Windows Server):
```powershell
irm bit.ly/opsapi | iex
```

**Author:** Ferhat Developer  
**Version:** 5.2 (Enterprise Deployment)  
**Framework:** FastAPI (Python)

## 📌 Proje Hakkında
EXFIN OPS, operasyon yönetimi ve Logo ERP entegrasyonu sağlayan gelişmiş bir API servisidir. Bu backend projesi, kullanıcı yönetimi, vardiya takibi, depo transferleri, fatura oluşturma ve sistem izleme gibi kritik iş süreçlerini yönetir.

---

## 🚀 Hızlı Başlangıç (Kurulum Sihirbazı)

Projeyi kurmanın en kolay yolu, geliştirilmiş **Python Wizard** aracını kullanmaktır. Bu araç bağımlılıkları yükler, veritabanını kurar ve servisi çalıştırır.

### Kurulum Adımları
1.  Projeyi klonlayın ve `backend` klasörüne gidin.
2.  Wizard'ı başlatın:
    ```powershell
    python scripts/wizard.py
    ```
3.  **Adımları Takip Edin:**
    - Sistem gereksinimleri kontrolü.
    - Python kütüphanelerinin (`requirements.txt`) otomatik yüklenmesi.
    - PostgreSQL bağlantı ayarları.
    - **Windows Servis Kurulumu** (Önerilen: "Basit Başlangıç + Tray").

---

## 🖥️ System Tray (Görev Çubuğu) Kontrolü

Versiyon 5.2 ile birlikte gelen **System Tray** uygulaması, API'yi arka planda yönetmenizi sağlar.

- **Yeşil İkon (🟢):** Servis çalışıyor (Port 8000 açık).
- **Kırmızı İkon (🔴):** Servis durdu.
- **Turuncu İkon (🟠):** İşlem yapılıyor (Başlatılıyor/Durduruluyor).

### Kontrol Menüsü
Saatin yanındaki ikona sağ tıklayarak şu işlemleri yapabilirsiniz:
1.  **Swagger UI Aç:** API dokümantasyonunu tarayıcıda açar.
2.  **Başlat:** Servisi başlatır.
3.  **Durdur (🔒):** Servisi durdurur. **(Şifre Gerektirir: `1993`)**
4.  **Yeniden Başlat (🔒):** Servisi yeniden başlatır. **(Şifre Gerektirir: `1993`)**
5.  **Çıkış:** Tray uygulamasını tamamen kapatır.

> **NOT:** Şifre koruması, yetkisiz kişilerin sunucuyu durdurmasını engellemek için eklenmiştir.

---

## 🛠️ Manuel Çalıştırma (Geliştiriciler İçin)

Eğer Wizard kullanmak istemiyorsanız, terminal üzerinden manuel olarak da çalıştırabilirsiniz.

### 1. Sanal Ortam (Virtual Environment)
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Bağımlılıklar
```powershell
pip install -r requirements.txt
# Ekstra sistem araçları için:
pip install psutil pystray Pillow requests pywin32
```

### 3. Uygulamayı Başlatma
Geliştirme modunda (Hot Reload aktif):
```powershell
python main.py
```
Veya doğrudan Uvicorn ile:
```powershell
uvicorn main:app --reload --port 8000
```

---

## 📂 Proje Yapısı

```
backend/
├── app/
│   ├── api/            # API Router ve Endpoint tanımları
│   ├── core/           # Konfigürasyon, Güvenlik, Loglama
│   ├── db/             # Veritabanı modelleri ve bağlantı
│   ├── schemas/        # Pydantic şemaları (Request/Response)
│   └── services/       # İş mantığı servisleri
├── scripts/            # Yardımcı scriptler (Wizard, Bat dosyaları)
├── tray_app.py         # System Tray uygulaması
├── main.py             # Uygulama giriş noktası
└── requirements.txt    # Python kütüphaneleri
```

## 🔐 Önemli Endpoint'ler

Kurulum sonrası **Swagger UI** üzerinden tüm endpoint'leri test edebilirsiniz:
`http://localhost:8000/docs`

- **Auth:** `/api/v1/auth/login` (Token alma)
- **CRM:** `/api/v1/crm` (Müşteri yönetimi)
- **Operasyon:** `/api/v1/operations`
- **Sistem:** `/api/v1/system/info`

---

## ❓ Sorun Giderme

**Soru: "No module named ..." hatası alıyorum.**
> **Çözüm:** `pip install -r requirements.txt` komutunu çalıştırın veya Wizard'ı tekrar çalıştırarak bağımlılıkları yükletin.

**Soru: Tray ikonu tepki vermiyor.**
> **Çözüm:** Görev yöneticisinden `python.exe` veya `ExfinOPS Backend` işlemlerini sonlandırıp tekrar başlatın.

**Soru: API endpoint'leri görünmüyor.**
> **Çözüm:** Sunucu kodları güncellenmiş olabilir. Tray menüsünden **Yeniden Başlat** yapın (Şifre: 1993).