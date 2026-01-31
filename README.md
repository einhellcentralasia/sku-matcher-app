# SKU / Model Matcher (Cloudflare Pages)

This app runs on Cloudflare Pages + Functions.

## Current user flow
1. **Download template** — click “Download template”.
2. **Fill it in** — first sheet, single column header `raw_name`.
3. **Upload and process** — choose the filled `.xlsx`, click “Process”.
4. **Auto-download** — the output file downloads automatically after processing.
5. **Manual download** — “Download output file” becomes active (accent button) if you want to re-download.

## How it works
- Input: `.xlsx`, first sheet with a single column header `raw_name`.
- Matching source: `public/sku_model_list.xlsx` (first sheet, columns: `sku`, `model`, `raw_model`).
- Output: `output.xlsx` with columns `raw_name`, `sku`, `model`, `note`.

Matching logic:
1. **SKU pass** — exact substring match with digit-boundary protection (e.g., `1234` will not match `123456`).
2. **Raw model pass** — exact match after lowercasing and removing whitespace.
3. **Fallback pass** — exact match after lowercasing and removing all punctuation; matched rows get a `note`.

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
