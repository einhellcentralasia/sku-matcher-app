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
        "card": "#16161a",
        "text": "#f3f3f3",
        "muted": "#a0a0a0",
        "accent": "#0a84ff",
        "border": "rgba(255,255,255,0.16)"
    }
}

def build_css(light: dict, dark: dict) -> str:
    """Return CSS with both palettes; actual pick is done by the class on <html>."""
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

/* Apply theme to all possible Streamlit containers */
html, body, .stApp, [data-testid="stAppViewContainer"], 
[data-testid="stAppViewContainer"] > div {{
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}}

[data-testid="stHeader"] {{
  background: var(--bg) !important;
  border-bottom: 1px solid var(--border);
}}

/* Target all text elements more aggressively */
h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stCaption, 
label, p, span, div, .stSelectbox label, .stTextInput label,
.stTextArea label, .stNumberInput label, .stDateInput label,
.stTimeInput label, .stFileUploader label {{
  color: var(--text) !important;
}}

small, .muted, .stCaption {{
  color: var(--muted) !important;
}}

.block-container {{ 
  padding-top: 1rem !important;
  background: var(--bg) !important;
}}

section.main > div {{ 
  border-radius: 18px;
  background: var(--bg) !important;
}}

/* Enhanced button styling */
.stButton>button, .stDownloadButton>button {{
  border-radius: 12px;
  padding: 8px 14px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--text) !important;
}}

.stButton>button:hover, .stDownloadButton>button:hover {{ 
  border-color: var(--accent);
  background: var(--card);
}}

/* Radio button styling */
.stRadio > div > label > div > div {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}

.stRadio > div > label > div > div[data-testid="stMarkdownContainer"] {{
  color: var(--text) !important;
}}

/* File uploader styling */
[data-testid="stFileUploader"] * {{ 
  color: var(--text) !important; 
}}

[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
}}

[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] div {{
  color: var(--text) !important;
}}

.header-row {{ 
  display:flex; 
  align-items:center; 
  gap:1rem; 
  margin-bottom:.5rem; 
}}

.header-row .grow {{ 
  flex:1; 
}}

.header-pill {{
  display:inline-flex; 
  gap:6px; 
  align-items:center; 
  padding:6px 10px;
  border-radius:999px; 
  background: var(--card);
  border:1px solid var(--border); 
  color: var(--text);
}}

/* Ensure sidebar follows theme */
.css-1d391kg {{
  background: var(--bg) !important;
}}

/* Force Streamlit widgets to use theme colors */
.stSelectbox, .stTextInput, .stTextArea, .stNumberInput, .stDateInput, .stTimeInput {{
  background: var(--card) !important;
  color: var(--text) !important;
}}

.stSelectbox > div > div {{
  background: var(--card) !important;
  color: var(--text) !important;
}}

/* Dataframe styling */
.stDataFrame {{
  background: var(--card) !important;
  color: var(--text) !important;
}}

.stDataFrame table {{
  background: var(--card) !important;
  color: var(--text) !important;
}}

.stDataFrame th, .stDataFrame td {{
  background: var(--card) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}}

/* Additional Streamlit component styling */
.stSuccess, .stError, .stWarning, .stInfo {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}

/* Spinner styling */
.stSpinner {{
  color: var(--accent) !important;
}}

/* Divider styling */
hr {{
  border-color: var(--border) !important;
}}

/* Input field styling */
.stTextInput > div > div > input {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}

.stTextArea > div > div > textarea {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}

.stSelectbox > div > div > select {{
  background: var(--card) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}
</style>
"""
