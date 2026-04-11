"""Generate a static storefront with real Amazon links + images + daily rotation.

Run: python generate.py
Output: index.html, 4 category pages, 20 product pages, style.css
Data source: Amazon CDN for product images (downloaded at build time to images/).
"""
import os
import html
import json
import re
import urllib.request
import urllib.parse
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "images")
os.makedirs(IMG_DIR, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Amazon Associates tracking tag. Override with env var AMAZON_AFFILIATE_TAG.
AFFILIATE_TAG = os.environ.get("AMAZON_AFFILIATE_TAG", "bestsellin092-20")


def affiliate_url(url):
    """Append the Amazon affiliate tracking tag to any amazon.com URL."""
    if not url or "amazon." not in url:
        return url
    if "tag=" in url:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}tag={AFFILIATE_TAG}"


# ---- Product catalog with real Amazon ASINs/URLs ----
CATEGORIES = [
    {
        "slug": "home-kitchen",
        "name": "Home & Kitchen",
        "tagline": "Essentials for cooking, cleaning, and comfort.",
        "accent": "#c97b63",
        "icon": "\u2756",
        "products": [
            {
                "asin": "B00FLYWNYQ",
                "name": "Instant Pot Duo 7-in-1 Pressure Cooker",
                "blurb": "6-quart multi-cooker that replaces seven separate appliances.",
                "price": "$89.99",
                "story": "The original all-in-one kitchen workhorse. A single stainless-steel pot pressure cooks, slow cooks, steams rice, sautés, makes yogurt, and warms leftovers. 13 smart programs and a tri-ply bottom for even heating.",
                "url": "https://www.amazon.com/Instant-Pot-Multi-Use-Programmable-Pressure/dp/B00FLYWNYQ",
            },
            {
                "asin": "B07FDJMC9Q",
                "name": "Ninja AF101 Air Fryer",
                "blurb": "4-quart ceramic-coated basket that crisps food with little to no oil.",
                "price": "$99.99",
                "story": "Four one-touch presets (air fry, roast, reheat, dehydrate), a 105°F-400°F temperature range, and a dishwasher-safe basket and crisper plate. Recipe book ships in the box.",
                "url": "https://www.amazon.com/Ninja-AF101-Fryer-Black-gray/dp/B07FDJMC9Q",
            },
            {
                "asin": "B00005UP2P",
                "name": "KitchenAid Artisan Stand Mixer",
                "blurb": "5-quart tilt-head stand mixer with 10 speeds.",
                "price": "$449.99",
                "story": "The gold standard for home baking. A 325-watt motor handles bread dough, whipped cream, and everything in between. Accepts 10+ attachments via the front PowerHub.",
                "url": "https://www.amazon.com/KitchenAid-KSM150PSER-Artisan-Tilt-Head-Pouring/dp/B00005UP2P",
            },
            {
                "asin": "B018UQ5AMS",
                "name": "Keurig K-Classic Coffee Maker",
                "blurb": "Brews 6, 8, and 10 oz cups from K-Cup pods in under a minute.",
                "price": "$99.99",
                "story": "A 48-ounce reservoir means four cups between refills. Removable drip tray fits travel mugs up to 7.2 inches, and descaling mode keeps it running clean for years.",
                "url": "https://www.amazon.com/Keurig-K55-K-Classic-Coffee-Programmable/dp/B018UQ5AMS",
            },
            {
                "asin": "B0979R48CX",
                "name": "Dyson V15 Detect Cordless Vacuum",
                "blurb": "Laser-illuminated dust detection with HEPA filtration and 60-minute runtime.",
                "price": "$749.99",
                "story": "A precisely-angled green laser reveals invisible dust on hard floors, while a piezo sensor counts and sizes particles in real time. Whole-machine HEPA seal captures 99.99% of particles down to 0.3 microns.",
                "url": "https://www.amazon.com/Dyson-Detect-Cordless-Vacuum-Yellow/dp/B0979R48CX",
            },
        ],
    },
    {
        "slug": "beauty-personal-care",
        "name": "Beauty & Personal Care",
        "tagline": "Daily-routine staples dermatologists and stylists actually recommend.",
        "accent": "#b5838d",
        "icon": "\u273f",
        "products": [
            {
                "asin": "B00TTD9BRC",
                "name": "CeraVe Moisturizing Cream",
                "blurb": "Fragrance-free daily moisturizer with three essential ceramides.",
                "price": "$18.99",
                "story": "Developed with dermatologists, this non-greasy cream uses MVE technology to release hyaluronic acid and ceramides throughout the day. Non-comedogenic and suitable for face and body on normal to very dry skin.",
                "url": "https://www.amazon.com/CeraVe-Moisturizing-Cream-Daily-Moisturizer/dp/B00TTD9BRC",
            },
            {
                "asin": "B003UKM9CO",
                "name": "Oral-B Pro 1000 Electric Toothbrush",
                "blurb": "Rechargeable rotating toothbrush with pressure sensor and 2-minute timer.",
                "price": "$49.99",
                "story": "The CrossAction round head oscillates, rotates, and pulsates to break up plaque. A built-in pressure sensor stops pulsation if you brush too hard, and the quadrant timer pulses every 30 seconds.",
                "url": "https://www.amazon.com/Oral-B-1000-Rechargeable-Electric-Toothbrush/dp/B003UKM9CO",
            },
            {
                "asin": "B00SNM5US4",
                "name": "Olaplex No. 3 Hair Perfector",
                "blurb": "At-home bond-building treatment that reduces breakage.",
                "price": "$30.00",
                "story": "A weekly pre-shampoo treatment using patented bis-aminopropyl diglycol dimaleate to relink broken disulfide bonds. Works on all hair types, colored or natural. Leave in for at least 10 minutes before shampooing.",
                "url": "https://www.amazon.com/Olaplex-Hair-Perfector-Repairing-Treatment/dp/B00SNM5US4",
            },
            {
                "asin": "B01MDTVZTZ",
                "name": "The Ordinary Niacinamide 10% + Zinc 1%",
                "blurb": "High-strength vitamin and mineral serum that targets blemishes.",
                "price": "$6.70",
                "story": "A water-based serum from Deciem's value-first skincare line. Niacinamide reduces the appearance of skin blemishes and congestion; zinc salt of pyrrolidone carboxylic acid balances visible sebum activity.",
                "url": "https://www.amazon.com/Ordinary-Niacinamide-10-Zinc-30ml/dp/B01MDTVZTZ",
            },
            {
                "asin": "B00MEDOY2G",
                "name": "Dove Deep Moisture Body Wash",
                "blurb": "Sulfate-free body wash with microMoisture technology.",
                "price": "$8.49",
                "story": "Unlike typical soaps that can strip skin, Dove's formula contains 1/4 moisturizing cream and nutrients that go beyond cleansing to actively nourish skin during the shower.",
                "url": "https://www.amazon.com/Dove-Body-Wash-Pump-Moisture/dp/B00MEDOY2G",
            },
        ],
    },
    {
        "slug": "clothing-accessories",
        "name": "Clothing & Accessories",
        "tagline": "Wardrobe classics that never go out of style.",
        "accent": "#6b705c",
        "icon": "\u2737",
        "products": [
            {
                "asin": "B01GSAXOVW",
                "name": "Levi's 501 Original Fit Jeans",
                "blurb": "The original blue jean since 1873. Button fly, straight leg.",
                "price": "$69.50",
                "story": "100% cotton denim, straight through the seat and thigh with a signature button fly. The same five-pocket design that Levi Strauss patented 150 years ago — still the most copied silhouette in fashion.",
                "url": "https://www.amazon.com/Levis-Mens-501-Original-Jean/dp/B01GSAXOVW",
            },
            {
                "asin": "B000VKQZUI",
                "name": "Hanes EcoSmart Cotton T-Shirt",
                "blurb": "Tagless crewneck tee made with recycled polyester blend.",
                "price": "$9.99",
                "story": "An everyday crewneck with a double-needle hem, shoulder-to-shoulder taping, and recycled polyester blended into a soft cotton jersey. Tag-free neck and ribbed collar that holds its shape.",
                "url": "https://www.amazon.com/Hanes-ComfortBlend-EcoSmart-Crewneck-T-Shirt/dp/B000VKQZUI",
            },
            {
                "asin": "B002Q1P12S",
                "name": "Ray-Ban Wayfarer Classic Sunglasses",
                "blurb": "The iconic 1952 silhouette with 100% UV protection.",
                "price": "$163.00",
                "story": "Raymond Stegeman's wayfarer frame reshaped eyewear overnight. Acetate frames, B-15 crystal green lenses that block 100% of UVA and UVB, and metal arms signed on the inside.",
                "url": "https://www.amazon.com/Ray-Ban-Wayfarer-Crystal-Polarized-Lenses/dp/B002Q1P12S",
            },
            {
                "asin": "B0D4TDQKY4",
                "name": "Nike Air Force 1 '07",
                "blurb": "The 1982 basketball shoe that became a streetwear icon.",
                "price": "$115.00",
                "story": "Full-grain leather upper, perforated toe box, and the first basketball shoe to use Nike Air cushioning. Bruce Kilgore's original tooling is still unchanged four decades later.",
                "url": "https://www.amazon.com/Nike-Mens-Gymnastics-Shoes-Sneaker/dp/B0D4TDQKY4",
            },
            {
                "asin": "B09B2YNGSN",
                "name": "Fossil Gen 6 Smartwatch",
                "blurb": "Wear OS smartwatch with heart-rate tracking and GPS.",
                "price": "$255.00",
                "story": "Snapdragon Wear 4100+ platform, SpO2 sensor, built-in GPS, and contactless payments via Google Wallet. Fast charging gets you to 80% in about 30 minutes.",
                "url": "https://www.amazon.com/Fossil-Stainless-Steel-Silicone-Touchscreen/dp/B09B2YNGSN",
            },
        ],
    },
    {
        "slug": "electronics",
        "name": "Electronics",
        "tagline": "The gadgets people actually buy — and keep using.",
        "accent": "#457b9d",
        "icon": "\u26a1",
        "products": [
            {
                "asin": "B0CHWRXH8B",
                "name": "Apple AirPods Pro (2nd Generation)",
                "blurb": "Active noise cancellation, Adaptive Audio, and MagSafe charging.",
                "price": "$249.00",
                "story": "The H2 chip powers 2x stronger Active Noise Cancellation than the first generation, plus Adaptive Audio that blends transparency and ANC in real time. Up to 6 hours of listening on a charge, 30 hours with the case.",
                "url": "https://www.amazon.com/Apple-Generation-Cancelling-Transparency-Personalized/dp/B0CHWRXH8B",
            },
            {
                "asin": "B09XS7JWHH",
                "name": "Sony WH-1000XM5 Wireless Headphones",
                "blurb": "Industry-leading noise cancellation with 30-hour battery.",
                "price": "$399.99",
                "story": "Eight microphones and two processors power Sony's best-in-class ANC. Multipoint connection pairs with two devices simultaneously, and the redesigned slider sits flatter on a carry bag.",
                "url": "https://www.amazon.com/Sony-WH-1000XM5-Canceling-Headphones-Hands-Free/dp/B09XS7JWHH",
            },
            {
                "asin": "B0CMDRCZBJ",
                "name": "Samsung Galaxy S24",
                "blurb": "6.2-inch AMOLED, Snapdragon 8 Gen 3, and Galaxy AI.",
                "price": "$799.99",
                "story": "Galaxy AI brings live translation, Circle to Search, and generative photo editing to a titanium-framed flagship. 50MP main camera with 2x optical-quality zoom and Nightography on every lens.",
                "url": "https://www.amazon.com/SAMSUNG-Smartphone-Unlocked-Processor-SM-S921UZKAXAA/dp/B0CMDRCZBJ",
            },
            {
                "asin": "B09B8V1LZ3",
                "name": "Amazon Echo Dot (5th Gen)",
                "blurb": "Compact smart speaker with improved audio and a temperature sensor.",
                "price": "$49.99",
                "story": "A larger front-firing speaker delivers clearer vocals and deeper bass than the previous Dot. Built-in temperature sensor and accelerometer unlock new Routines — tap the top to dismiss an alarm.",
                "url": "https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3",
            },
            {
                "asin": "B0BJLXMVMV",
                "name": "Apple iPad (10th Generation)",
                "blurb": "10.9-inch Liquid Retina display with A14 Bionic and USB-C.",
                "price": "$449.00",
                "story": "The base iPad finally gets an all-screen redesign, USB-C charging, and a landscape FaceTime camera — the first iPad with the front camera on the long edge, fixing a decade-old video call awkwardness.",
                "url": "https://www.amazon.com/Apple-2022-10-9-inch-iPad-Wi-Fi/dp/B0BJLXMVMV",
            },
        ],
    },
]

