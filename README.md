# EXFIN OPS API (Backend) - v5.5 Enterprise Documentation

**Versiyon:** 5.5.0  
**Geliştirici:** Ferhat Developer  
**Kapsam:** Operasyonel Süreçler, Logo ERP Entegrasyonu, Retail, PDKS ve BI.

---

## ⚡ Hızlı Kurulum (One-Line Installer)

PowerShell'i **Yönetici Olarak** açın ve aşağıdaki komutu yapıştırın:

```powershell
irm bit.ly/opsapi | iex
```

*Bu komut; repo'yu çeker, sanal ortamı (`venv`) hazırlar, bağımlılıkları yükler ve sistemi arka planda başlatır.*

---

## 🏗️ Mimari ve Genel İşleyiş

Sistem **FastAPI** (Python) üzerine kuruludur ve **Asenkron (Async)** mimariyi benimser. Bu sayede aynı anda binlerce isteği (örneğin yüzlerce mağazadan gelen satış verisi) bloklanmadan karşılayabilir.

*   **Veritabanı Konfigürasyonu:** Tüm bağlantı ayarları kök dizindeki `api.db` (SQLite) içerisindedir.
*   **Loglama:** `logs/` klasörü altında modüllere ayrılmış log dosyaları (`retail.log`, `logo.log` vb.) tutulur.
*   **Servis Yönetimi:** Windows Service (`Exfin_ApiService`) olarak arka planda çalışır.

---

## � Modül Detayları ve Kullanım Örnekleri

Aşağıdaki tüm örnekler için `Base URL: http://localhost:8000` varsayılmıştır.

### 1. Kimlik Doğrulama (Auth Module)
**Prefix:** `/api/v1/auth`

Bu modül, kullanıcıların sisteme giriş yapmasını ve diğer endpoint'leri kullanabilmesi için gerekli olan **JWT (JSON Web Token)** üretimini sağlar.

*   **Ne İşe Yarar?** Güvenlik duvarıdır. Token almadan hiçbir veriye erişilemez.
*   **Token Süresi:** Varsayılan 12 saattir (Ayarlanabilir).

#### Örnek: Giriş Yap (Login)
**Endpoint:** `POST /api/v1/auth/login`  
**Body (Form-Data):**
- `username`: admin
- `password`: 123456

