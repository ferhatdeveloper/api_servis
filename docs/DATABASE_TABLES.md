# EXFIN OPS - Tam Veritabanı Şeması

## 📊 Tüm Tablolar (29 Tablo)

### Ana Şema (database_schema.sql) - 9 Tablo
1. ✅ `users` - Kullanıcılar
2. ✅ `user_settings` - Kullanıcı ayarları
3. ✅ `visits` - Ziyaret kayıtları
4. ✅ `gps_tracks` - GPS geçmişi
5. ✅ `offline_sync_queue` - Senkronizasyon kuyruğu
6. ✅ `notifications` - Bildirimler
7. ✅ `report_snapshots` - Rapor önbelleği
8. ✅ `user_activity_logs` - Aktivite logları
9. ✅ `tasks` - Görevler

### Ek Şema (database_schema_additional.sql) - 20 Tablo

#### Güvenlik & Firewall
10. ✅ `device_security_logs` - Cihaz güvenlik kayıtları
11. ✅ `firewall_rules` - Firewall kuralları
12. ✅ `blocked_devices` - Engellenen cihazlar

#### Canlı Konum
13. ✅ `live_location_snapshots` - Son bilinen konum
14. ✅ `location_history` - Detaylı konum geçmişi

#### Sipariş & Satış (Offline)
15. ✅ `offline_orders` - Offline siparişler
16. ✅ `offline_collections` - Offline tahsilatlar
17. ✅ `offline_stock_counts` - Offline stok sayımları

#### Raporlama
18. ✅ `favorite_reports` - Favori raporlar
19. ✅ `report_access_logs` - Rapor erişim logları

#### Bildirimler
20. ✅ `push_notification_history` - Push notification geçmişi

#### Sistem
21. ✅ `system_settings` - Sistem ayarları
22. ✅ `cache_entries` - Genel cache

#### Multi-Tenant
23. ✅ `tenants` - Tenant'lar (firmalar)
24. ✅ `user_tenants` - Kullanıcı-Tenant ilişkisi

#### Dosya Yönetimi
25. ✅ `uploaded_files` - Yüklenen dosyalar

---

## 🚀 Kurulum Sırası

```bash
# 1. Ana şemayı yükle
psql -U postgres -d exfin_db -f database_schema.sql

# 2. Ek tabloları yükle
psql -U postgres -d exfin_db -f database_schema_additional.sql
```

**VEYA Docker ile:**
```bash
docker exec -i exfin-postgres psql -U postgres -d exfin_db < database_schema.sql
docker exec -i exfin-postgres psql -U postgres -d exfin_db < database_schema_additional.sql
```

---

## 📋 Modül-Tablo Eşleşmesi

| Modül | Tablolar |
|-------|----------|
| **Auth** | users, user_settings, user_activity_logs |
| **Firewall** | device_security_logs, firewall_rules, blocked_devices |
| **Live Location** | live_location_snapshots, location_history, gps_tracks |
| **Visits** | visits, gps_tracks |
| **Sales** | offline_orders, offline_collections |
| **Stock** | offline_stock_counts |
| **Reports** | report_snapshots, favorite_reports, report_access_logs |
| **Notifications** | notifications, push_notification_history |
| **Offline Sync** | offline_sync_queue, offline_orders, offline_collections, offline_stock_counts |
| **Admin** | users, system_settings, tenants, user_tenants |
| **Tasks** | tasks |
| **Files** | uploaded_files |
| **Cache** | cache_entries, report_snapshots |

---

## 🔍 Önemli İndeksler

- `idx_gps_user_time` - GPS sorguları
- `idx_sync_status` - Senkronizasyon
- `idx_notif_user_read` - Bildirimler
- `idx_report_user_code` - Raporlar
- `idx_activity_user_time` - Aktivite
- `idx_security_user_device` - Güvenlik
- `idx_live_location_update` - Canlı konum
- `idx_location_user_time` - Konum geçmişi
- `idx_offline_orders_status` - Offline siparişler
- `idx_report_access` - Rapor erişimi
- `idx_cache_key_expires` - Cache
- `idx_files_entity` - Dosyalar

---

## ⚡ Performans Notları

- **Partition**: `location_history` tablosu büyüdükçe aylık partition'lara bölünebilir
- **Vacuum**: Otomatik vacuum her gece 02:00'de çalışır
- **Cache Cleanup**: Süresi dolan cache'ler otomatik temizlenir
- **Trigger'lar**: `updated_at` alanları otomatik güncellenir

---

## 🔐 Güvenlik

- Tüm foreign key'ler `ON DELETE CASCADE` veya `ON DELETE SET NULL`
- Hassas veriler için JSONB kullanımı
- IP adresi ve user agent kaydı
- Cihaz güvenlik logları

---

## 📦 Toplam

- **29 Tablo**
- **15+ İndeks**
- **5 Trigger**
- **1 Cleanup Fonksiyonu**
- **Multi-tenant desteği**
- **Offline-first mimari**
