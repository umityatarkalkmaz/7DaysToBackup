# Active Context - 7DaysToBackup

## Mevcut Çalışma Odağı
Tamamlanan özelliklerin dokümantasyonu ve kodun commitlenmesi.

## Son Değişiklikler

### Ayarlar ve Konfigürasyon
- `ConfigManager` Singleton sınıfı eklendi (`src/core/config.py`).
- `config.json` ile ayarların kalıcı olması sağlandı.
- Ayarlar butonu ve dialog penceresi eklendi (`src/ui/settings_dialog.py`).
- Özel save yolu belirleme özelliği eklendi (Karanlık tema uyumlu).

### Kod Refaktörü (Modern Yapı)
- Proje `src/` klasörü altına taşındı
- `platform.py`, `window.py` ve `theme.py` gibi modüller oluşturuldu
- `languages.py` `src/i18n/` altına taşındı

### Platform Desteği
- `get_os_type()` fonksiyonu ile OS tespiti
- `get_saves_path()` fonksiyonu ile otomatik save klasörü bulma ve özel save yolu önceliği
- `get_desktop_path()` fonksiyonu ile masaüstü yolu

## Sonraki Adımlar

### Kısa Vadeli (Öncelikli)
1. **Otomatik Yedekleme**: Arka planda periyodik yedek alma özelliği (Zamanlayıcı).
2. **Yedek Geçmişi**: Alınan yedeklerin listelenmesi ve yönetimi.

### Orta Vadeli
3. Yedekleri sıkıştırma (ZIP).
4. Uzak sunucuya yedekleme (Opsiyonel).

## Aktif Kararlar ve Düşünceler
- **Karanlık Tema Zorunluluğu**: UI geliştirilirken "Karanlık Tema Kutsaldır" prensibi, ayarlar penceresinde de uygulandı.
- **Konfigürasyon Yönetimi**: `ConfigManager` singleton'ı üzerinden tüm ayarlar yönetilir.
- **Ayarlar UX**: Ayarlar butonu ana ekranda sağ üstte, dikkat dağıtmayan bir yerde.

## Önemli Kalıplar ve Tercihler
- **Singleton**: `ConfigManager` sınıfı uygulama genelinde tekil erişim sağlar.
- **Type hints**: `-> str`, `Optional[str]` kullanımı.
- **Path Handling**: `os.path` modülü platform bağımsızlığı için kullanılır.
- **Çeviriler**: Dictionary yapısında ve format string'ler ile.

## Öğrenilen Dersler
- Windows'ta `%APPDATA%` expandvars ile açılmalı
- macOS'ta `Application Support` klasörü farklı
- Linux'ta XDG standartları kontrol edilmeli
