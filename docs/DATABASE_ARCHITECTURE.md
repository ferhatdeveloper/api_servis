# EXFIN OPS - Database Architecture

## 📊 **Veritabanı Mimarisi**

EXFIN OPS, **hybrid database** yaklaşımı kullanır:

```
┌─────────────────────────────────────────────────────────┐
│                    EXFIN OPS                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Web App    │         │  Mobile App  │            │
│  │  (Flutter)   │         │  (Flutter)   │            │
│  └──────┬───────┘         └──────┬───────┘            │
│         │                        │                     │
│         │ Direct                 │ Sync                │
│         ↓                        ↓                     │
│  ┌──────────────┐         ┌──────────────┐            │
│  │ PostgreSQL   │         │   SQLite     │            │
│  │  (Cloud)     │←────────│  (Local)     │            │
│  └──────┬───────┘  Sync   └──────────────┘            │
│         │                                              │
│         │ Read Reports                                 │
│         ↓                                              │
│  ┌──────────────┐                                      │
│  │  Logo ERP    │                                      │
│  │ (SQL Server) │                                      │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ **1. PostgreSQL (Cloud Database)**

### **Konum:** Uzak Sunucu
### **Kullanım:** Web + Mobile (sync)
### **Dosya:** `exfin_complete_schema.sql`

### **Tablolar (29 adet):**

| Kategori | Tablolar |
|----------|----------|
| **Kullanıcı Yönetimi** | `users`, `user_settings`, `user_tenants` |
| **Saha Operasyonları** | `visits`, `gps_tracks`, `live_location_snapshots`, `location_history` |
| **Offline Sync** | `offline_sync_queue`, `offline_orders`, `offline_collections`, `offline_stock_counts` |
| **Bildirimler** | `notifications`, `push_notification_history` |
| **Raporlama** | `report_snapshots`, `favorite_reports`, `report_access_logs`, `user_activity_logs` |
| **Güvenlik** | `device_security_logs`, `firewall_rules`, `blocked_devices` |
| **Sistem** | `system_settings`, `cache_entries`, `tenants`, `uploaded_files`, `tasks` |

### **Kurulum:**
```bash
# Uzak sunucuda
psql -U postgres -f exfin_complete_schema.sql
psql -U postgres -d exfin_db -f exfin_mock_data.sql
```

---

## 📱 **2. SQLite (Mobile Database)**

### **Konum:** Mobil cihaz (local)
### **Kullanım:** Sadece Mobile (offline-first)
### **Dosya:** `mobile_sqlite_schema.sql`

### **Tablolar (14 adet):**

| Kategori | Tablolar | Sync Yönü |
|----------|----------|-----------|
| **Kullanıcı** | `users`, `user_settings` | ⬇️ Pull |
| **Cache** | `customers`, `products` | ⬇️ Pull |
| **Offline İşlemler** | `offline_orders`, `offline_collections`, `offline_stock_counts` | ⬆️ Push |
| **Saha** | `visits`, `gps_tracks` | ⬆️ Push |
| **Raporlar** | `report_snapshots` | ⬇️ Pull |
| **Sync** | `offline_queue`, `sync_metadata` | ⬆️⬇️ Both |
| **Diğer** | `notifications`, `cache_entries`, `app_logs` | ⬇️ Pull |

### **Kurulum:**
```dart
// Flutter'da otomatik oluşturulur
final db = await MobileDatabaseService.instance.database;
```

---

## 🏢 **3. Logo ERP (SQL Server)**

### **Konum:** Müşteri sunucusu
### **Kullanım:** Read-only (raporlar)
### **Dosya:** `yoy_comparison_views.sql`

### **View'lar:**
- `V_YOY_DAILY_COMPARISON` - Günlük karşılaştırma
- `V_YOY_WEEKLY_COMPARISON` - Haftalık karşılaştırma
- `V_YOY_MONTHLY_COMPARISON` - Aylık karşılaştırma

### **Kurulum:**
```sql
-- Logo veritabanında
USE NAWRAS
GO
-- yoy_comparison_views.sql çalıştır
```

---

## 🔄 **Senkronizasyon Akışı**

### **📥 PULL (Sunucu → Mobil)**

```dart
// 1. Müşterileri çek
final customers = await api.getCustomers();
await MobileDatabaseService.instance.pullCustomers(customers);

