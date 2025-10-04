# palette.py
# Centralized theme colors. Change hex codes here only.

THEMES = {
    "Light": {
        "bg": "#ffffff",
        "card": "#f3f4f6",
        "text": "#0f172a",
        "muted": "#475569",
        "accent": "#0071e3",
        "border": "rgba(15,23,42,0.15)"
    },
    "Dark": {
        "bg": "#0b0b0c",
        "card": "#16165a",
        "text": "#f3f3f3",
        "muted": "#a0a0a0",
        "accent": "#0a84ff",
        "border": "rgba(255,255,255,0.16)"
    }
}


def build_css(light: dict, dark: dict) -> str:
    """Return the CSS string using provided palettes."""
    return f"""
<style>
:root, .light-theme {{
  --bg: {light['bg']};
  --card: {light['card']};
  --text: {light['text']};
  --muted: {light['muted']};
  --accent: {light['accent']};
  --border: {light['border']};
}}
.dark-theme {{
  --bg: {dark['bg']};
  --card: {dark['card']};
  --text: {dark['text']};
  --muted: {dark['muted']};
  --accent: {dark['accent']};
  --border: {dark['border']};
}}

html, body, .stApp, [data-testid="stAppViewContainer"] {{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}
[data-testid="stHeader"] {{
  background: var(--bg) !important;
  border-bottom: 1px solid var(--border);
}}
h1, h2, h3, .stMarkdown, .stText, .stCaption, label, p, span, div {{
  color: var(--text) !important;
}}
small, .muted {{ color: var(--muted) !important; }}
.block-container {{ padding-top: 1rem !important; }}
section.main > div {{ border-radius: 18px; }}
.stButton>button, .stDownloadButton>button {{
  border-radius: 12px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text);
}}
.stButton>button:hover, .stDownloadButton>button:hover {{ border-color: var(--accent); }}

.header-row {{ display:flex; align-items:center; gap:1rem; margin-bottom:.5rem; }}
.header-row .grow {{ flex:1; }}
.header-pill {{
  display:inline-flex; gap:6px; align-items:center; padding:6px 10px;
  border-radius:999px; background: var(--card);
  border:1px solid var(--border); color: var(--text);
}}

/* File uploader: readable text + visible box */
[data-testid="stFileUploader"] * {{ color: var(--text) !important; }}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
}}
[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] div {{
  color: var(--text) !important;
}}
</style>
"""
