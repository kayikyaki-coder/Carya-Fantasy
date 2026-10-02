# Carya Evreni — Yazım ve Biçim Standardı

Bu standart, Yeryüzü Tapınağı belgesinin Word tasarımı model alınarak belirlendi. Tüm metinler `metin/` altında Markdown olarak tutulur; Word çıktıları `araclar/docx_olustur.py` ile bu dosyalardan üretilir (`docx/` klasörü).

## 1. Markdown kuralları

- Her dosya bir bölümle başlar: `# Başlık` (H1 = bölüm). Alt başlıklar `##` ve `###` ile verilir. H4 kullanılmaz.
- Başlıklarda `**kalın**`, görsel, HTML, ters bölü veya boş başlık olmaz. Başlıklar Türkçe başlık biçimindedir (Her Kelimenin İlk Harfi Büyük; bağlaç ve ekler küçük).
- Gövde metni düz paragraftır. Satır sonu boşluğu, `\` ve `<br>` yoktur. Vurgu için `*italik*` ve `**kalın**` kullanılır.
- Listeler `- ` ile yazılır. Tablolar standart pipe (`| a | b |`) tablosudur ve ilk satır başlıktır.
- Alıntı, dua, ağıt, kutsal metin ve kehanet gibi bloklar `> ` ile yazılır; her paragraf ayrı `> ` satırıdır (araya boş `>` satırı).
- Sahne/bölüm arası ayracı tek başına `* * *` satırıdır.
- Amblem/görsel: başlığın hemen altında tek başına bir satır, `![Ad](../gorseller/media/imageN.png)`. Görseller `metin/gorseller/media/` altındadır. Satır içi (`<img>`) görsel kullanılmaz.
- Metin içinde editör notu, yapay zekâ taslak cümlesi, sohbet cümlesi veya yorum bırakılmaz.
- Yazım: Türkçe tırnak olarak düz `"` yerine `“ ”`, kesme için `’` kullanılır. Bir dosya içinde tutarlı olsun yeter; mevcut metni değiştirmeyin, yalnızca bariz yazım hatasını düzeltin.

## 2. Kanonik yazımlar

| Doğru | Kullanılmayacak |
|---|---|
| Serenquill | Serenquell |
| De Santis | De Santics |
| Gork | Gorg |
| Arcan | Arkan |
| Greatwolf | Büyükkurt / Great Wolf (metin içinde) |
| Yeryüzü Tapınağı | İmparatorluk Tapınağı, İmparatorluk Kilisesi (aynı kurum için) |
| İlericiler Tapınağı | (tanrılar topluluğu için; Yeryüzü Tapınağı ile karıştırılmaz) |

Harita adları (Ventura, Cortas, Aalsidente, Hegos, Sanland, Cogurastem, Trumdilm) metinlerdeki adlarla (Venture, Cortax, Aal Silente, Herbs, Sunland, Cogvrastum, Trumheim) birebir örtüşmüyor; hangisinin doğru olduğu yazara sorulana kadar metindeki yazım korunur.

## 3. Word tasarımı (Yeryüzü Tapınağı stili)

- Sayfa: A4, kenar boşlukları 2,54 cm.
- Yazı tipi: Georgia, her yerde. Gövde 11 pt, iki yana yaslı, satır aralığı 1,15, paragraf sonrası 8 pt.
- Kapak sayfası: Başlık 26 pt kalın ortalı (üstte 60 pt boşluk), alt başlık 14 pt italik, altında `#5B4A2E` renginde ince çizgi, ardından 12 pt italik yazar satırı ve italik açıklama; sonra sayfa sonu.
- H1: 16 pt kalın, `#5B4A2E`, önce 18 pt, sonra 10 pt. H2: 13 pt kalın, `#6E5A38`, önce 12 pt, sonra 7 pt. H3: 11,5 pt kalın italik, `#6E5A38`, önce 10 pt, sonra 5 pt.
- Liste: sol girinti 0,5", asılı girinti 0,25", sonrası 4 pt.
- Alıntı bloğu: italik, sol girinti 0,5", sol kenarda `#C9B681` ince çizgi, sonrası 6 pt.
- Ayraç `* * *`: ortalı, `#6E5A38`.
- Tablo: tam genişlik, hücre kenarlığı `#C9B681`, başlık satırı dolgusu `#5B4A2E` beyaz kalın yazı, gövde satırları dolgusu `#FBF7EC`, hücre iç boşluğu 80/120 twip.
- Amblem: ortalı, 3 cm.
- Alt bilgi: ortalı sayfa numarası, Georgia 9 pt, `#6E5A38` (kapak sayfasında yok).