// 2. Ürünleri çek
final products = await api.getProducts();
await MobileDatabaseService.instance.pullProducts(products);

// 3. Raporları çek
final reports = await api.getReportSnapshot('SALES_REPORT');
await db.saveReportSnapshot(reports);
```

### **📤 PUSH (Mobil → Sunucu)**

```dart
// 1. Offline siparişleri gönder
final orders = await MobileDatabaseService.instance.getPendingOrders();
for (var order in orders) {
  final response = await api.createOrder(order);
  await db.markOrderSynced(order['id'], response['logo_ref']);
}

// 2. Tahsilatları gönder
final collections = await db.getPendingCollections();
for (var collection in collections) {
  await api.createCollection(collection);
  await db.markCollectionSynced(collection['id']);
}

// 3. Ziyaretleri gönder
final visits = await db.getPendingVisits();
for (var visit in visits) {
  await api.createVisit(visit);
  await db.markVisitSynced(visit['id']);
}
```

### **🔄 Otomatik Sync**

```dart
// Her 5 dakikada bir
Timer.periodic(Duration(minutes: 5), (_) async {
  if (await isOnline()) {
    // Önce gönder
    await pushAll();
    
    // Sonra çek
    await pullAll();
  }
});
```

---

## 📋 **Platform Bazlı Kullanım**

### **🌐 Web Platform**

```dart
if (kIsWeb) {
  // Direkt PostgreSQL kullan
  final data = await PostgreSQLService.instance.query('SELECT * FROM customers');
}
```

### **📱 Mobile Platform**

```dart
if (!kIsWeb) {
  // SQLite kullan
  final data = await MobileDatabaseService.instance.searchCustomers('ABC');
  
  // Offline sipariş oluştur
  await db.insert('offline_orders', orderData);
  
  // Sync zamanı geldiğinde
  await syncService.pushAll();
}
```

---

## 🎯 **Kullanım Senaryoları**

### **Senaryo 1: Satış Temsilcisi (Offline)**

```
1. Sabah ofiste → Veri çek (customers, products)
2. Sahada → İnternet yok
3. Müşteri ziyareti → SQLite'a kaydet
4. Sipariş oluştur → SQLite'a kaydet
5. Tahsilat yap → SQLite'a kaydet
6. Akşam ofise dön → İnternet var
7. Otomatik sync → Tüm veriler PostgreSQL'e
8. PostgreSQL → Logo ERP'ye gönder
```

### **Senaryo 2: Web Kullanıcısı (Online)**

```
1. Web'de login
2. Direkt PostgreSQL'den veri çek
3. Rapor görüntüle → Logo ERP'den çek
4. Sipariş oluştur → Direkt Logo'ya gönder
```

---

## 📊 **Veri Boyutları**

| Veritabanı | Tahmini Boyut | Açıklama |
|------------|---------------|----------|
| PostgreSQL | 100-500 MB | Tüm kullanıcılar, loglar, snapshot'lar |
| SQLite (Mobil) | 10-50 MB | Kullanıcı bazlı cache + offline queue |
| Logo ERP | 10+ GB | Ana ERP veritabanı (read-only) |

---

## ✅ **Kurulum Checklist**

- [ ] PostgreSQL sunucusu kuruldu
- [ ] `exfin_complete_schema.sql` çalıştırıldı
- [ ] `exfin_mock_data.sql` çalıştırıldı (test için)
- [ ] Logo ERP'de `yoy_comparison_views.sql` çalıştırıldı
- [ ] `db_config.json` güncellendi
- [ ] EXFIN_API başlatıldı
- [ ] Flutter app test edildi (web + mobile)

---

## 🔧 **Bakım**

### **PostgreSQL Temizlik:**
```sql
-- Eski snapshot'ları temizle
DELETE FROM report_snapshots WHERE expires_at < NOW();

-- Eski logları temizle
DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL '30 days';
```

### **SQLite Temizlik:**
```dart
// Expired cache temizle
await MobileDatabaseService.instance.clearExpiredCache();

// Logout - tüm veriyi sil
await MobileDatabaseService.instance.clearAllData();
```

---

## 📞 **Destek**

Sorular için: `DATABASE_SETUP.md` ve `DATABASE_TABLES.md` dosyalarına bakın.
