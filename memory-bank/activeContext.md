# Active Context - 7DaysToBackup

## Mevcut Çalışma Odağı
Proje temel işlevselliğe sahip ve çalışır durumda. Son yapılan değişiklikler:
- Çapraz platform desteği eklendi (Windows, macOS, Linux)
- Save klasörü bulunamadığında açıklayıcı hata mesajları eklendi

## Son Değişiklikler

### Platform Desteği (Ocak 2026)
- `platform` modülü eklendi
- `get_os_type()` fonksiyonu eklendi
- `get_saves_path()` fonksiyonu eklendi (OS'e göre yol)
- `get_desktop_path()` fonksiyonu eklendi
- `APPDATA_PATH` → `SAVES_PATH` olarak yeniden adlandırıldı

### Hata Mesajları (Ocak 2026)
- `saves_missing` çevirisi eklendi (TR ve EN)
- Olası nedenler listesi eklendi:
  - Oyun yüklü olmayabilir
  - Oyun hiç oynanmamış olabilir
  - Save dosyaları farklı konumda olabilir

## Sonraki Adımlar

### Kısa Vadeli (Öncelikli)
1. **Kod Refaktörü**: Ana dosyanın bölünmesi
   - `ui.py` - Arayüz bileşenleri
   - `utils.py` - Yardımcı fonksiyonlar
   - `file_ops.py` - Dosya işlemleri
   
2. **Test Coverage**: Unit testler ekleme

### Orta Vadeli
3. Ayarlar penceresi (özel save yolu belirleme)
4. Otomatik yedekleme özelliği
5. Yedek geçmişi görüntüleme

### Uzun Vadeli
6. Steam entegrasyonu
7. Cloud backup desteği

## Aktif Kararlar ve Düşünceler
- **Karanlık Tema Zorunluluğu**: UI geliştirilirken "Karanlık Tema Kutsaldır" prensibi uygulanacak. Asla açık renkli tema kullanılmayacak.
- Tek dosya yapısı şimdilik yeterli ama büyüdükçe bölünmeli
- PySide6 tercih edildi (daha modern Qt bindings)
- Koyu tema varsayılan (oyuncu dostu)

## Önemli Kalıplar ve Tercihler
- Type hints kullanımı (`-> str`, `Optional[str]`)
- Özel metotlar `_` ile başlıyor
- Çeviriler dictionary yapısında
- Format string'ler `{}` ile

## Öğrenilen Dersler
- Windows'ta `%APPDATA%` expandvars ile açılmalı
- macOS'ta `Application Support` klasörü farklı
- Linux'ta XDG standartları kontrol edilmeli
