# System Patterns - 7DaysToBackup

## Mimari Yapı

### Dosya Organizasyonu
```
7DaysToBackup.py   → Ana uygulama (UI + iş mantığı)
languages.py       → Çeviri sözlüğü
```

### Sınıf Yapısı
```
SaveManagerWindow (QMainWindow)
├── __init__()           → Başlatma
├── _setup_ui()          → UI kurulumu
├── change_language()    → Dil değiştirme
├── load_maps()          → Map listesi yükleme
├── load_saves()         → Save listesi yükleme
├── backup_save()        → Yedekleme
├── delete_save()        → Silme
├── export_save()        → Dışa aktarma
├── import_save()        → İçe aktarma
├── _selected_map()      → Seçili map
├── _selected_paths()    → Seçili yollar
├── _show_info()         → Bilgi mesajı
└── _show_error()        → Hata mesajı
```

## Tasarım Desenleri

### 1. Helper Functions (Yardımcı Fonksiyonlar)
- `get_os_type()` - İşletim sistemi tespiti
- `get_saves_path()` - Save yolu belirleme
- `get_desktop_path()` - Masaüstü yolu belirleme
- `create_dark_palette()` - Koyu tema oluşturma

### 2. Çeviri Sistemi
```python
LANGUAGES = {
    'tr': { ... },
    'en': { ... }
}
```
- Anahtar-değer çiftleri ile çeviri
- Format string desteği: `"mesaj: {}".format(değer)`

### 3. Hata Yönetimi
- `try-except` blokları ile güvenli işlemler
- `ValueError` özel hata durumları için
- Genel `Exception` beklenmedik hatalar için

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