# Wikipedia fallback titles for products Amazon's legacy CDN doesn't have
WIKI_FALLBACKS = {
    "B0D4TDQKY4": "Nike Air Force 1",
    "B0CHWRXH8B": "AirPods Pro",
    "B0CMDRCZBJ": "Samsung Galaxy S24",
    "B0979R48CX": "Dyson (company)",
    "B000VKQZUI": "T-shirt",
}


def try_wiki_image(asin, title, min_bytes=8000):
    """Query Wikipedia pageimages API and download the lead image if present."""
    api = (
        "https://en.wikipedia.org/w/api.php?action=query&prop=pageimages"
        "&format=json&piprop=original&titles=" + urllib.parse.quote(title)
    )
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "MeridianStore/1.0 (local)"})
        with urllib.request.urlopen(req, timeout=12) as r:
            data = json.loads(r.read())
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return False
        page = next(iter(pages.values()))
        original = page.get("original")
        if not original:
            return False
        img_url = original["source"]
        req2 = urllib.request.Request(img_url, headers=UA)
        with urllib.request.urlopen(req2, timeout=15) as r2:
            data2 = r2.read()
        if len(data2) < min_bytes:
            return False
        # Wikipedia may return SVG/PNG/JPG. Save with its original extension.
        ext = ".jpg"
        if img_url.lower().endswith(".png"):
            ext = ".png"
        elif img_url.lower().endswith(".svg"):
            ext = ".svg"
        out = os.path.join(IMG_DIR, f"{asin}{ext}")
        with open(out, "wb") as f:
            f.write(data2)
        # Also remove any stale .jpg placeholder
        stale = os.path.join(IMG_DIR, f"{asin}.jpg")
        if ext != ".jpg" and os.path.exists(stale):
            try:
                os.remove(stale)
            except OSError:
                pass
        print(f"  wiki fallback [{asin}] {title} -> {len(data2)} bytes ({ext})")
        return True
    except Exception as e:
        print(f"  wiki fallback [{asin}] {title} FAILED: {e}")
        return False


