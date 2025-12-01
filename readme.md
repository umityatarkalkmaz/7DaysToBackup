# 7 Days To Die Save Yedekleme Aracı

7 Days To Die için save dosyalarını yedekleme, dışa aktarma ve silme işlemlerinde kolaylık sağlar. Arayüz artık PySide6 ile hazırlanmış koyu tema kullanmaktadır.

## Kurulum

Bu aracı kullanabilmek için bilgisayarınızda Python ve PySide6 kütüphanesinin kurulu olması gerekir.

```bash
pip install PySide6
```

İsterseniz [yayımlananlar](https://github.com/umityatarkalkmaz/7DaysToBacup/releases/) arasından exe indirebilirsiniz.

## Güvenlik Uyarısı

> :warning: **EXE dosyası indirilirken güvenlik uyarısı alabilirsiniz:** Bu uygulama imzalanmamış bir EXE olarak dağıtılmaktadır, bu nedenle bazı antivirüs programları tarafından potansiyel bir tehdit olarak algılanabilir. Bu, uygulamanın güvensiz olduğu anlamına gelmez; ancak güvenlik endişeleriniz varsa, aşağıdaki adımları takip ederek uygulamayı kendiniz derleyebilirsiniz.

## Kendi Build'inizi Oluşturma

Eğer güvenlik endişeleriniz varsa veya sadece projeyi kendiniz derlemek istiyorsanız, aşağıdaki adımları takip edebilirsiniz. Bu işlem için Python ve PyInstaller gerekmektedir.

1. Python'u bilgisayarınıza kurun. Python kurulumu hakkında daha fazla bilgi için [Python'un resmi web sitesine](https://www.python.org/downloads/) göz atabilirsiniz.

2. Projeyi bilgisayarınıza klonlayın veya indirin.

3. Komut satırı veya terminal açın ve proje dizinine gidin.

4. Gerekli bağımlılıkları yükleyin:

   ```bash
   pip install PySide6 pyinstaller
   ```

5. Build alma

   1. PyInstaller'ı kullanarak EXE dosyasını oluşturun. Proje dizininde aşağıdaki komutları çalıştırın

      ```bash
      pyinstaller 7DaysToBackup.py -F -w
      ```

      Bu komut, dist adında bir klasör içinde 7DaysToBackup.exe adında tek bir çalıştırılabilir dosya oluşturur.

   2. Auto-py-to-exe ile Build Oluşturma

      1. Auto-py-to-exe'yi kurun:

      ```bash
      pip install auto-py-to-exe
      ```

      2. Auto-py-to-exe'yi çalıştırın:

      ```bash
      auto-py-to-exe
      ```

      Açılan grafik arayüzde şu adımları takip edin:

      Script Location: 7DaysToBackup.py dosyasını seçin.

      Onefile: "One File" seçeneğini işaretleyin (Bu, tek bir EXE dosyası oluşturur).

      Window Based (hide the console): "Window Based" seçeneğini seçin (Bu, konsol penceresinin görünmesini engeller).

      Ayarları yaptıktan sonra Convert .py to .exe düğmesine tıklayın.

6. **dist** veya **output** klasörünü açın ve **7DaysToBackup.exe** dosyasını bulun. Bu dosya, uygulamanızın EXE versiyonudur ve herhangi bir yükleme işlemine gerek kalmadan doğrudan çalıştırılabilir.
   Bu adımları takip ederek, güvenlik uyarılarına maruz kalmadan ve güvenlik şüpheniz varsa, güvenliğinizi riske atmadan uygulamayı güvenle kullanabilirsiniz.

### Videolu anlatım

[7 Days to die Save Yedekleme Aracım Hızlı ve Kolay | Mini Rehber Days](https://youtu.be/t4v6_USS3cY?si=K0U2gpJxR6D9_gG3)
