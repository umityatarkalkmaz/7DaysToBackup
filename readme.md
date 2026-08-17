# 7 Days To Die Save Yedekleme Aracı (Python)

7 Days To Die için save dosyalarını yedekleme, dışa aktarma ve silme işlemlerinde kolaylık sağlar. Arayüz PySide6 ile hazırlanmış, koyu tema ve çoklu dil desteği içerir.

> ### 📦 Bu sürüm bakım modunda
>
> Geliştirme **[7DaysToBackup-rust](https://github.com/umityatarkalkmaz/7DaysToBackup-rust)** deposuna taşındı. Yeni özellikler orada geliştiriliyor: yedek geçmişi ve geri yükleme, çoklu save seçimi, otomatik yedekleme, ayarlanabilir arayüz ölçeği. Rust sürümü tek dosya olarak çalışır — hedef makinede Python veya Qt kurulu olmasına gerek yoktur.
>
> **Bu depo kapatılmadı.** Python sürümü çalışmaya devam ediyor ve kullanılabilir. Buradaki durum şu:
>
> | | Durum |
> |---|---|
> | Kullanım | Destekleniyor, indirilebilir |
> | Hata bildirimi | Açık — [issue](https://github.com/umityatarkalkmaz/7DaysToBackup/issues) açabilirsiniz |
> | Topluluk PR'ları | **Açık ve memnuniyetle karşılanır** |
> | Bakımcıdan yeni özellik | Gelmeyecek |
>
> Python sürümünde bir özellik görmek istiyorsanız yolu açık: kendiniz yazıp PR gönderin. Gelen katkılar incelenip birleştirilir.

**İçindekiler**
- [Quick Start](#quick-start)
- [Kurulum](#kurulum)
- [Kendi Build'inizi Oluşturma](#kendi-buildinizi-olu%C5%9Fturma)
- [Konfigürasyon & Ayarlar](#konfig%C3%BCrasyon--ayarlar)
- [Katkıda Bulunma](#katk%C4%B1da-bulunma)
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

## Konfigürasyon & Ayarlar

Uygulama `config.json` dosyasında kullanıcı tercihlerini saklar (dil, özel save yolu vb.). `Settings` penceresinden bu ayarları düzenleyebilirsiniz. `config.json` varsayılan olarak uygulama verisi klasöründe oluşturulur.

## Katkıda Bulunma

Proje bakım modunda olduğu için yeni özellikler artık topluluktan geliyor. Hata düzeltmeleri ve özellik PR'ları açık; küçük bir düzeltme için önce issue açmanıza gerek yok.

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
- Testleri koşturun: `pytest`

Rust sürümüne katkı vermek isterseniz o depo ayrı: [7DaysToBackup-rust](https://github.com/umityatarkalkmaz/7DaysToBackup-rust).

## Videolu anlatım

[7 Days to die Save Yedekleme Aracım Hızlı ve Kolay | Mini Rehber Days](https://youtu.be/t4v6_USS3cY?si=K0U2gpJxR6D9_gG3)
