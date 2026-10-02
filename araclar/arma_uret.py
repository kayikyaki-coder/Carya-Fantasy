"""Arma promptlarını Gemini API ile görsele çevirir.

Kullanım:
  GEMINI_API_KEY=... python3 araclar/arma_uret.py [--model MODEL] [aile adı parçası ...]
Anahtar repo içine yazılmaz; ortam değişkeninden okunur.
"""
import base64, json, os, re, sys, time, urllib.request, urllib.error

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(KOK, "rehber", "Arma_Promptlari.md")
CIKTI = os.path.join(KOK, "gorseller", "armalar_yeni")


def promptlari_oku():
    t = open(MD, encoding="utf-8").read()
    sehir = None
    sonuc = []
    for blok in re.split(r"\n(?=## |### )", t):
        m = re.match(r"## (.*) ailelerinin armaları", blok)
        if m:
            sehir = m.group(1).strip()
            continue
        m = re.match(r"### (.*)\n", blok)
        if m and sehir:
            p = re.search(r"```\n(.*?)\n```", blok, re.S)
            if p:
                sonuc.append((sehir, m.group(1).strip(), p.group(1).strip()))
    return sonuc


def dosya_adi(sehir, aile):
    s = f"{sehir}_{aile}".lower()
    for a, b in {"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "’": "", "'": ""}.items():
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_") + ".png"


def uret(model, prompt, anahtar):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    govde = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1"}},
    }
    istek = urllib.request.Request(url, data=json.dumps(govde).encode(), method="POST",
                                   headers={"Content-Type": "application/json", "x-goog-api-key": anahtar})
    with urllib.request.urlopen(istek, timeout=300) as r:
        d = json.load(r)
    for aday in d.get("candidates", []):
        for parca in aday.get("content", {}).get("parts", []):
            veri = parca.get("inlineData") or parca.get("inline_data")
            if veri and veri.get("data"):
                return base64.b64decode(veri["data"])
    raise RuntimeError("Görsel dönmedi: " + json.dumps(d)[:500])


def main():
    arg = sys.argv[1:]
    model = "gemini-3.1-flash-image"
    if "--model" in arg:
        i = arg.index("--model"); model = arg[i + 1]; del arg[i:i + 2]
    anahtar = os.environ.get("GEMINI_API_KEY")
    if not anahtar:
        sys.exit("GEMINI_API_KEY ortam değişkeni yok.")
    os.makedirs(CIKTI, exist_ok=True)
    liste = promptlari_oku()
    if arg:
        liste = [x for x in liste if any(a.lower() in x[1].lower() for a in arg)]
    for sehir, aile, prompt in liste:
        hedef = os.path.join(CIKTI, dosya_adi(sehir, aile))
        for deneme in range(3):
            try:
                png = uret(model, prompt, anahtar)
                open(hedef, "wb").write(png)
                print(f"OK  {sehir} / {aile} -> {os.path.relpath(hedef, KOK)}", flush=True)
                break
            except urllib.error.HTTPError as e:
                govde = e.read().decode()[:400]
                print(f"HATA {e.code} {sehir} / {aile}: {govde}", flush=True)
                if e.code == 429:
                    time.sleep(30 * (deneme + 1))
                    continue
                break
            except Exception as e:
                print(f"HATA {sehir} / {aile}: {e}", flush=True)
                break
        time.sleep(2)


if __name__ == "__main__":
    main()
