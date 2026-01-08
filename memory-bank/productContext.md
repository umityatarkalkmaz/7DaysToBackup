# Product Context - 7DaysToBackup

## Neden Bu Proje Var?
7 Days to Die oyuncuları save dosyalarını manuel olarak yönetmek zorunda kalıyor. Bu uygulama:
- Save dosyalarının kaybolma riskini azaltır
- Farklı oyun durumlarını denemeyi kolaylaştırır
- Save dosyalarını arkadaşlarla paylaşmayı sağlar

## Çözdüğü Problemler
1. **Manuel yedekleme zorluğu**: Kullanıcılar AppData gibi karmaşık klasörlere gitmek zorunda kalmaz
2. **Platform farklılıkları**: Her işletim sisteminde farklı olan save konumlarını otomatik bulur
3. **Organize olmayan save'ler**: Map ve save listesi ile düzenli görünüm sağlar
4. **Paylaşım zorluğu**: Zip formatında dışa aktarma ile kolay paylaşım

## Nasıl Çalışmalı?
1. Uygulama açıldığında mevcut map'leri listeler
2. Map seçildiğinde o map'e ait save'ler gösterilir
3. Kullanıcı istediği işlemi (yedekle, sil, dışa/içe aktar) tek tıkla yapar
4. Tüm işlemler onay ve bilgilendirme mesajları ile desteklenir

## Kullanıcı Deneyimi Hedefleri
- **KARANLIK TEMA KUTSALDIR**: UI her zaman karanlık temaya uygun olarak geliştirilmelidir. Beyaz/açık temalar yasaktır. 🌑
- **Basitlik**: Tek pencere, anlaşılır butonlar
- **Güvenlik**: Silme işlemlerinde onay isteme
- **Bilgilendirme**: Her işlem sonrası başarı/hata mesajı
- **Erişilebilirlik**: Koyu tema, okunabilir fontlar
- **Çoklu dil**: Türkçe ve İngilizce arayüz seçimi
