# Tech Context - 7DaysToBackup

## Kullanılan Teknolojiler

### Ana Framework
- **Python 3.x** - Ana programlama dili
- **PySide6** (Qt6) - GUI framework

### Standart Kütüphaneler
- `os` - Dosya sistemi işlemleri
- `platform` - İşletim sistemi tespiti
- `shutil` - Dosya kopyalama/silme
- `zipfile` - Zip arşiv işlemleri
- `datetime` - Tarih/saat formatı
- `sys` - Sistem işlemleri
- `typing` - Type hints

## Geliştirme Ortamı

### Gereksinimler
```
PySide6==6.10.1
PySide6_Addons==6.10.1
PySide6_Essentials==6.10.1
shiboken6==6.10.1
```

### Kurulum
```bash
pip install -r requirements.txt
```

### Çalıştırma
```bash
python 7DaysToBackup.py
```

### Build (EXE)
```bash
pyinstaller 7DaysToBackup.py -F -w
```

## Teknik Kısıtlamalar
- PySide6 sadece Python 3.7+ destekler
- Qt framework bazı eski sistemlerde sorun çıkarabilir
- EXE dosyası imzasız olduğu için antivirüs uyarısı verebilir

## Dosya Yapısı
```
7DaysToBackup/
├── 7DaysToBackup.py    # Entry point wrapper
├── src/                # Kaynak kodlar
│   ├── main.py         # Ana uygulama başlatıcı
│   ├── core/           # Çekirdek işlevler
│   │   └── platform.py # OS ve yol işlemleri
│   ├── ui/             # Kullanıcı arayüzü
│   │   ├── window.py   # Ana pencere
│   │   └── theme.py    # Tema ayarları
│   └── i18n/           # Çoklu dil desteği
│       └── languages.py # Çeviriler
├── requirements.txt    # Bağımlılıklar
├── readme.md          # Dokümantasyon
├── LICENSE            # Lisans
└── memory-bank/       # Proje bellek dosyaları
```

## Save Lokasyonları (İşletim Sistemine Göre)
| OS | Konum |
|----|-------|
| Windows | `%APPDATA%\7DaysToDie\Saves` |
| macOS | `~/Library/Application Support/7DaysToDie/Saves` |
| Linux | `~/.local/share/7DaysToDie/Saves` |
