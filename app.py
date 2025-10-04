#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =========================
# SKU/Model Matcher - Streamlit App
# =========================
# Design goals:
# - Minimal UI, Apple-like feel
# - EN/RU language toggle (remember via cookie if available; else session)
# - Dark/Light toggle (default Dark; CSS-based toggle)
# - Robust error handling up-front
# - Clear success logs when done

import os
os.environ["STREAMLIT_HOME"] = "/tmp"
import io
import sys
import traceback
import pandas as pd
import streamlit as st

# Optional cookie persistence (best effort).
# If streamlit-extras is unavailable, the app still works (session-only memory).
try:
    from streamlit_extras.cookie_manager import CookieManager
    COOKIE_OK = True
except Exception:
    CookieManager = None
    COOKIE_OK = False

APP_TITLE = "SKU / Model Matcher"
REF_FILE = "sku_model_list.xlsx"  # must sit next to app.py in repo

# -------------------------------
# i18n dictionary
# -------------------------------
TXT = {
    "EN": {
        "title": "SKU / Model Matcher",
        "subtitle": "Download → Fill → Upload → Process → Download results",
        "download_tmpl": "📥 Download Excel template",
        "upload_label": "Upload your filled template (.xlsx)",
        "process_btn": "▶️ Process",
        "dl_output": "📤 Download output.xlsx",
        "preview_head": "Preview",
        "ok_done": "✅ Done. Rows processed: {n}",
        "using_ref": "Using reference file: {name} ({rows} rows)",
        "err_generic": "❌ Error",
        "err_header": "The uploaded file must have a first sheet with a single column header named **raw_name**.",
        "err_ref_missing": "Reference file `sku_model_list.xlsx` not found in the app folder.",
        "err_ref_schema": "Reference file must have columns: sku, model, raw_model (first sheet).",
        "lang": "Language",
        "theme": "Theme",
        "dark": "Dark",
        "light": "Light",
        "en": "EN",
        "ru": "RU",
        "helper": "Tip: drag & drop your file above, then click Process.",
        "footer": "Simple. Fast. Free.",
        "tmpl_note": "Template = first sheet, header **raw_name**."
    },
    "RU": {
        "title": "Сопоставление SKU / Модели",
        "subtitle": "Скачать шаблон → Заполнить → Загрузить → Обработать → Скачать результат",
        "download_tmpl": "📥 Скачать шаблон Excel",
        "upload_label": "Загрузите заполненный шаблон (.xlsx)",
        "process_btn": "▶️ Обработать",
        "dl_output": "📤 Скачать output.xlsx",
        "preview_head": "Предпросмотр",
        "ok_done": "✅ Готово. Обработано строк: {n}",
        "using_ref": "Используется файл справочника: {name} ({rows} строк)",
        "err_generic": "❌ Ошибка",
        "err_header": "В загруженном файле на первом листе должна быть одна колонка с заголовком **raw_name**.",
        "err_ref_missing": "Файл справочника `sku_model_list.xlsx` не найден в папке приложения.",
        "err_ref_schema": "В справочнике должны быть колонки: sku, model, raw_model (первый лист).",
        "lang": "Язык",
        "theme": "Тема",
        "dark": "Тёмная",
        "light": "Светлая",
        "en": "АНГ",
        "ru": "РУС",
        "helper": "Подсказка: перетащите файл выше и нажмите Обработать.",
        "footer": "Просто. Быстро. Бесплатно.",
        "tmpl_note": "Шаблон = первый лист, заголовок **raw_name**."
    }
}

# -------------------------------
# Minimal Apple-like CSS + Theme switch
# -------------------------------
BASE_CSS = """
<style>
:root, .light-theme {
  --bg: #ffffff;
  --card: #f6f7f8;
  --text: #111111;
  --muted: #777777;
  --accent: #0071e3; /* Apple-ish blue */
}
.dark-theme {
  --bg: #0b0b0c;
  --card: #151517;
  --text: #f3f3f3;
  --muted: #a0a0a0;
  --accent: #0a84ff;
}
html, body, .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.block-container { padding-top: 2rem; }
header, [data-testid="stHeader"] { background: transparent !important; }
h1, h2, h3 { letter-spacing: -0.01em; }
section.main > div { border-radius: 18px; }
.stButton>button, .stDownloadButton>button {
  border-radius: 12px;
  padding: 0.5rem 0.9rem;
  border: 1px solid rgba(127,127,127,0.2);
  background: var(--card);
  color: var(--text);
}
.stButton>button:hover, .stDownloadButton>button:hover {
  border-color: var(--accent);
}
.st-emotion-cache-1xarl3l, .st-emotion-cache-1v0mbdj { background: var(--card) !important; }
small, .muted { color: var(--muted); }
.header-row { display: flex; align-items: center; gap: 1rem; }
.header-row .grow { flex: 1; }
.header-pill {
  display: inline-flex; gap: 6px; align-items: center; padding: 6px 10px;
  border-radius: 999px; background: var(--card); border: 1px solid rgba(127,127,127,0.2);
}
</style>
"""

