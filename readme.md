# 7 Days To Die Save Yedekleme Aracı

7 Days To Die için save dosyalarını yedekleme, dışa aktarma ve silme işlemlerinde kolaylık sağlar. Arayüz PySide6 ile hazırlanmış, koyu tema ve çoklu dil desteği içerir.

**İçindekiler**
- [Quick Start](#quick-start)
- [Kurulum](#kurulum)
- [Kendi Build'inizi Oluşturma](#kendi-buildinizi-olu%C5%9Fturma)
- [Konfigürasyon & Ayarlar](#konfig%C3%BCrasyon--ayarlar)
- [Katkıda Bulunma](#katk%C4%B1da-bulunma)
- [Yapay Zeka ile Geliştirme Süreci](#-yapay-zeka-ile-geli%C5%9Ftirme-s%C3%BCreci)
- [Videolu anlatım](#videolu-anlat%C4%B1m)

## Quick Start

```bash
pip install -r requirements.txt
python 7DaysToBackup.py
```

## Kurulum

Bu aracı kullanabilmek için bilgisayarınızda Python ve gerekli kütüphanelerin kurulu olması gerekir.

```bash
pip install -r requirements.txt
```

İsterseniz [yayımlananlar](https://github.com/umityatarkalkmaz/7DaysToBackup/releases/) arasından exe indirebilirsiniz.
Build durumunu buradan görüp exe hazır mı kontrol edebilirsiniz: [![Auto Release & Build](https://github.com/umityatarkalkmaz/7DaysToBackup/actions/workflows/auto-release.yml/badge.svg)](https://github.com/umityatarkalkmaz/7DaysToBackup/actions/workflows/auto-release.yml)

## Güvenlik Uyarısı

> ⚠️ **EXE dosyası indirilirken güvenlik uyarısı alabilirsiniz:**  
> Bu uygulama imzalanmamış bir EXE olarak dağıtılmaktadır, bu nedenle bazı antivirüs programları tarafından potansiyel bir tehdit olarak algılanabilir. Bu, uygulamanın güvensiz olduğu anlamına gelmez; ancak güvenlik endişeleriniz varsa, aşağıdaki adımları takip ederek uygulamayı kendiniz derleyebilirsiniz.

## Kendi Build'inizi Oluşturma

Eğer güvenlik endişeleriniz varsa veya sadece projeyi kendiniz derlemek istiyorsanız, aşağıdaki adımları takip edebilirsiniz.

1. Python'u bilgisayarınıza kurun.  
   Daha fazla bilgi için [Python Downloads](https://www.python.org/downloads/).

2. Projeyi bilgisayarınıza klonlayın veya indirin.

3. Terminal veya komut satırından proje dizinine gidin.

4. Bağımlılıkları yükleyin:

   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

5. Build alma:

   ### PyInstaller ile

   ```bash
   pyinstaller 7DaysToBackup.py -F -w
   ```

   **dist** klasöründe `7DaysToBackup.exe` oluşacaktır.

   ### Auto-py-to-exe ile

   ```bash
   pip install auto-py-to-exe
   auto-py-to-exe
   ```

   GUI açıldığında:

   - Script Location: `7DaysToBackup.py`
   - Onefile: ✔
   - Window-Based: ✔  
     Ardından *Convert .py to .exe* butonuna basın.

6. **dist** veya **output** klasöründen `7DaysToBackup.exe` dosyasını alıp çalıştırabilirsiniz.

## 🤖 Yapay Zeka ile Geliştirme Süreci

Bu proje, modern yazılım geliştirme pratiklerine ayak uydurarak geliştirme sürecine yapay zekayı tam anlamıyla entegre etmiştir. Kod kalitesini artırmak, dokümantasyonu canlı tutmak ve sürdürülebilirliği sağlamak adına **Cline** ve **Memory Bank** konseptleri aktif olarak kullanılmaktadır.

* **Cline's Memory Bank:** Projenin bağlamını, mimari kararlarını ve gelecek planlarını "canlı" bir bellek yapısında tutarak, yapay zeka asistanının projeye her an hakim olmasını ve katkı vermesini sağlar.
* **Modern Teknoloji Adaptasyonu:** Gelişen teknolojiler ve AI destekli araçlar sayesinde, kod refaktörü, hata ayıklama ve yeni özellik geliştirme süreçleri optimize edilmiştir. Proje sürekli olarak güncel teknolojilerle beslenmektedir.

## Konfigürasyon & Ayarlar

Uygulama `config.json` dosyasında kullanıcı tercihlerini saklar (dil, özel save yolu vb.). `Settings` penceresinden bu ayarları düzenleyebilirsiniz. `config.json` varsayılan olarak uygulama verisi klasöründe oluşturulur.

## Katkıda Bulunma

Katkıda bulunmak isterseniz aşağıdaki akışı kullanın:

```bash
git clone https://github.com/umityatarkalkmaz/7DaysToBackup.git
cd 7DaysToBackup
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
\.venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
python 7DaysToBackup.py
```

- Fork → yeni branch (örn. `feat/my-feature`) → commit & PR
- Commit mesajı: `feat:`, `fix:`, `chore:`, veya `BREAKING CHANGE:` kullanın (otomatik semver için önerilir).

## Ekran Görüntüleri

Ekran görüntüleri `assets/screenshots/` klasöründe saklanacaktır. Şu an görseller eklenmemiştir; cihaz değiştirdiğinizde yüksek çözünürlüklü görüntüleri ekleyebilirsiniz.

## Videolu anlatım

[7 Days to die Save Yedekleme Aracım Hızlı ve Kolay | Mini Rehber Days](https://youtu.be/t4v6_USS3cY?si=K0U2gpJxR6D9_gG3)