def resolve_image(asin):
    """Return the relative image path to use in HTML, or None for CSS-gradient fallback."""
    for ext in (".jpg", ".png", ".svg"):
        path = os.path.join(IMG_DIR, f"{asin}{ext}")
        if os.path.exists(path) and os.path.getsize(path) >= 8000:
            return f"images/{asin}{ext}"
    return None


def slugify(s):
    s = s.lower()
    s = re.sub(r"[''\u2019]", "", s)
    s = re.sub(r"&", "and", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def nav(active_slug):
    links = [("index.html", "Home", "home")]
    for c in CATEGORIES:
        links.append((f"{c['slug']}.html", c["name"], c["slug"]))
    parts = []
    for href, label, key in links:
        cls = "nav-link active" if key == active_slug else "nav-link"
        parts.append(f'<a class="{cls}" href="{href}">{html.escape(label)}</a>')
    return (
        '<nav class="topnav"><div class="nav-inner">'
        '<a class="brand" href="index.html"><span class="brand-mark"></span>MERIDIAN</a>'
        '<div class="nav-links">' + "".join(parts) + "</div>"
        "</div></nav>"
    )


def footer():
    today = date.today().isoformat()
    return (
        '<footer class="site-foot"><div class="foot-inner">'
        "<span>&copy; 2026 Meridian Goods</span>"
        f'<span>Index last built: {today} &middot; Pick of the Day rotates automatically.</span>'
        "</div></footer>"
    )


def base_page(title, body, active_slug, extra_head=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} &mdash; Meridian</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
{extra_head}
</head>
<body>
{nav(active_slug)}
<main>
{body}
</main>
{footer()}
<script src="daily.js" defer></script>
</body>
</html>
"""


def product_image_html(p, cat, size="card"):
    """Render either an <img> tag with the real product image, or a gradient fallback tile."""
    img_path = resolve_image(p["asin"])
    if img_path:
        if size == "hero":
            return (
                f'<div class="prod-hero-img has-photo" style="--accent:{cat["accent"]}">'
                f'<img src="{img_path}" alt="{html.escape(p["name"])}" loading="lazy">'
                "</div>"
            )
        return (
            f'<div class="prod-card-img has-photo" style="--accent:{cat["accent"]}">'
            f'<img src="{img_path}" alt="{html.escape(p["name"])}" loading="lazy">'
            "</div>"
        )
    # Fallback: gradient tile with product initial
    initial = html.escape(p["name"][0])
    if size == "hero":
        return (
            f'<div class="prod-hero-img" style="--accent:{cat["accent"]}">'
            f'<span class="prod-hero-initial">{initial}</span>'
            "</div>"
        )
    return (
        f'<div class="prod-card-img" style="--accent:{cat["accent"]}">'
        f'<span class="prod-card-initial">{initial}</span>'
        "</div>"
    )


# ---- Index page ----
def build_index():
    cat_cards = []
    for c in CATEGORIES:
        cat_cards.append(
            f'<a class="cat-card" href="{c["slug"]}.html" style="--accent:{c["accent"]}">'
            f'<div class="cat-card-mark">{c["icon"]}</div>'
            f'<div class="cat-card-body">'
            f'<h3>{html.escape(c["name"])}</h3>'
            f'<p>{html.escape(c["tagline"])}</p>'
            f'<span class="cat-card-meta">{len(c["products"])} top picks &rarr;</span>'
            f'</div></a>'
        )
    # Daily pick banner placeholder — filled in by daily.js based on today's date
    body = f"""
<section class="hero">
  <div class="hero-inner">
    <span class="eyebrow">Est. 2026 &middot; Updated daily</span>
    <h1>The things worth buying.<br><em>And nothing else.</em></h1>
    <p class="hero-sub">A hand-picked shortlist of the five best products in every category we cover. Fresh Pick of the Day below, rotating every midnight.</p>
    <a class="btn-primary" href="#categories">Browse categories</a>
  </div>
</section>

<section class="daily-wrap">
  <div class="daily-head">
    <span class="eyebrow">Pick of the Day</span>
    <h2 id="daily-date">Today's featured product</h2>
  </div>
  <a id="daily-link" class="daily-card" href="#" style="--accent:#888">
    <div id="daily-img" class="daily-img"></div>
    <div class="daily-body">
      <span id="daily-cat" class="pill">&mdash;</span>
      <h3 id="daily-name">Loading&hellip;</h3>
      <p id="daily-blurb">Pick rotates automatically based on today's date.</p>
      <div class="daily-foot">
        <span id="daily-price" class="price">&mdash;</span>
        <span class="arrow">&rarr;</span>
      </div>
    </div>
  </a>
</section>

<section id="categories" class="cat-grid-wrap">
  <div class="section-head">
    <h2>Shop by category</h2>
    <p>Four categories. Five picks each. Twenty things we stand behind.</p>
  </div>
  <div class="cat-grid">
    {''.join(cat_cards)}
  </div>
</section>
"""
    return base_page("The things worth buying", body, "home")


# ---- Category page ----
def build_category(cat):
    cards = []
    for p in cat["products"]:
        pslug = slugify(p["name"])
        img_html = product_image_html(p, cat, size="card")
        cards.append(
            f'<a class="prod-card" href="{cat["slug"]}-{pslug}.html">'
            f'{img_html}'
            f'<div class="prod-card-body">'
            f'<h3>{html.escape(p["name"])}</h3>'
            f'<p>{html.escape(p["blurb"])}</p>'
            f'<div class="prod-card-foot">'
            f'<span class="price">{html.escape(p["price"])}</span>'
            f'<span class="arrow">&rarr;</span>'
            f'</div></div></a>'
        )
    body = f"""
<section class="cat-hero" style="--accent:{cat['accent']}">
  <div class="cat-hero-inner">
    <span class="eyebrow">Category</span>
    <h1>{html.escape(cat['name'])}</h1>
    <p>{html.escape(cat['tagline'])}</p>
  </div>
</section>
<section class="prod-grid-wrap">
  <div class="section-head">
    <h2>Our top 5 picks</h2>
    <p>The shortlist &mdash; ranked by what people actually buy and keep.</p>
  </div>
  <div class="prod-grid">
    {''.join(cards)}
  </div>
</section>
"""
    return base_page(cat["name"], body, cat["slug"])


# ---- Product page ----
def build_product(cat, prod, rank):
    img_html = product_image_html(prod, cat, size="hero")
    body = f"""
<section class="prod-hero" style="--accent:{cat['accent']}">
  <div class="prod-hero-grid">
    {img_html}
    <div class="prod-hero-body">
      <a class="backlink" href="{cat['slug']}.html">&larr; Back to {html.escape(cat['name'])}</a>
      <span class="eyebrow">{html.escape(cat['name'])} &middot; #{rank} pick</span>
      <h1>{html.escape(prod['name'])}</h1>
      <p class="prod-blurb">{html.escape(prod['blurb'])}</p>
      <div class="prod-meta">
        <span class="price-lg">{html.escape(prod['price'])}</span>
        <span class="pill">In stock on Amazon</span>
      </div>
      <a class="btn-primary" target="_blank" rel="noopener sponsored nofollow" href="{html.escape(affiliate_url(prod['url']))}">View on Amazon &rarr;</a>
      <p class="affiliate-note">Opens the real Amazon product page in a new tab.</p>
    </div>
  </div>
</section>
<section class="prod-body-wrap">
  <div class="prod-body">
    <h2>Why it made the list</h2>
    <p>{html.escape(prod['story'])}</p>
  </div>
</section>
"""
    return base_page(prod["name"], body, cat["slug"])


# ---- Daily-rotation JS ----
# Uses day-of-year % 20 to pick one of 20 products as today's featured item.
# Runs client-side on every page load: if the date has changed since last render,
# the banner updates automatically.
def build_daily_js():
    products = []
    for c in CATEGORIES:
        for p in c["products"]:
            pslug = slugify(p["name"])
            products.append({
                "name": p["name"],
                "blurb": p["blurb"],
                "price": p["price"],
                "url": affiliate_url(p["url"]),
                "image": resolve_image(p["asin"]) or "",
                "accent": c["accent"],
                "category": c["name"],
                "page": f"{c['slug']}-{pslug}.html",
            })
    data = json.dumps(products, ensure_ascii=False)
    return f"""// Meridian daily-rotation logic.
// Picks one of 20 products as today's "Pick of the Day" using day-of-year.
// The choice changes automatically every midnight.
(function() {{
  const products = {data};

  function dayOfYear(d) {{
    const start = new Date(d.getFullYear(), 0, 0);
    const diff = d - start + (start.getTimezoneOffset() - d.getTimezoneOffset()) * 60 * 1000;
    return Math.floor(diff / 86400000);
  }}

  function dailyPick() {{
    const today = new Date();
    // Seed combines year and day-of-year so the rotation is deterministic per calendar day
    const seed = today.getFullYear() * 1000 + dayOfYear(today);
    return products[seed % products.length];
  }}

  function fmtDate(d) {{
    return d.toLocaleDateString(undefined, {{ weekday: 'long', month: 'long', day: 'numeric' }});
  }}

  document.addEventListener('DOMContentLoaded', function() {{
    const pick = dailyPick();
    const dateEl = document.getElementById('daily-date');
    if (!dateEl) return; // only the home page has the daily widget

    dateEl.textContent = fmtDate(new Date());
    const link = document.getElementById('daily-link');
    link.href = pick.page;
    link.style.setProperty('--accent', pick.accent);
    document.getElementById('daily-name').textContent = pick.name;
    document.getElementById('daily-blurb').textContent = pick.blurb;
    document.getElementById('daily-price').textContent = pick.price;
    document.getElementById('daily-cat').textContent = pick.category;

    const imgBox = document.getElementById('daily-img');
    if (pick.image) {{
      imgBox.innerHTML = '<img src="' + pick.image + '" alt="' + pick.name + '" loading="lazy">';
    }} else {{
      imgBox.style.background = 'linear-gradient(135deg, ' + pick.accent + ', rgba(0,0,0,.2))';
      imgBox.innerHTML = '<span class="daily-initial">' + pick.name.charAt(0) + '</span>';
    }}
  }});
}})();
"""


# ---- CSS ----
CSS = """
:root {
  --bg: #faf8f5;
  --ink: #1a1a1a;
  --ink-soft: #555;
  --line: #e8e4dc;
  --card: #ffffff;
  --accent: #c97b63;
  --shadow: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06);
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'Inter', -apple-system, system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3 {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 600;
  line-height: 1.15;
  margin: 0 0 .4em;
  letter-spacing: -0.01em;
}
h1 { font-size: clamp(2.2rem, 5vw, 4rem); }
h2 { font-size: clamp(1.5rem, 3vw, 2.2rem); }
h3 { font-size: 1.2rem; }
p  { margin: 0 0 1em; color: var(--ink-soft); }
a  { color: inherit; text-decoration: none; }
em { font-style: italic; color: var(--accent); }

.eyebrow {
  display: inline-block;
  font-size: .75rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--ink-soft);
  margin-bottom: 1rem;
  font-weight: 500;
}