def set_theme_class(theme_choice: str):
    # Injects a theme class onto the app root
    theme_class = "dark-theme" if theme_choice == "Dark" else "light-theme"
    st.markdown(BASE_CSS + f"<script>document.documentElement.className='{theme_class}';</script>", unsafe_allow_html=True)

# -------------------------------
# Helpers: persistence (cookie/session)
# -------------------------------
def get_cookie_manager():
    return CookieManager() if COOKIE_OK else None

def read_pref(cm, key, default):
    # 1) cookie, 2) session_state
    if cm:
        try:
            val = cm.get(key)
            if val:
                return val
        except Exception:
            pass
    return st.session_state.get(key, default)

def write_pref(cm, key, val):
    st.session_state[key] = val
    if cm:
        try:
            cm.set(key, val)
        except Exception:
            pass

# -------------------------------
# Core: load reference and process
# -------------------------------
@st.cache_data(show_spinner=False)
def load_reference(ref_path: str):
    if not os.path.exists(ref_path):
        raise FileNotFoundError("REF_MISSING")
    df = pd.read_excel(ref_path, sheet_name=0)
    # Normalize expected columns
    cols_lower = [str(c).strip().lower() for c in df.columns]
    df.columns = cols_lower
    needed = ["sku", "model", "raw_model"]
    if any(c not in cols_lower for c in needed):
        raise ValueError("REF_BAD_SCHEMA")
    # Cast types & normalize
    df["sku"] = df["sku"].astype(str).fillna("").str.strip()
    df["model"] = df["model"].astype(str).fillna("").str.strip()
    df["raw_model"] = df["raw_model"].astype(str).fillna("").str.strip()
    return df

def process(raw_df: pd.DataFrame, ref_df: pd.DataFrame) -> pd.DataFrame:
    # Validate header
    cols_lower = [str(c).strip().lower() for c in raw_df.columns]
    if len(cols_lower) != 1 or cols_lower[0] != "raw_name":
        raise ValueError("BAD_HEADER")

    df_raw = pd.DataFrame({"raw_name": raw_df.iloc[:, 0].astype(str).fillna("")})
    df_sku = ref_df

    # Precompute lowercase lists/maps
    sku_list = df_sku["sku"].astype(str).tolist()
    sku_list_l = [s.lower() for s in sku_list]
    model_map = dict(zip(sku_list, df_sku["model"].astype(str)))
    model_map_l = dict(zip(sku_list_l, df_sku["model"].astype(str)))

    raw_models = df_sku["raw_model"].astype(str).tolist()
    raw_models_l = [rm.lower() for rm in raw_models]
    raw_model_to_sku = dict(zip(raw_models_l, df_sku["sku"].astype(str)))
    raw_model_to_model = dict(zip(raw_models_l, df_sku["model"].astype(str)))

    found_skus, found_models = [], []

    # Pass 1: find SKU substring (case-insensitive)
    for name in df_raw["raw_name"]:
        nm = str(name).lower()
        hit_sku = None
        for sku_l, sku_orig in zip(sku_list_l, sku_list):
            if sku_l and sku_l in nm:
                hit_sku = sku_orig
                break
        if hit_sku:
            found_skus.append(hit_sku)
            found_models.append(model_map_l[hit_sku.lower()])
        else:
            found_skus.append("not found")
            found_models.append("not found")

    # Pass 2: if no SKU, try raw_model substring
    for i, (nm, sku_now) in enumerate(zip(df_raw["raw_name"].astype(str).str.lower(), found_skus)):
        if sku_now == "not found":
            for rm_l in raw_models_l:
                if rm_l and rm_l in nm:
                    found_skus[i] = raw_model_to_sku[rm_l]
                    found_models[i] = raw_model_to_model[rm_l]
                    break

    df_out = df_raw.copy()
    df_out["sku"] = found_skus
    df_out["model"] = found_models
    return df_out

