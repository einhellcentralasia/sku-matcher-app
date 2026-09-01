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
- `public/sku_model_list.xlsx` — generated mapping file used by the app
- `config/sharepoint-mapping.json` — non-secret SharePoint path, table, column, and output configuration
- `scripts/sync_sharepoint_mapping.py` — SharePoint download, SKU join, validation, and workbook generation
- `functions/api/update-data.js` — dispatches the mapping workflow from the UI
- `functions/api/update-status.js` — reports queued, running, successful, or failed workflow state
- `.github/workflows/sync-sharepoint-mapping.yml` — on-demand GitHub Actions sync
- `public/logo.png` — logo

## Cloudflare Pages setup
- Build command: *(none)*
- Build output directory: `public`

## On-demand mapping update

The separate **Update from Bava_data** UI button starts the GitHub Actions workflow. The button is disabled while the update runs, its label changes, and an `aria-live` status message shows starting, in-progress, success, failure, timeout, or API-error states. There is no automatic schedule.

Committed non-secret routing is stored in `config/sharepoint-mapping.json`:

- Site: `bavatools.sharepoint.com/sites/Einhell_common`
- File: `Shared Documents/General/_system_files/Bava_data.xlsx`
- `_rus_kaz_table`: `SKU` + `Описание` → output `sku` + `model`
- `_param_table`: `SKU` + `Model` → output `raw_model`

`_rus_kaz_table` is the base product list. `_param_table` is left-joined by normalized `SKU`, so a product remains available when its `raw_model` is blank. Rows with a blank `Описание` are excluded, matching the current workbook contract where `model` is always populated. The workflow fails on duplicate SKUs, missing required columns, or missing named tables instead of committing ambiguous data.

### Required GitHub repository secrets

Add only these Microsoft Graph app credentials:

- `TENANT_ID`
- `CLIENT_ID`
- `CLIENT_SECRET`

The SharePoint path and table names are configuration, not secrets. The workflow uses GitHub's built-in token through `contents: write`; no separate GitHub token is required.

### Required Cloudflare Pages secret

Add:

- `GITHUB_ACTIONS_TRIGGER_TOKEN`

This is the server-side token used by the two Pages Functions to dispatch and inspect the GitHub Actions workflow. Use a fine-grained token restricted to `einhellcentralasia/sku-matcher-app` with **Actions: read and write**. Do not put this token in browser JavaScript or a GitHub Actions secret used by the workflow.

The Pages Functions default to owner `einhellcentralasia`, repository `sku-matcher-app`, branch `main`, and workflow `sync-sharepoint-mapping.yml`. Optional non-secret Cloudflare variables can override them: `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`, `GITHUB_REPO_REF`, and `GITHUB_UPDATE_WORKFLOW_ID`.

When the generated row data is unchanged, the script keeps the existing workbook byte-for-byte and the workflow skips the commit. When data changes, it commits only `public/sku_model_list.xlsx`; Cloudflare Pages can then rebuild from the new commit.

### Optional local verification

With the three credentials exported in the shell:

```bash
python -m pip install -r requirements-sync.txt
python -m unittest discover -s tests -p "test_*.py"
python scripts/sync_sharepoint_mapping.py
```

For an offline test against a local workbook without SharePoint credentials:

```bash
python scripts/sync_sharepoint_mapping.py --input-workbook /path/to/Bava_data.xlsx --output /tmp/sku_model_list.xlsx
```