/* ---- NAV ---- */
.topnav {
  position: sticky; top: 0; z-index: 50;
  background: rgba(250,248,245,.85);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--line);
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.1rem 1.5rem;
  display: flex; align-items: center; justify-content: space-between;
  gap: 2rem;
}
.brand {
  display: flex; align-items: center; gap: .55rem;
  font-weight: 600; font-size: 1rem; letter-spacing: .15em;
}
.brand-mark {
  display: inline-block;
  width: 14px; height: 14px;
  background: var(--ink);
  transform: rotate(45deg);
}
.nav-links { display: flex; gap: .35rem; flex-wrap: wrap; }
.nav-link {
  padding: .5rem .9rem;
  border-radius: 999px;
  font-size: .9rem;
  font-weight: 500;
  color: var(--ink-soft);
  transition: all .2s;
}
.nav-link:hover { color: var(--ink); background: rgba(0,0,0,.04); }
.nav-link.active { background: var(--ink); color: #fff; }

main { min-height: 70vh; }

/* ---- HERO (home) ---- */
.hero {
  padding: 6rem 1.5rem 3rem;
  text-align: center;
}
.hero-inner { max-width: 820px; margin: 0 auto; }
.hero h1 { margin-bottom: 1.2rem; }
.hero-sub { font-size: 1.1rem; max-width: 560px; margin: 0 auto 2rem; }
.btn-primary {
  display: inline-block;
  padding: .95rem 1.8rem;
  background: var(--ink);
  color: #fff;
  border-radius: 999px;
  font-weight: 500;
  font-size: .95rem;
  letter-spacing: .02em;
  transition: transform .15s, background .2s;
}
.btn-primary:hover { transform: translateY(-1px); background: #000; }

/* ---- DAILY PICK (home) ---- */
.daily-wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 2rem 1.5rem 4rem;
}
.daily-head { text-align: center; margin-bottom: 1.8rem; }
.daily-head h2 { font-size: 1.6rem; color: var(--ink); }
.daily-card {
  display: grid;
  grid-template-columns: 280px 1fr;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 20px;
  overflow: hidden;
  transition: transform .2s, box-shadow .2s;
}
.daily-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); }
@media (max-width: 720px) { .daily-card { grid-template-columns: 1fr; } }
.daily-img {
  aspect-ratio: 1;
  background: linear-gradient(135deg, var(--accent), rgba(0,0,0,.2));
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.daily-img img { width: 100%; height: 100%; object-fit: contain; padding: 1.5rem; background: #fff; }
.daily-initial { font-family: 'Fraunces', serif; font-size: 5rem; color: #fff; opacity: .9; }
.daily-body { padding: 2rem 2.2rem; display: flex; flex-direction: column; justify-content: center; }
.daily-body h3 { font-size: 1.5rem; margin: .6rem 0 .5rem; }
.daily-body p { font-size: .95rem; }
.daily-foot {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 1rem; margin-top: .8rem; border-top: 1px solid var(--line);
}

/* ---- CATEGORY GRID (home) ---- */
.cat-grid-wrap { max-width: 1200px; margin: 0 auto; padding: 4rem 1.5rem 6rem; }
.section-head { text-align: center; margin-bottom: 3rem; }
.section-head p { max-width: 480px; margin: 0 auto; }
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.2rem;
}
.cat-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 2rem 1.8rem;
  transition: all .25s;
  display: flex; flex-direction: column; gap: 1.2rem;
  position: relative; overflow: hidden;
}
.cat-card::before {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(135deg, var(--accent), transparent 70%);
  opacity: 0; transition: opacity .25s;
}
.cat-card:hover { transform: translateY(-4px); box-shadow: var(--shadow); border-color: transparent; }
.cat-card:hover::before { opacity: .08; }
.cat-card-mark {
  font-size: 1.8rem;
  width: 56px; height: 56px;
  border-radius: 14px;
  background: var(--accent);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.cat-card-body { position: relative; }
.cat-card-body h3 { font-size: 1.35rem; }
.cat-card-meta {
  display: inline-block;
  margin-top: .8rem;
  font-size: .85rem;
  font-weight: 500;
  color: var(--ink);
}

/* ---- CATEGORY PAGE HERO ---- */
.cat-hero { padding: 5rem 1.5rem 3rem; text-align: center; position: relative; overflow: hidden; }
.cat-hero::before {
  content: "";
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at top, var(--accent) 0%, transparent 55%);
  opacity: .12;
}
.cat-hero-inner { position: relative; max-width: 720px; margin: 0 auto; }
.cat-hero p { font-size: 1.1rem; }

/* ---- PRODUCT GRID ---- */
.prod-grid-wrap { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem 6rem; }
.prod-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1.5rem;
}
.prod-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 16px;
  overflow: hidden;
  transition: all .25s;
  display: flex; flex-direction: column;
}
.prod-card:hover { transform: translateY(-4px); box-shadow: var(--shadow); border-color: transparent; }
.prod-card-img {
  aspect-ratio: 4/3;
  background: linear-gradient(135deg, var(--accent), rgba(0,0,0,.15));
  display: flex; align-items: center; justify-content: center;
  position: relative;
  overflow: hidden;
}
.prod-card-img.has-photo { background: #fff; }
.prod-card-img img { width: 100%; height: 100%; object-fit: contain; padding: 1.2rem; }
.prod-card-initial {
  font-family: 'Fraunces', serif;
  font-size: 4.5rem;
  color: #fff;
  opacity: .9;
  font-weight: 600;
}
.prod-card-body { padding: 1.3rem 1.4rem 1.5rem; }
.prod-card-body h3 { font-size: 1.1rem; margin-bottom: .5rem; }
.prod-card-body p {
  font-size: .9rem;
  margin-bottom: 1.2rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.prod-card-foot {
  display: flex; justify-content: space-between; align-items: center;
  padding-top: 1rem;
  border-top: 1px solid var(--line);
}
.price { font-weight: 600; font-size: 1.05rem; }
.arrow { color: var(--ink-soft); transition: transform .2s; }
.prod-card:hover .arrow, .daily-card:hover .arrow { transform: translateX(4px); color: var(--ink); }

/* ---- PRODUCT DETAIL ---- */
.prod-hero { padding: 3rem 1.5rem 4rem; }
.prod-hero-grid {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 3.5rem;
  align-items: center;
}
@media (max-width: 820px) {
  .prod-hero-grid { grid-template-columns: 1fr; gap: 2rem; }
}
.prod-hero-img {
  aspect-ratio: 1;
  background: linear-gradient(135deg, var(--accent), rgba(0,0,0,.2));
  border-radius: 24px;
  position: relative;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.prod-hero-img.has-photo { background: #fff; border: 1px solid var(--line); }
.prod-hero-img img { width: 100%; height: 100%; object-fit: contain; padding: 2rem; }
.prod-hero-initial {
  font-family: 'Fraunces', serif;
  font-size: 12rem;
  color: #fff;
  opacity: .88;
  font-weight: 600;
}
.backlink {
  display: inline-block;
  font-size: .85rem;
  color: var(--ink-soft);
  margin-bottom: 1.2rem;
  transition: color .2s;
}
.backlink:hover { color: var(--ink); }
.prod-blurb { font-size: 1.15rem; color: var(--ink-soft); }
.prod-meta {
  display: flex; align-items: center; gap: 1rem;
  margin: 1.5rem 0 2rem;
  flex-wrap: wrap;
}
.price-lg { font-size: 2rem; font-weight: 600; font-family: 'Fraunces', serif; }
.pill {
  padding: .35rem .8rem;
  background: #e6f4ea;
  color: #1e6938;
  border-radius: 999px;
  font-size: .8rem;
  font-weight: 500;
}
.affiliate-note {
  font-size: .78rem;
  color: var(--ink-soft);
  margin-top: 1rem;
  opacity: .8;
}
.prod-body-wrap { max-width: 720px; margin: 0 auto; padding: 2rem 1.5rem 6rem; }
.prod-body { border-top: 1px solid var(--line); padding-top: 3rem; }
.prod-body h2 { margin-bottom: 1rem; }
.prod-body p { font-size: 1.05rem; line-height: 1.75; }

/* ---- FOOTER ---- */
.site-foot { border-top: 1px solid var(--line); padding: 2rem 1.5rem; background: #fff; }
.foot-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex; justify-content: space-between;
  font-size: .85rem;
  color: var(--ink-soft);
  flex-wrap: wrap;
  gap: 1rem;
}
"""


def write(path, content):
    full = os.path.join(ROOT, path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    # Step 1: Wikipedia fallback for ASINs missing a usable image
    print("Resolving missing product images via Wikipedia fallback...")
    for asin, title in WIKI_FALLBACKS.items():
        if resolve_image(asin):
            continue  # already have a good image
        try_wiki_image(asin, title)

    # Step 2: Report image coverage
    have = sum(1 for c in CATEGORIES for p in c["products"] if resolve_image(p["asin"]))
    total = sum(len(c["products"]) for c in CATEGORIES)
    print(f"Image coverage: {have}/{total}")

    # Step 3: Write all site files
    write("style.css", CSS)
    write("daily.js", build_daily_js())
    write("index.html", build_index())
    count = 3
    for cat in CATEGORIES:
        write(f"{cat['slug']}.html", build_category(cat))
        count += 1
        for rank, prod in enumerate(cat["products"], start=1):
            pslug = slugify(prod["name"])
            write(f"{cat['slug']}-{pslug}.html", build_product(cat, prod, rank))
            count += 1
    print(f"Wrote {count} files to {ROOT}")


if __name__ == "__main__":
    main()