def make_template_bytes() -> bytes:
    bio = io.BytesIO()
    pd.DataFrame(columns=["raw_name"]).to_excel(bio, index=False)
    return bio.getvalue()

def make_output_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    df.to_excel(bio, index=False)
    return bio.getvalue()

# -------------------------------
# App
# -------------------------------
def main():
    # Error handling at the very beginning
    try:
        cm = get_cookie_manager()

        # Preferences (language + theme)
        lang_default = "EN"
        theme_default = "Dark"

        lang = read_pref(cm, "pref_lang", lang_default)
        if lang not in ("EN", "RU"):
            lang = lang_default
        theme_choice = read_pref(cm, "pref_theme", theme_default)
        if theme_choice not in ("Dark", "Light"):
            theme_choice = theme_default

        set_theme_class(theme_choice)
        t = TXT[lang]

        # Header row (title + toggles on the right)
        st.markdown(f"<div class='header-row'><div class='grow'><h1>{t['title']}</h1><div class='muted'>{t['subtitle']}</div></div>", unsafe_allow_html=True)
        col_lang, col_theme = st.columns([0.12, 0.12])
        with col_lang:
            new_lang = st.radio(t["lang"], options=["EN", "RU"], index=0 if lang=="EN" else 1, horizontal=True, key="lang_radio")
        with col_theme:
            new_theme = st.radio(t["theme"], options=["Dark", "Light"], index=0 if theme_choice=="Dark" else 1, horizontal=True, key="theme_radio")
        st.markdown("</div>", unsafe_allow_html=True)

        # Persist changes if user toggled
        if new_lang != lang:
            lang = new_lang
            write_pref(cm, "pref_lang", lang)
            st.rerun()
        if new_theme != theme_choice:
            theme_choice = new_theme
            write_pref(cm, "pref_theme", theme_choice)
            st.rerun()

        # Rebind translations after possible rerun
        t = TXT[lang]
        set_theme_class(theme_choice)

        st.caption(f"📝 {t['tmpl_note']}")
        st.download_button(t["download_tmpl"], data=make_template_bytes(), file_name="raw_names_input.xlsx")

        st.divider()
        st.write(f"**{t['upload_label']}**")
        up = st.file_uploader(" ", type=["xlsx"], accept_multiple_files=False, label_visibility="collapsed")

        # Load reference (fail fast with a friendly error)
        try:
            ref = load_reference(REF_FILE)
            st.caption("ℹ️ " + t["using_ref"].format(name=REF_FILE, rows=len(ref)))
        except FileNotFoundError:
            st.error(t["err_ref_missing"])
            st.stop()
        except ValueError:
            st.error(t["err_ref_schema"])
            st.stop()
        except Exception as e:
            st.error(f"{t['err_generic']}: {e}")
            st.stop()

        st.write(f"_{t['helper']}_")

        if st.button(t["process_btn"], type="primary", use_container_width=False, disabled=(up is None)):
            if up is None:
                st.warning(t["upload_label"])
                st.stop()
            try:
                raw_df = pd.read_excel(up, sheet_name=0)  # first sheet only
            except Exception as e:
                st.error(f"{t['err_generic']}: {e}")
                st.stop()

            try:
                with st.spinner("Processing..."):
                    df_out = process(raw_df, ref)
                st.success(t["ok_done"].format(n=len(df_out)))

                st.subheader(t["preview_head"])
                st.dataframe(df_out.head(200), use_container_width=True)

                st.download_button(
                    label=t["dl_output"],
                    data=make_output_bytes(df_out),
                    file_name="output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except ValueError as ve:
                if str(ve) == "BAD_HEADER":
                    st.error(t["err_header"])
                else:
                    st.error(f"{t['err_generic']}: {ve}")
            except Exception as e:
                st.error(f"{t['err_generic']}: {e}")
                st.exception(e)

        st.markdown(f"<p class='muted'>{t['footer']}</p>", unsafe_allow_html=True)

    except Exception as fatal:
        # last line of defense (won't crash the app UI)
        st.error("💥 Fatal: " + str(fatal))
        st.text("Traceback:")
        st.code("".join(traceback.format_exc()))

if __name__ == "__main__":
    main()
