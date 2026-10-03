"""Carya gece üretimi: Stable Diffusion WebUI (Forge / AUTOMATIC1111) API'si ile
promptlar.json'daki promptlardan sabaha kadar rastgele görsel üretir.

Kullanım:  python gece_uret.py                 (sabah 08:00'e kadar)
           python gece_uret.py --bitis 07:30   (bitiş saati)
           python gece_uret.py --adet 2        (her turda prompt başına görsel)
Önce WebUI '--api' ile açık olmalı. Ek kurulum gerekmez (yalnızca Python).
"""
import argparse, base64, datetime as dt, json, os, random, sys, time, urllib.request

KLASOR = os.path.dirname(os.path.abspath(__file__))
p = argparse.ArgumentParser()
p.add_argument("--adres", default="http://127.0.0.1:7860")
p.add_argument("--bitis", default="08:00", help="SS:DD, bu saatte durur")
p.add_argument("--adet", type=int, default=1, help="her turda prompt başına görsel")
p.add_argument("--adim", type=int, default=30, help="sampling steps")
p.add_argument("--cfg", type=float, default=6.0)
p.add_argument("--sampler", default="DPM++ 2M")
p.add_argument("--scheduler", default="Karras")
p.add_argument("--kategori", default="", help="ör. kuzey,florentina (boş = hepsi)")
a = p.parse_args()
sys.stdout.reconfigure(line_buffering=True)

veri = json.load(open(os.path.join(KLASOR, "promptlar.json"), encoding="utf-8"))
liste = veri["promptlar"]
if a.kategori:
    istenen = set(a.kategori.split(","))
    liste = [x for x in liste if x["kategori"] in istenen]

simdi = dt.datetime.now()
s, d = map(int, a.bitis.split(":"))
bitis = simdi.replace(hour=s, minute=d, second=0)
if bitis <= simdi:
    bitis += dt.timedelta(days=1)
print(f"{len(liste)} prompt, bitiş: {bitis:%d.%m %H:%M}")

def istek(govde):
    r = urllib.request.Request(a.adres + "/sdapi/v1/txt2img", data=json.dumps(govde).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=900) as y:
        return json.loads(y.read())

sayac, tur = 0, 0
while dt.datetime.now() < bitis:
    tur += 1
    random.shuffle(liste)
    for x in liste:
        if dt.datetime.now() >= bitis:
            break
        for _ in range(a.adet):
            tohum = random.randint(0, 2**31 - 1)
            govde = {"prompt": x["prompt"], "negative_prompt": veri["negatif"],
                     "width": x["genislik"], "height": x["yukseklik"], "steps": a.adim,
                     "cfg_scale": a.cfg, "sampler_name": a.sampler, "scheduler": a.scheduler,
                     "seed": tohum}
            try:
                sonuc = istek(govde)
            except Exception as e:
                print("Hata (WebUI --api ile açık mı?):", e); time.sleep(30); continue
            hedef = os.path.join(KLASOR, "ciktilar", x["kategori"])
            os.makedirs(hedef, exist_ok=True)
            ad = f'{x["no"]:03d}_{x["baslik"].replace(" ", "_")}_{tohum}'
            with open(os.path.join(hedef, ad + ".png"), "wb") as f:
                f.write(base64.b64decode(sonuc["images"][0]))
            sayac += 1
            print(f'[{dt.datetime.now():%H:%M}] tur {tur} #{sayac}: {x["kategori"]}/{ad}.png')
print(f"Bitti: {sayac} görsel üretildi -> ciktilar/")
