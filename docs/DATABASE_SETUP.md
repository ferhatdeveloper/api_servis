# EXFIN OPS - Veritabanı Kurulum Kılavuzu

EXFIN OPS sisteminin doğru çalışabilmesi için PostgreSQL (EXFINOPS) ve MSSQL (LOGO ERP) veritabanlarının yapılandırılması gerekmektedir.

## 1. PostgreSQL (EXFINOPS) Kurulumu

PostgreSQL veritabanını kurmak için iki yöntem bulunmaktadır:

### Yöntem A: Hızlı Kurulum (Tavsiye Edilen)
Tek bir script ile tüm tablo yapısını ve mock verileri yükler.

1. `sql/setup/01_master_setup.sql` dosyasını `postgres` kullanıcısı ile çalıştırın.
   - Bu script `EXFINOPS` veritabanını oluşturur, şemayı kurar ve başlangıç verilerini yükler.

### Yöntem B: Modüler Kurulum
Dosyaları sırasıyla çalıştırarak kurulumu özelleştirin.

1.  **Şema**: `sql/schema/01_core_schema.sql` (Tablo yapısını oluşturur)
2.  **Veri**: `sql/data/01_mock_data.sql` (Başlangıç kullanıcılarını ve ayarları yükler)
3.  **Anlık Görüntüler**: `sql/report_snapshots.sql` (Rapor önbellek tabloları)

---

## 2. MSSQL (LOGO ERP) Kurulumu

Logo ERP veritabanında YoY (Year-over-Year) raporlarının çalışabilmesi için gerekli view'ların oluşturulması gerekir.

1. Logo ERP'nin bulunduğu MSSQL Server üzerinde `sql/views/01_yoy_views.sql` dosyasını çalıştırın.
   - Bu dosya `V_YOY_DAILY_COMPARISON`, `V_YOY_WEEKLY_COMPARISON` ve `V_YOY_MONTHLY_COMPARISON` view'larını oluşturur.

---

## 3. Kurulum Sonrası Kontroller

Veritabanı kurulumu bittikten sonra `SETUP.bat` dosyasını çalıştırarak:
- Veritabanı bağlantı bilgilerini girin.
- "Bağlantıyı Test Et" butonu ile doğruluğunu kontrol edin.
- Sihirbazı tamamlayarak `.env` dosyasını oluşturun.

---

## 4. Alternatif Kurulum Yöntemleri (Referans)

Aşağıdaki yöntemler, otomasyon scriptlerini kullanmadan manuel veya Docker ile kurulum yapmak isteyenler içindir.

### Yöntem A: Docker ile Hızlı Kurulum

```bash
# PostgreSQL container'ı başlat
docker run --name exfin-postgres \
  -e POSTGRES_DB=exfin_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -v exfin_data:/var/lib/postgresql/data \
  -d postgres:15

# Veritabanı şemasını yükle (Dosya yolunu güncelleyin)
docker exec -i exfin-postgres psql -U postgres -d exfin_db < sql/schema/01_core_schema.sql
```

### Yöntem B: Varsayılan Kullanıcılar (Demo Veri)

`01_mock_data.sql` yüklendiğinde aşağıdaki kullanıcılar oluşturulur:

| Kullanıcı | Şifre | Rol | E-posta |
|-----------|-------|-----|---------|
| `admin` | `admin123` | admin | admin@exfin.com |
| `salesman1` | `test123` | salesman | salesman@exfin.com |

### Sorun Giderme

**Bağlantı Hatası:** PostgreSQL servisinin çalıştığından emin olun (`docker ps` veya `services.msc`).
**Port Çakışması:** 5432 portu doluysa, `docker run` komutunda `-p 5433:5432` gibi farklı bir port kullanın ve `.env` dosyasını buna göre güncelleyin.

