# 7 Days To Die Save Yedekleme Aracı

7 Days To Die için save dosyalarını yedekleme, dışa aktarma ve silme işlemlerinde kolaylık sağlar. Arayüz artık PySide6 ile hazırlanmış koyu tema kullanmaktadır.

## Kurulum

Bu aracı kullanabilmek için bilgisayarınızda Python ve PySide6 kütüphanesinin kurulu olması gerekir.

```bash
pip install PySide6
```

İsterseniz [yayımlananlar](https://github.com/umityatarkalkmaz/7DaysToBacup/releases/) arasından exe indirebilirsiniz.
Build durumunu buradan görüp exe hazır mı kontrol edebilirsiniz: [![Build](https://github.com/umityatarkalkmaz/7DaysToBackup/actions/workflows/build.yml/badge.svg)](https://github.com/umityatarkalkmaz/7DaysToBackup/actions/workflows/build.yml)

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
   pip install PySide6 pyinstaller
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

## Videolu anlatım

[7 Days to die Save Yedekleme Aracım Hızlı ve Kolay | Mini Rehber Days](https://youtu.be/t4v6_USS3cY?si=K0U2gpJxR6D9_gG3)
