# Carya Haritası

- `carya_haritasi_etiketli.jpg`: Şehir adlarıyla işaretlenmiş harita; imparatorluk kasabaları da işlenmiştir (küçük içi boş daireler). `araclar/harita_kasabalar.py` ile üretilir.
- `carya_haritasi_etiketli_eski.jpg`: Kasabalar eklenmeden önceki orijinal etiketli harita (yedek; betik bunu kaynak olarak kullanır, değiştirmeyin).
- `carya_haritasi_bos.png`: Aynı kıtanın etiketsiz taslağı.

Kasabaların konumları `metin/imparatorluk/kasabalar.md` metinlerindeki ipuçlarına göre seçildi (örneğin Zevk Adası Florentina açıklarında bir ada, Kara Liman Venture'ın güneyinde bir liman, Son Kale Serenquill'in kuzeyinde). Bir konumu değiştirmek için betikteki `KASABALAR` listesini düzenleyip `python3 araclar/harita_kasabalar.py` çalıştırın, ardından siteyi `python3 araclar/site_olustur.py` ile yeniden üretin.
