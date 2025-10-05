#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# =========================
# SKU/Model Matcher — Streamlit App
# =========================
# - Uses single light theme from palette.py
# - Clean, minimal Apple-like design
# - EN/RU toggle with cookie/session
# - No theme switching

import os
os.environ["STREAMLIT_HOME"] = "/tmp"

import io
import traceback
import pandas as pd
import streamlit as st

# Import centralized colors
from palette import THEMES, build_css

# Optional cookie persistence
try:
    from streamlit_extras.cookie_manager import CookieManager
    COOKIE_OK = True
except Exception:
    CookieManager = None
    COOKIE_OK = False

APP_TITLE = "SKU / Model Matcher"
REF_FILE = "sku_model_list.xlsx"

st.set_page_config(page_title=APP_TITLE, layout="wide")

# -------------------------------
# i18n (EN / RU text)
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
        "en": "АНГ",
        "ru": "РУС",
        "helper": "Подсказка: перетащите файл выше и нажмите Обработать.",
        "footer": "Просто. Быстро. Бесплатно.",
        "tmpl_note": "Шаблон = первый лист, заголовок **raw_name**."
    }
}

# -------------------------------
# Helpers for cookies
# -------------------------------
def get_cookie_manager():
    return CookieManager() if COOKIE_OK else None

def read_pref(cm, key, default):
    if cm:
        try:
            v = cm.get(key)
            if v:
                return v
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
# Data logic
# -------------------------------
@st.cache_data(show_spinner=False)
def load_reference(ref_path: str):
    if not os.path.exists(ref_path):
        raise FileNotFoundError("REF_MISSING")
    df = pd.read_excel(ref_path, sheet_name=0)
    cols_lower = [str(c).strip().lower() for c in df.columns]
    df.columns = cols_lower
    needed = ["sku", "model", "raw_model"]
    if any(c not in cols_lower for c in needed):
        raise ValueError("REF_BAD_SCHEMA")
    for c in needed:
        df[c] = df[c].astype(str).fillna("").str.strip()
    return df

def process(raw_df: pd.DataFrame, ref_df: pd.DataFrame) -> pd.DataFrame:
    cols_lower = [str(c).strip().lower() for c in raw_df.columns]
    if len(cols_lower) != 1 or cols_lower[0] != "raw_name":
        raise ValueError("BAD_HEADER")

    df_raw = pd.DataFrame({"raw_name": raw_df.iloc[:, 0].astype(str).fillna("")})
    sku_list = ref_df["sku"].astype(str).tolist()
    sku_list_l = [s.lower() for s in sku_list]
    model_map_l = dict(zip(sku_list_l, ref_df["model"].astype(str)))

    raw_models = ref_df["raw_model"].astype(str).tolist()
    raw_models_l = [rm.lower() for rm in raw_models]
    rm_to_sku   = dict(zip(raw_models_l, ref_df["sku"].astype(str)))
    rm_to_model = dict(zip(raw_models_l, ref_df["model"].astype(str)))

    found_skus, found_models = [], []

    # Pass 1: SKU detection
    for name in df_raw["raw_name"]:
        nm = str(name).lower()
        hit = None
        for sku_l, sku_orig in zip(sku_list_l, sku_list):
            if sku_l and sku_l in nm:
                hit = sku_orig
                break
        if hit:
            found_skus.append(hit)
            found_models.append(model_map_l[hit.lower()])
        else:
            found_skus.append("not found")
            found_models.append("not found")

    # Pass 2: raw_model detection
    for i, nm in enumerate(df_raw["raw_name"].astype(str).str.lower()):
        if found_skus[i] == "not found":
            for rm_l in raw_models_l:
                if rm_l and rm_l in nm:
                    found_skus[i] = rm_to_sku[rm_l]
                    found_models[i] = rm_to_model[rm_l]
                    break

    out = df_raw.copy()
    out["sku"] = found_skus
    out["model"] = found_models
    return out

def make_template_bytes() -> bytes:
    bio = io.BytesIO()
    pd.DataFrame(columns=["raw_name"]).to_excel(bio, index=False)
    return bio.getvalue()

def make_output_bytes(df: pd.DataFrame) -> bytes:
    bio = io.BytesIO()
    df.to_excel(bio, index=False)
    return bio.getvalue()

# -------------------------------
# Apply global CSS
# -------------------------------
def inject_css_once():
    st.markdown(build_css(THEMES["Light"]), unsafe_allow_html=True)

# -------------------------------
# App main
# -------------------------------
def main():
    try:
        cm = get_cookie_manager()

        # Language preference (default EN)
        lang = read_pref(cm, "pref_lang", "EN")
        if lang not in ("EN", "RU"):
            lang = "EN"

        inject_css_once()
        t = TXT[lang]

        # Header and language toggle
        st.markdown(
            f"<div class='header-row'><div class='grow'><h1>{t['title']}</h1>"
            f"<div class='muted'>{t['subtitle']}</div></div>",
            unsafe_allow_html=True
        )
        col_lang, _ = st.columns([0.2, 0.8])
        with col_lang:
            new_lang = st.radio(t["lang"], ["EN", "RU"], index=0 if lang == "EN" else 1, horizontal=True, key="lang_radio")
        st.markdown("</div>", unsafe_allow_html=True)

        # Save lang pref if changed
        if new_lang != lang:
            write_pref(cm, "pref_lang", new_lang)
            st.rerun()

        # Reload correct language
        t = TXT[new_lang]

        st.caption(f"📝 {t['tmpl_note']}")
        st.download_button(t["download_tmpl"], data=make_template_bytes(), file_name="raw_names_input.xlsx")

        st.divider()
        st.write(f"**{t['upload_label']}**")
        up = st.file_uploader(" ", type=["xlsx"], accept_multiple_files=False, label_visibility="collapsed")

        # Load reference
        try:
            ref = load_reference(REF_FILE)
            st.caption("ℹ️ " + t["using_ref"].format(name=REF_FILE, rows=len(ref)))
        except FileNotFoundError:
            st.error(t["err_ref_missing"]); st.stop()
        except ValueError:
            st.error(t["err_ref_schema"]); st.stop()
        except Exception as e:
            st.error(f"{t['err_generic']}: {e}"); st.stop()

        st.write(f"_{t['helper']}_")

        if st.button(t["process_btn"], type="primary", disabled=(up is None)):
            if up is None:
                st.warning(t["upload_label"]); st.stop()
            try:
                raw_df = pd.read_excel(up, sheet_name=0)
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
                st.error(t["err_header"] if str(ve) == "BAD_HEADER" else f"{t['err_generic']}: {ve}")
            except Exception as e:
                st.error(f"{t['err_generic']}: {e}")
                st.exception(e)

        st.markdown(f"<p class='muted'>{t['footer']}</p>", unsafe_allow_html=True)

    except Exception as fatal:
        st.error("💥 Fatal: " + str(fatal))
        st.text("Traceback:")
        st.code("".join(traceback.format_exc()))

if __name__ == "__main__":
    main()
