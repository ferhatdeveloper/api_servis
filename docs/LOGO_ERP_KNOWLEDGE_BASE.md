# 🏗️ Logo ERP Veritabanı Bilgi Bankası (Knowledge Base)

Bu doküman, Logo Tiger ve Go serisi ERP sistemleri için raporlama, veri entegrasyonu ve SQL sorgu geliştirme süreçlerinde kullanılmak üzere hazırlanmış teknik bir rehberdir.

## 1. Veritabanı Temelleri
Logo veritabanında tablolar `LG_FFF_SS_TABLENAME` formatında isimlendirilir:
- **FFF:** 3 haneli firma numarası (Örn: 001).
- **SS:** 2 haneli dönem numarası (Örn: 01).
- **Global Tablolar:** `LG_FFF_CLCARD` gibi kartlar genellikle dönemden bağımsızdır.
- **Hareket Tabloları:** `LG_FFF_01_STLINE` gibi hareketler döneme bağlıdır.

---

## 2. Ana Modüller ve Tablolar

### 📦 Malzeme Yönetimi (Stok)
- **LG_FFF_ITEMS:** Malzeme (Stok) kartları. `LOGICALREF` ana anahtardır.
- **LG_FFF_SS_STLINE:** Malzeme hareketleri (Fatura satırları, ambar fişleri vb.).
- **LG_FFF_SS_STFICHE:** Malzeme fişleri başlık bilgileri.
- **LG_FFF_UNITSETL:** Birim setleri ve çevrim katsayıları.
- **LG_FFF_INVDEF:** Ambar (Depo) tanımları.

### 👥 Finans (Cari Hesaplar)
- **LG_FFF_CLCARD:** Cari hesap kartları (Müşteri, Tedarikçi).
- **LG_FFF_SS_CLFLINE:** Cari hesap hareketleri.
- **LG_FFF_SS_CLFICHE:** Cari hesap fişleri.
- **LG_FFF_PAYPLANS:** Ödeme/Tahsilat planları (Vade tanımları).

### 💰 Satış ve Satın Alma
- **LG_FFF_SS_INVOICE:** Fatura başlıkları (Satış ve Alış).
- **LG_FFF_SS_ORFLINE:** Sipariş satırları.
- **LG_FFF_SS_ORFICHE:** Sipariş fişleri başlıkları.

### 🏦 Banka ve Kasa
- **LG_FFF_BNCARD:** Banka hesap kartları.
- **LG_FFF_SS_BNFLINE:** Banka hareketleri.
- **LG_FFF_KSCARD:** Kasa tanımları.
- **LG_FFF_SS_KSLINES:** Kasa hareketleri.

---

## 3. Kritik Sorgu Mantıkları (Snippets)

### Fatura ve Satır Detayı Join Yapısı
```sql
SELECT 
    INV.FICHENO AS [Fatura No],
    CL.DEFINITION_ AS [Cari Ünvan],
    ITM.NAME AS [Malzeme Adı],
    STL.AMOUNT AS [Miktar],
    STL.PRICE AS [Birim Fiyat]
FROM LG_FFF_SS_INVOICE INV WITH(NOLOCK)
INNER JOIN LG_FFF_SS_STLINE STL WITH(NOLOCK) ON INV.LOGICALREF = STL.INVOICEREF
LEFT JOIN LG_FFF_CLCARD CL WITH(NOLOCK) ON INV.CLIENTREF = CL.LOGICALREF
LEFT JOIN LG_FFF_ITEMS ITM WITH(NOLOCK) ON STL.STOCKREF = ITM.LOGICALREF
WHERE INV.CANCELLED = 0 -- İptal edilmemiş kayıtlar
```

### Önemli TRCODE Değerleri
| Modül | TRCODE | Açıklama |
| :--- | :--- | :--- |
| **INVOICE** | 8 | Toptan Satış Faturası |
| **INVOICE** | 1 | Satın Alma Faturası |
| **STFICHE** | 1 | Satın Alma İrsaliyesi |
| **CLFLINE** | 38 | Toptan Satış Faturası (Cari Hareket) |
| **BNFLINE** | 3 | Gelen Havale |

---

## 4. Raporlama İpuçları
1. **Zaman Zekası:** `DATE_` alanları `DATETIME` formatındadır. Yıl analizi için `YEAR(DATE_)` kullanılır.
2. **Para Birimleri:** `TRCURR` (Yerel) vs `REPORTCURR` (Raporlama - Genelde USD/EUR) farkına dikkat edilmelidir.
3. **Net Tutar:** Brüt tutardan indirimlerin (DISCOUNT) düşülmesi gerekir.
4. **Birim Çevrim:** `STLINE.AMOUNT` değeri her zaman `LINENR=1` olan ana birim üzerinden hesaplanmalıdır.

---

## 5. İleri Seviye İlişkiler ve Mantıklar

### LINETYPE (Satır Tipi) Matrisi
| Kod | Açıklama | Raporlama Etkisi |
| :--- | :--- | :--- |
| **0** | Stoklu Malzeme | Ciro ve Stok miktarını etkiler. |
| **1** | Promosyon | Stok miktarını düşürür, ciroyu etkilemez. |
| **2** | İndirim | Satır genetiğinde eksi değer oluşturur. |
| **3** | Masraf | Ciroya eklenir. |
| **4** | Hizmet | Stok miktarını etkilemez, ciroya eklenir. |

### Finansal Tahsilat (BNFLINE) Join Senaryosu
Banka hareketlerinden hangi cariye/faturaya gittiğini bulmak için:
```sql
SELECT 
    BNC.DEFINITION_ AS Banka,
    CA.DEFINITION_ AS Cari,
    BNL.AMOUNT AS [Tutar],
    CASE BNL.TRCODE 
        WHEN 3 THEN 'Gelen Havale' 
        WHEN 4 THEN 'Gönderilen Havale' 
    END AS [İşlem Tipi]
FROM LG_FFF_SS_BNFLINE BNL WITH(NOLOCK)
LEFT JOIN LG_FFF_BNCARD BNC WITH(NOLOCK) ON BNC.LOGICALREF = BNL.BANKREF
LEFT JOIN LG_FFF_CLCARD CA WITH(NOLOCK) ON CA.LOGICALREF = BNL.CLIENTREF
WHERE BNL.CANCELLED = 0
```

### Multi-Dönem Raporlama Notu
Logo'da hareketler her yıl (dönem) için farklı tablolarda tutulur (`_01_STLINE`, `_02_STLINE` vb.). Geniş kapsamlı analizler için `UNION ALL` yapısı kullanarak bu tablolar birleştirilmelidir. AI Copilot bu yer tutucuları (`_SS_`) otomatik olarak yönetecek şekilde eğitilmiştir.

---
> [!TIP]
> Bu rehber @ugurozpinar/Logo reposundan derlenmiştir. Daha detaylı tablo açıklamaları için [Logo Veri Sözlüğü](https://docs.logo.com.tr) ziyaret edilmelidir.
