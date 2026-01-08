# System Patterns - 7DaysToBackup

## Mimari Yapı

### Dosya Organizasyonu
```
src/
├── main.py        → Giriş noktası
├── ui/            → Arayüz ve tema
├── core/          → İşletim sistemi ve dosya işlemleri
└── i18n/          → Çeviri verileri
```

### Sınıf Yapısı
```
src.ui.window.SaveManagerWindow (QMainWindow)
├── __init__()
├── _setup_ui()
... (iş mantığı metotları)
```

## Tasarım Desenleri

### Modülarite
Proje tek bir dosyadan modüler bir yapıya geçirilmiştir:
- **UI**: Arayüz kodları `src/ui` altında
- **Core**: Platform bağımlı kodlar `src/core` altında
- **I18n**: Dil verileri `src/i18n` altında

### 1. Helper Functions (Yardımcı Fonksiyonlar)
`src/core/platform.py` içinde:
- `get_os_type()`
- `get_saves_path()`
- `get_desktop_path()`

`src/ui/theme.py` içinde:
- `create_dark_palette()`

### 2. Çeviri Sistemi
```python
LANGUAGES = {
    'tr': { ... },
    'en': { ... }
}
```
- Anahtar-değer çiftleri ile çeviri
- Format string desteği: `"mesaj: {}".format(değer)`

### 4. Konfigürasyon Yönetimi (Yeni)
- `src/core/config.py`: Ayarların (custom path, dil vb.) saklanması ve yüklenmesi
- JSON tabanlı basit yapı

## Bileşen İlişkileri

```
┌─────────────────────────────────────────────┐
│              SaveManagerWindow               │
│  ┌─────────────┐     ┌─────────────┐        │
│  │  map_list   │ ──► │  save_list  │        │
│  └─────────────┘     └─────────────┘        │
│         │                   │               │
│         ▼                   ▼               │
│  ┌──────────────────────────────────┐       │
│  │         Action Buttons           │       │
│  │  [Backup] [Delete] [Export/Import]       │
│  └──────────────────────────────────┘       │
└─────────────────────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │    SAVES_PATH       │
         │ (OS'e göre değişir) │
         └─────────────────────┘
```

## Kritik Uygulama Yolları

### Yedekleme Akışı
1. Seçili map ve save al
2. Kaynak yolu oluştur
3. Tarih damgalı hedef yolu oluştur
4. `shutil.copytree()` ile kopyala
5. Liste güncelle, mesaj göster

### Dışa Aktarma Akışı
1. Seçili save yolunu al
2. Masaüstünde zip dosyası oluştur
3. Klasör yapısını koruyarak zip'e ekle
4. Başarı mesajı göster

### İçe Aktarma Akışı
1. Map seçili mi kontrol et
2. Zip dosyası seç
3. Aynı isimde save var mı kontrol et
4. Hedef map klasörüne çıkart
5. Liste güncelle
