# bestselling.live

Static affiliate storefront. Four categories, top picks per category, one rotating "Pick of the Day". Built from `generate.py`, deployed to Cloudflare Pages.

## Build

```
python generate.py
```

Writes `index.html`, category pages, product pages, `style.css`, and `daily.js` into this directory. Product images live in `images/`.

## Affiliate tag

Set `AMAZON_AFFILIATE_TAG` env var to override the default tag baked into `generate.py`.

## Deploy

Cloudflare Pages is configured to run `python generate.py` on every push and serve this directory as the site root.
