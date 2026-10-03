# Carya: Stable Diffusion ile gece görsel üretimi

Bu klasörde 115 hazır prompt ve sabaha kadar otomatik görsel üreten bir script var. Promptlar şehirler, tapınaklar, gruplar, mitoloji ve genel sahneler üzerine.

## Klasördekiler

| Dosya | Ne işe yarar |
|---|---|
| `promptlar.json` | 115 prompt (kategori, başlık, boyut) ve ortak negatif prompt. Script bunu okur. |
| `promptlar_a1111.txt` | Aynı promptlar, WebUI'nin "Prompts from file" eklentisi için satır satır. |
| `promptlar_liste.md` | Okunabilir liste. Tek tek kopyalamak istersen buradan al. |
| `gece_uret.py` | Sabaha kadar rastgele sırayla üreten script. |
| `gece_baslat.bat` | Windows'ta çift tıklayıp başlatmak için. |
| `ciktilar/` | Görseller buraya kategori klasörlerine ayrılarak düşer (otomatik oluşur). |

Bu klasörü bilgisayarında istediğin yere kopyala, örneğin `C:\Carya\gorsel_uretim`.

## 1. Hangi arayüz?

**Önerim: Stable Diffusion WebUI Forge.** AUTOMATIC1111 ile aynı görünür ama daha hızlıdır ve daha az ekran kartı belleği ister.
- İndirme: GitHub'da `lllyasviel/stable-diffusion-webui-forge`. "One-click package" zip'ini indir, aç, önce `update.bat`, sonra `run.bat`.
- AUTOMATIC1111 kurduysan o da olur, aşağıdakiler aynen geçerli.
- ComfyUI kurduysan script doğrudan çalışmaz. Bana söyle, ona göre bir workflow hazırlarım.

## 2. Hangi model?

Modeller civitai.com'dan indirilir. `.safetensors` dosyasını şu klasöre koy:
`webui\models\Stable-diffusion\` (Forge tek tık paketinde `webui\models\Stable-diffusion\`)

Ekran kartına göre seç:

| Ekran kartı belleği (VRAM) | Model | Neden |
|---|---|---|
| 8 GB ve üstü | **Juggernaut XL** (SDXL) | Sinematik, gerçekçi fantastik sahneler; şehir ve şövalye için çok iyi. |
| 8 GB ve üstü (alternatif) | **DreamShaper XL** | Daha resimsi, illüstrasyon havası. |
| 6 GB veya daha az | **DreamShaper 8** (SD 1.5) | Hafif. Bu durumda boyutları küçültmek gerekir, aşağıya bak. |

İkisini de indirip bir gece birini, öbür gece diğerini deneyebilirsin. Hangisi seçiliyse script onu kullanır: WebUI'de sol üstteki "Stable Diffusion checkpoint" menüsünden seç.

Ekran kartını bilmiyorsan: Görev Yöneticisi → Performans → GPU → "Ayrılmış GPU belleği".

## 3. API'yi aç (script için şart)

Script WebUI ile API üzerinden konuşur, bu yüzden WebUI `--api` ile açılmalı:
- AUTOMATIC1111: `webui-user.bat` dosyasını Not Defteri ile aç, şu satırı yap: `set COMMANDLINE_ARGS=--api`
- Forge tek tık paketi: `webui\webui-user.bat` içinde aynı satır.

Kaydet ve WebUI'yi o dosyayla yeniden başlat. Tarayıcıda `http://127.0.0.1:7860/docs` açılıyorsa API çalışıyor demektir.

## 4. Python

Bilgisayarda Python 3.10+ olmalı (WebUI kurulumu zaten istemiş olabilir). Ek paket gerekmez. Kontrol: komut satırında `python --version`.

## 5. Geceyi başlat

1. WebUI'yi aç ve modeli seç.
2. `gece_baslat.bat`'a çift tıkla. Saat 08:00'de kendisi durur.
3. Bilgisayarın uyku moduna geçmesini kapat: Ayarlar → Sistem → Güç → Uyku: "Hiçbir zaman".

Komut satırından ince ayar yapabilirsin:

```
python gece_uret.py --bitis 07:30          # 07:30'da dur
python gece_uret.py --adet 2               # her promptten her turda 2 görsel
python gece_uret.py --kategori kuzey,tapinak   # sadece bu kategoriler
python gece_uret.py --adim 25 --cfg 5.5    # daha hızlı / daha serbest
```

Kategoriler: `florentina, serenquill, venture, arcans_gate, aquamere, greenhall, kuzey, cuce, elf, ozgur, tapinak, gruplar, mitoloji, genel`

Script 115 promptu her turda karıştırır ve her görsele rastgele tohum verir. Böylece aynı prompt her turda farklı bir görsel çıkarır. Sabaha kadar tur tur dolaşır.

**Ne kadar çıkar?** SDXL ile orta bir kartta (RTX 3060 / 4060) bir görsel yaklaşık 15–30 saniye sürer. 8 saatte kabaca 1000–1500 görsel eder, yani her prompt için 10 civarı varyasyon.

## Varsayılan ayarlar

- Sampler: DPM++ 2M, scheduler: Karras, 30 adım, CFG 6
- Boyutlar: yatay 1216×832, dikey 832×1216 (SDXL için ideal)
- **SD 1.5 model kullanıyorsan** boyutlar fazla büyük gelir. `promptlar.json` içinde 1216→768 ve 832→512 yap, ya da bana söyle, ben ayrı bir dosya hazırlayayım.
- Hata alırsan (sampler adı farklı vs.) `--sampler "DPM++ 2M Karras" --scheduler ""` dene.

## Script olmadan (WebUI'nin kendi yöntemiyle)

1. txt2img sekmesinde en alttaki **Script** menüsünden **"Prompts from file or textbox"** seç.
2. `promptlar_a1111.txt` dosyasını yükle.
3. **Batch count** değerini 4 yap: 115 × 4 = 460 görsel.
4. Generate'e bas. Görseller WebUI'nin `outputs` klasörüne düşer.

Dezavantajı: liste bitince durur ve kategori klasörlerine ayırmaz.

## Sabah

`ciktilar/` içinde kategori klasörleri olacak. Dosya adı `numara_başlık_tohum.png` biçiminde. Beğendiğinin tohumunu ve numarasını bana söylersen o promptu geliştiririz.