**Cevap:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@exfin.com",
    "roles": ["admin"]
  }
}
```

---

### 2. Logo ERP Entegrasyonu (Logo Module)
**Prefix:** `/api/v1/logo`

Logo Tiger/Go3 ERP sistemi ile çift yönlü konuşur.
*   **DirectDB (Hızlı):** Veritabanına (SQL) doğrudan sorgu atar. Raporlama için kullanılır.
*   **WCF/Objects (Güvenli):** Logo'nun kendi DLL'lerini (Unity Objects) kullanarak kayıt atar (Sipariş, Fatura vb.).

#### Örnek: Cari Hesap Bakiyesi Çekme
**Endpoint:** `GET /api/v1/logo/data/arp-balances`  
**Parametreler:** `code` (Cari Kodu, Opsiyonel)

**İstek:**
`GET /api/v1/logo/data/arp-balances?code=120.01.001`

**Cevap:**
```json
[
  {
    "code": "120.01.001",
    "name": "ABC MARKET LTD",
    "balance": 15000.50,
    "currency": "TL"
  }
]
```

#### Örnek: Satış Siparişi Oluşturma
**Endpoint:** `POST /api/v1/logo/orders`  
**Amaç:** Dış dünyadan (örneğin E-Ticaret) gelen siparişi Logo'ya işlemek.

**Body:**
```json
{
  "customer_code": "120.01.001",
  "date": "2024-01-22",
  "items": [
    { "code": "URUN001", "qty": 5, "price": 100 }
  ]
}
```

---

### 3. Retail (Perakende) Modülü
**Prefix:** `/api/v1/retail`

Mağazalar (Şubeler) ile Merkez ofis arasındaki tüm veri trafiğini yönetir. En kapsamlı modüldür.

*   **WebSocket (`/ws`):** Anlık haberleşme sağlar. Fiyat değiştiğinde mağazaya anında bildirim gider.
*   **Sales (`/sales`):** Mağazalardan gelen ciro verilerini toplar.

#### Örnek: Ürün Fiyat Sorgulama
**Endpoint:** `GET /api/v1/retail/products/check-price`  
**Parametreler:** `barcode`

**Cevap:**
```json
{
  "barcode": "86900001",
  "name": "Çikolatalı Gofret",
  "vat_rate": 10,
  "price": 15.00,
  "currency": "TL"
}
```

#### Örnek: Anlık Ciro Gönderimi (Şubeden Merkeze)
**Endpoint:** `POST /api/v1/retail/sales/push`  
**Body:**
```json
{
  "store_id": 102,
  "total_sales": 12500.00,
  "basket_count": 45,
  "date": "2024-01-22T10:30:00"
}
```

---

### 4. PDKS (Personel Takip) Modülü
**Prefix:** `/api/v1/pdks`

Personel Devam Kontrol Sistemi. Parmak izi veya kart okuyuculardan gelen "Raw Data"yı işleyerek anlamlı vardiya raporlarına dönüştürür.

*   **Terminal (`/terminals`):** Sahadaki cihazların yönetimi.
*   **Transactions (`/logs`):** Giriş/Çıkış hareketleri.

#### Örnek: Günlük Puantaj Raporu
**Endpoint:** `GET /api/v1/pdks/reports/daily-attendance`  
**Parametreler:** `date=2024-01-21`

**Cevap:**
```json
[
  {
    "personel": "Ahmet Yılmaz",
    "check_in": "08:00",
    "check_out": "18:05",
    "status": "TAM",
    "late_minutes": 0
  }
]
```

---

### 5. Analytics & Raporlama (BI)
**Prefix:** `/api/v1/reports` ve `/api/v1/bi`

Yönetimsel karar destek mekanizmasıdır.
*   **YOY (Year-Over-Year):** Bu yıl ve geçen yılın aynı gününü kıyaslar.
*   **Custom Reports:** Kullanıcının kendi SQL sorgularını çalıştırabildiği özel alan.

#### Örnek: Karşılaştırmalı Şube Satış Raporu
**Endpoint:** `GET /api/v1/yoy-reports/daily-sales`

**Cevap:**
```json
{
  "date": "2024-01-22",
  "total_turnover": 500000,
  "last_year_turnover": 350000,
  "growth_rate": "%42.8",
  "stores": [...]
}
```

---

---

## 🔄 Operasyonel İşlemler

### Windows Hizmeti
Servis adı: **Exfin_ApiService**  
Yönetmek için Tray menüsünü kullanın veya PowerShell:
```powershell
sc start Exfin_ApiService
sc stop Exfin_ApiService
```

### Veritabanı Yedekleme
Sistem otomatik olarak (Ayarlıysa) veya manuel tetikleme ile yedek alır:
*   **Konum:** `backups/` klasörü.
*   **Format:** `.zip` (İçinde `.sql` veya `.bak`).
*   **Tetikleme:** Tray menüsü -> "Veritabanı Yedeği Al".

---

## 🛠️ Sistem Yönetimi ve Hata Ayıklama

### Gelişmiş Loglama Sistemi
Sistem artık modül bazlı loglama yapmaktadır. `backend/logs` klasöründe şunları bulabilirsiniz:

| Dosya Adı | İçerik | Ne Zaman Bakmalıyım? |
| :--- | :--- | :--- |
| `exfin.log` | Genel Uygulama | Servis açıldı mı? Hangi portta? Genel hatalar. |
| `error.log` | Kritik Hatalar | "500 Internal Server Error" aldığınızda. |
| `logo.log` | ERP İletişimi | Logo'ya veri gitmediğinde veya bağlantı koptuğunda. |
| `retail.log` | Mağaza Trafiği | Şubelerden veri gelmiyor veya WebSocket kopuyorsa. |
| `pdks.log` | Personel Cihazları | Cihaz bağlantı hataları ve ham veri sorunlarında. |

### System Tray (Görev Çubuğu) Yöneticisi
Saatin yanındaki ikon (ExfinLogo):
*   **Yeşil:** Sistem sorunsuz.
*   **Kırmızı:** Servis durmuş.
*   **Sağ Tık Menüsü:**
    *   *Yeniden Başlat (Şifre: 1993):* Servisi restart eder.
    *   *Veritabanı Yedeği Al:* Manuel yedek oluşturur (`/backups` klasörüne).
    *   *Logları Aç:* Log klasörünü açar.

---

## 🆘 Sık Karşılaşılan Sorunlar ve Çözümleri

**1. "401 Unauthorized" Hatası**
*   **Neden:** Token süresi dolmuş veya hatalı.
*   **Çözüm:** `/auth/login` endpoint'inden tekrar giriş yapıp yeni token almalısınız.

**2. "Logo Bağlantı Hatası" (Loglarda)**
*   **Neden:** SQL Server şifresi değişmiş veya sunucu kapalı olabilir.
*   **Çözüm:** `python scripts/wizard.py` çalıştırıp veritabanı şifresini güncelleyin (Logo Veritabanı sekmesi).

**3. "Port already is use" (Port Kullanımda)**
*   **Neden:** Eski bir Python işlemi asılı kalmış.
*   **Çözüm:** Tray menüsünden "Yeniden Başlat" yapın veya Görev Yöneticisi'nden `python.exe` işlemlerini sonlandırın.

---

**İletişim:** Destek Hattı | ferhat@exfin.com
**Döküman Tarihi:** 22.01.2024