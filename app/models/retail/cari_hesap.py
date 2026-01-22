"""
RetailOS - Cari Hesap Models
Cari Hesap (MÃ¼ÅŸteri/TedarikÃ§i BorÃ§-Alacak Takibi) modelleri
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.async_database import Base


class CariTipi(str, enum.Enum):
    """Cari Tipi Enum"""
    MUSTERI = "Musteri"
    TEDARIKCI = "Tedarikci"
    PERSONEL = "Personel"
    ORTAK = "Ortak"
    DIGER = "Diger"


class IslemTipi(str, enum.Enum):
    """Ä°ÅŸlem Tipi Enum"""
    BORC = "Borc"
    ALACAK = "Alacak"


class BelgeTipi(str, enum.Enum):
    """Belge Tipi Enum"""
    FATURA = "Fatura"
    TAHSILAT = "Tahsilat"
    TEDIYE = "Tediye"
    VIRMAN = "Virman"
    DEKONT = "Dekont"
    ACILIS = "Acilis"


class CariHesap(Base):
    """Cari Hesaplar (MÃ¼ÅŸteri/TedarikÃ§i KartlarÄ±)"""
    __tablename__ = "cari_hesaplar"
    
    cari_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firma_id = Column(Integer, ForeignKey("firmalar.firma_id", ondelete="CASCADE"), nullable=False)
    
    # Cari Kart Bilgileri
    cari_kodu = Column(String(50), nullable=False, index=True)
    cari_unvan = Column(String(200), nullable=False)
    cari_tipi = Column(Enum(CariTipi), nullable=False)
    cari_grubu = Column(String(100))
    
    # Bakiye Bilgileri (Otomatik HesaplanÄ±r)
    toplam_borc = Column(DECIMAL(15, 2), default=0.00)
    toplam_alacak = Column(DECIMAL(15, 2), default=0.00)
    bakiye = Column(DECIMAL(15, 2), default=0.00)  # Pozitif: Bizden alacaklÄ±, Negatif: Bize borÃ§lu
    
    # Risk YÃ¶netimi
    risk_limiti = Column(DECIMAL(15, 2), default=0.00)
    acik_hesap_limiti = Column(DECIMAL(15, 2), default=0.00)
    kredi_limiti = Column(DECIMAL(15, 2), default=0.00)
    
    # Vade Bilgileri
    standart_vade_gun = Column(Integer, default=0)
    ozel_vade_gun = Column(Integer)
    
    # Vergi Bilgileri
    vergi_dairesi = Column(String(100))
    vergi_no = Column(String(20))
    tc_kimlik_no = Column(String(11))
    
    # Ä°letiÅŸim Bilgileri
    adres = Column(Text)
    sehir = Column(String(100))
    ilce = Column(String(100))
    posta_kodu = Column(String(10))
    ulke = Column(String(50), default="TÃ¼rkiye")
    telefon1 = Column(String(50))
    telefon2 = Column(String(50))
    fax = Column(String(50))
    email = Column(String(100))
    website = Column(String(100))
    
    # Yetkili KiÅŸi
    yetkili_kisi = Column(String(100))
    yetkili_telefon = Column(String(50))
    yetkili_email = Column(String(100))
    
    # Muhasebe Bilgileri
    muhasebe_kodu = Column(String(50))
    TAX_muafiyeti = Column(Boolean, default=False)
    TAX_orani = Column(DECIMAL(5, 2), default=20.00)
    
    # E-DÃ¶nÃ¼ÅŸÃ¼m
    efatura_kullanici = Column(Boolean, default=False)
    earsiv_kullanici = Column(Boolean, default=False)
    gib_etiket = Column(String(100))
    
    # Logo/Nebim Entegrasyon
    logo_cari_kodu = Column(String(50))
    logo_senkronize = Column(Boolean, default=False)
    logo_senkron_tarihi = Column(DateTime)
    
    # Sistem AlanlarÄ±
    aktif_mi = Column(Boolean, default=True)
    olusturan_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    olusturma_tarihi = Column(DateTime, server_default=func.now())
    guncelleme_tarihi = Column(DateTime, server_default=func.now(), onupdate=func.now())
    notlar = Column(Text)
    
    # Ä°liÅŸkiler
    hareketler = relationship("CariHareket", back_populates="cari_hesap", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CariHesap {self.cari_kodu}: {self.cari_unvan}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "cari_id": self.cari_id,
            "cari_kodu": self.cari_kodu,
            "cari_unvan": self.cari_unvan,
            "cari_tipi": self.cari_tipi.value if self.cari_tipi else None,
            "toplam_borc": float(self.toplam_borc) if self.toplam_borc else 0,
            "toplam_alacak": float(self.toplam_alacak) if self.toplam_alacak else 0,
            "bakiye": float(self.bakiye) if self.bakiye else 0,
            "telefon1": self.telefon1,
            "email": self.email,
            "aktif_mi": self.aktif_mi,
        }


class CariHareket(Base):
    """Cari Hareketler (BorÃ§-Alacak KayÄ±tlarÄ±)"""
    __tablename__ = "cari_hareketler"
    
    hareket_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cari_id = Column(Integer, ForeignKey("cari_hesaplar.cari_id", ondelete="CASCADE"), nullable=False)
    firma_id = Column(Integer, ForeignKey("firmalar.firma_id", ondelete="CASCADE"), nullable=False)
    yil_id = Column(Integer, nullable=False)
    donem_id = Column(Integer)
    
    # Ä°ÅŸlem Bilgileri
    islem_tarihi = Column(Date, nullable=False, index=True)
    islem_tipi = Column(Enum(IslemTipi), nullable=False)
    belge_tipi = Column(Enum(BelgeTipi), nullable=False)
    belge_no = Column(String(100))
    
    # Tutar
    tutar = Column(DECIMAL(15, 2), nullable=False)
    doviz_tipi = Column(String(10), default="TRY")
    doviz_kuru = Column(DECIMAL(15, 6), default=1.000000)
    doviz_tutari = Column(DECIMAL(15, 2))
    
    # AÃ§Ä±klama
    aciklama = Column(Text)
    
    # Vade
    vade_tarihi = Column(Date)
    vade_gun = Column(Integer)
    
    # Ä°liÅŸkili Belgeler
    fatura_id = Column(Integer)
    kasa_hareket_id = Column(Integer)
    banka_hareket_id = Column(Integer)
    
    # Bakiye (Running Balance)
    onceki_bakiye = Column(DECIMAL(15, 2))
    yeni_bakiye = Column(DECIMAL(15, 2))
    
    # Logo/Nebim Entegrasyon
    logo_fiche_no = Column(String(50))
    logo_line_no = Column(Integer)
    logo_senkronize = Column(Boolean, default=False)
    
    # Sistem
    olusturan_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    olusturma_tarihi = Column(DateTime, server_default=func.now())
    
    # Ä°liÅŸkiler
    cari_hesap = relationship("CariHesap", back_populates="hareketler")
    
    def __repr__(self):
        return f"<CariHareket {self.belge_no}: {self.tutar}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "hareket_id": self.hareket_id,
            "cari_id": self.cari_id,
            "islem_tarihi": self.islem_tarihi.isoformat() if self.islem_tarihi else None,
            "islem_tipi": self.islem_tipi.value if self.islem_tipi else None,
            "belge_tipi": self.belge_tipi.value if self.belge_tipi else None,
            "belge_no": self.belge_no,
            "tutar": float(self.tutar) if self.tutar else 0,
            "aciklama": self.aciklama,
            "vade_tarihi": self.vade_tarihi.isoformat() if self.vade_tarihi else None,
            "yeni_bakiye": float(self.yeni_bakiye) if self.yeni_bakiye else 0,
        }


class CariVadeTakip(Base):
    """Cari Vade Takip (Vadeli Ä°ÅŸlem Takibi)"""
    __tablename__ = "cari_vade_takip"
    
    vade_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cari_id = Column(Integer, ForeignKey("cari_hesaplar.cari_id", ondelete="CASCADE"), nullable=False)
    hareket_id = Column(Integer, ForeignKey("cari_hareketler.hareket_id", ondelete="CASCADE"), nullable=False)
    
    # Vade Bilgileri
    vade_tarihi = Column(Date, nullable=False, index=True)
    vade_tutari = Column(DECIMAL(15, 2), nullable=False)
    kalan_tutar = Column(DECIMAL(15, 2), nullable=False)
    odenen_tutar = Column(DECIMAL(15, 2), default=0.00)
    
    # Durum
    vade_durumu = Column(String(20), default="Bekliyor")  # Bekliyor, KismiOdendi, Odendi, Gecikti
    gecikme_gun = Column(Integer, default=0)
    
    # Ã–deme Bilgileri
    odeme_tarihi = Column(Date)
    
    def __repr__(self):
        return f"<CariVadeTakip {self.vade_tarihi}: {self.kalan_tutar}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "vade_id": self.vade_id,
            "cari_id": self.cari_id,
            "vade_tarihi": self.vade_tarihi.isoformat() if self.vade_tarihi else None,
            "vade_tutari": float(self.vade_tutari) if self.vade_tutari else 0,
            "kalan_tutar": float(self.kalan_tutar) if self.kalan_tutar else 0,
            "vade_durumu": self.vade_durumu,
            "gecikme_gun": self.gecikme_gun,
        }
