"""Download Amazon product images for all 20 products.

Tries several URL patterns per ASIN and keeps the largest (best) result.
Flags anything under 8KB as a likely placeholder.
Saves to images/<asin>.jpg.
"""
import os
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "images")
os.makedirs(IMG_DIR, exist_ok=True)

# All 20 products: (asin, short_name)
PRODUCTS = [
    ("B00FLYWNYQ", "instant-pot"),
    ("B07FDJMC9Q", "ninja-af101"),
    ("B00005UP2P", "kitchenaid"),
    ("B018UQ5AMS", "keurig"),
    ("B0979R48CX", "dyson-v15"),
    ("B00TTD9BRC", "cerave"),
    ("B003UKM9CO", "oralb-pro1000"),
    ("B00SNM5US4", "olaplex-3"),
    ("B01MDTVZTZ", "ordinary-niacinamide"),
    ("B00MEDOY2G", "dove-bodywash"),
    ("B01GSAXOVW", "levis-501"),
    ("B000VKQZUI", "hanes-ecosmart"),
    ("B002Q1P12S", "rayban-wayfarer"),
    ("B0D4TDQKY4", "nike-af1"),
    ("B09B2YNGSN", "fossil-gen6"),
    ("B0CHWRXH8B", "airpods-pro2"),
    ("B09XS7JWHH", "sony-wh1000xm5"),
    ("B0CMDRCZBJ", "galaxy-s24"),
    ("B09B8V1LZ3", "echo-dot-5"),
    ("B0BJLXMVMV", "ipad-10"),
]

# URL format patterns to try, ordered by preference
PATTERNS = [
    "https://images-na.ssl-images-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg",
    "https://m.media-amazon.com/images/P/{asin}.01._SCLZZZZZZZ_.jpg",
    "https://images-na.ssl-images-amazon.com/images/P/{asin}.01.L.jpg",
    "https://images-na.ssl-images-amazon.com/images/P/{asin}.01.LZZZZZZZ.jpg",
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MIN_BYTES = 8000  # anything smaller is likely a placeholder


def fetch(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=12) as r:
            if r.status != 200:
                return None
            if not r.headers.get("Content-Type", "").startswith("image/"):
                return None
            return r.read()
    except Exception:
        return None


def best_image(asin):
    best = None
    best_url = None
    for pat in PATTERNS:
        data = fetch(pat.format(asin=asin))
        if data is None:
            continue
        if best is None or len(data) > len(best):
            best = data
            best_url = pat.format(asin=asin)
    return best, best_url


def main():
    results = []
    for asin, short in PRODUCTS:
        data, url = best_image(asin)
        if data is None:
            print(f"[FAIL] {asin} {short}: no pattern returned an image")
            results.append((asin, short, None, 0))
            continue
        size = len(data)
        status = "OK" if size >= MIN_BYTES else "SMALL"
        out_path = os.path.join(IMG_DIR, f"{asin}.jpg")
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"[{status}] {asin} {short}: {size} bytes from {url.rsplit('/', 2)[-1]}")
        results.append((asin, short, out_path, size))
    print()
    fails = [r for r in results if r[3] < MIN_BYTES]
    print(f"Total: {len(results)}  OK: {len(results) - len(fails)}  Flagged: {len(fails)}")
    if fails:
        print("Flagged (likely placeholder, need fallback):")
        for asin, short, _, size in fails:
            print(f"  - {asin} {short} ({size} bytes)")


if __name__ == "__main__":
    main()
