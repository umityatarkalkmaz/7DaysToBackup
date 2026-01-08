# Progress - 7DaysToBackup

## Tamamlanan Özellikler ✅

### Temel İşlevler
- [x] Map listesi görüntüleme
- [x] Save listesi görüntüleme
- [x] Save yedekleme (tarih damgalı)
- [x] Save silme (onay ile)
- [x] Save dışa aktarma (zip)
- [x] Save içe aktarma (zip'ten)

### Arayüz
- [x] PySide6 (Qt6) tabanlı GUI
- [x] Koyu tema
- [x] Dil seçimi (TR/EN)
- [x] Responsive layout
- [x] Bilgi/hata mesaj kutuları

### Platform Desteği
- [x] Windows desteği
- [x] macOS desteği
- [x] Linux desteği
- [x] Otomatik save yolu tespiti
- [x] Açıklayıcı hata mesajları

### Build & Dağıtım
- [x] GitHub Actions ile otomatik build
- [x] PyInstaller ile EXE oluşturma
- [x] requirements.txt

## Yapılacaklar 📋

### Yüksek Öncelik
- [x] Kod refaktörü (dosya bölme) ✅
  - [x] `ui.py` - UI bileşenleri
  - [x] `utils.py` - Yardımcı fonksiyonlar (`core/platform.py`)
  - [x] `src` yapısı oluşturuldu
- [ ] Unit testler

### Orta Öncelik
- [x] Ayarlar penceresi
- [x] Özel save yolu belirleme
- [ ] Yedek geçmişi görüntüleme
- [ ] Birden fazla save seçimi

### Düşük Öncelik
- [ ] Otomatik yedekleme (zamanlayıcı)
- [ ] Steam entegrasyonu
- [ ] Cloud backup
- [ ] Ek dil desteği (Almanca, vb.)

## Mevcut Durum
**Versiyon**: Geliştirme aşamasında (stabil)
**Son Güncelleme**: Ocak 2026
**Durum**: Çalışır durumda, yeni özellikler ekleniyor

## Bilinen Sorunlar 🐛
- [ ] EXE dosyası antivirüs uyarısı verebilir (imzasız)
- [ ] Çok uzun yol isimleri Windows'ta sorun çıkarabilir

## Proje Kararlarının Evrimi

### v1.0 - Başlangıç
- Temel yedekleme işlevleri
- Sadece Windows desteği
- Tkinter kullanıldı (sonra değişti)

### v1.1 - PySide6 Geçişi
- PySide6 ile modern arayüz
- Koyu tema eklendi
- Dil desteği eklendi

### v1.2 - Çapraz Platform (Güncel)
- macOS ve Linux desteği
- Dinamik save yolu tespiti
- Geliştirilmiş hata mesajları
