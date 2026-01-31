# SKU / Model Matcher (Cloudflare Pages)

This app runs on Cloudflare Pages + Functions.

## How it works
- Upload an input `.xlsx` with the first sheet containing a single column header `raw_name`.
- The app matches against `public/sku_model_list.xlsx` (first sheet, columns: `sku`, `model`, `raw_model`).
- Output is `output.xlsx` with columns: `raw_name`, `sku`, `model`, `note`.

Matching logic:
1. **SKU pass**: exact substring match with digit-boundary protection (e.g., `1234` will not match `123456`).
2. **Raw model pass**: exact match after lowercasing and removing whitespace.
3. **Fallback pass**: exact match after lowercasing and removing all punctuation; matched rows get a `note`.

## Repo structure
- `public/` — static site (HTML/CSS/JS + assets)
- `functions/api/match.js` — Pages Function that handles matching
- `public/sku_model_list.xlsx` — mapping file (replace this when needed)
- `public/logo.png` — logo

## Cloudflare Pages setup
- Build command: *(none)*
- Build output directory: `public`

## Update mapping file
Replace `public/sku_model_list.xlsx` and push to GitHub. Cloudflare Pages will rebuild automatically.
