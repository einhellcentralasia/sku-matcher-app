const STRINGS = {
  en: {
    title: "SKU / Model Matcher",
    subtitle: "Upload → Process → Download",
    stepHint: "First sheet, single column header raw_name.",
    processBtn: "Process",
    downloadTitle: "Step 1. Download and fill template",
    downloadHint: "Download the template file and fill it in.",
    downloadBtn: "Download template",
    uploadTitle: "Step 2. Upload and download output",
    uploadHint: "Upload the fulfilled file and download the output file.",
    downloadOutput: "Download output file",
    statusReady: "Ready.",
    statusProcessing: "Processing...",
    statusError: "Error:",
    statusDone: (count) => `Done. Rows: ${count}`,
    statusNoFile: "Please select an .xlsx file.",
    statusBadHeader: "The first sheet must have a single header named raw_name.",
    statusBadRef: "Reference file must contain columns: sku, model, raw_model.",
  },
  ru: {
    title: "Сопоставление SKU / Модели",
    subtitle: "Загрузка → Обработка → Скачивание",
    stepHint: "Первый лист, одна колонка raw_name.",
    processBtn: "Обработать",
    downloadTitle: "Шаг 1. Скачать и заполнить шаблон",
    downloadHint: "Скачайте шаблон и заполните его.",
    downloadBtn: "Скачать шаблон",
    uploadTitle: "Шаг 2. Загрузка и скачивание результата",
    uploadHint: "Загрузите заполненный файл и скачайте результат.",
    downloadOutput: "Скачать файл результата",
    statusReady: "Готово.",
    statusProcessing: "Обработка...",
    statusError: "Ошибка:",
    statusDone: (count) => `Готово. Строк: ${count}`,
    statusNoFile: "Выберите файл .xlsx.",
    statusBadHeader: "В первом листе должна быть одна колонка raw_name.",
    statusBadRef: "Справочник должен содержать колонки: sku, model, raw_model.",
  },
};

const storageKeys = {
  lang: "skuMatcherLang",
  theme: "skuMatcherTheme",
};

const els = {
  fileInput: document.getElementById("fileInput"),
  processBtn: document.getElementById("processBtn"),
  statusMsg: document.getElementById("statusMsg"),
  downloadBtn: document.getElementById("downloadBtn"),
  templateBtn: document.getElementById("templateBtn"),
  themeToggle: document.getElementById("themeToggle"),
};

let currentLang = "en";
let currentTheme = "dark";
let latestRows = [];

function setTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(storageKeys.theme, theme);
  const icon = theme === "dark" ? "☀" : "☾";
  els.themeToggle.textContent = icon;
}

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem(storageKeys.lang, lang);
  const dict = STRINGS[lang];
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    const value = dict[key];
    if (typeof value === "string") {
      el.textContent = value;
    }
  });
  document.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
  if (els.statusMsg.textContent) {
    els.statusMsg.textContent = dict.statusReady;
    els.statusMsg.className = "msg";
  }
}

function setStatus(message, type = "") {
  els.statusMsg.textContent = message;
  els.statusMsg.className = `msg ${type}`.trim();
}

function mapErrorMessage(code, dict) {
  switch (code) {
    case "BAD_HEADER":
      return dict.statusBadHeader;
    case "REF_BAD_SCHEMA":
      return dict.statusBadRef;
    case "REF_MISSING":
      return dict.statusBadRef;
    case "NO_FILE":
      return dict.statusNoFile;
    default:
      return code || dict.statusError;
  }
}

function toggleLang() {
  const next = currentLang === "en" ? "ru" : "en";
  setLang(next);
}

async function handleProcess() {
  const dict = STRINGS[currentLang];
  const file = els.fileInput.files[0];
  if (!file) {
    setStatus(dict.statusNoFile, "error");
    return;
  }

  setStatus(dict.statusProcessing);
  els.processBtn.disabled = true;
  els.downloadBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", file, file.name);
    const res = await fetch("/api/match", {
      method: "POST",
      body: formData,
    });
    const payload = await res.json();
    if (!payload.ok) {
      const msg = mapErrorMessage(payload.error, dict);
      setStatus(`${dict.statusError} ${msg}`, "error");
      return;
    }

    latestRows = payload.rows || [];
    els.downloadBtn.disabled = false;
    setStatus(dict.statusDone(latestRows.length), "success");
    downloadOutput();
  } catch (err) {
    setStatus(`${dict.statusError} ${err.message}`, "error");
  } finally {
    els.processBtn.disabled = false;
  }
}

function downloadOutput() {
  if (!window.XLSX || !latestRows.length) return;
  const ws = window.XLSX.utils.json_to_sheet(latestRows, {
    header: ["raw_name", "sku", "model", "note"],
  });
  const wb = window.XLSX.utils.book_new();
  window.XLSX.utils.book_append_sheet(wb, ws, "output");
  const out = window.XLSX.write(wb, { bookType: "xlsx", type: "array" });
  const blob = new Blob([out], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "output.xlsx";
  link.click();
  URL.revokeObjectURL(url);
}

function downloadTemplate() {
  if (!window.XLSX) return;
  const ws = window.XLSX.utils.aoa_to_sheet([["raw_name"]]);
  const wb = window.XLSX.utils.book_new();
  window.XLSX.utils.book_append_sheet(wb, ws, "template");
  const out = window.XLSX.write(wb, { bookType: "xlsx", type: "array" });
  const blob = new Blob([out], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "raw_names_input.xlsx";
  link.click();
  URL.revokeObjectURL(url);
}

function init() {
  const savedLang = localStorage.getItem(storageKeys.lang);
  const savedTheme = localStorage.getItem(storageKeys.theme);
  setTheme(savedTheme || "dark");
  setLang(savedLang || "en");

  const langToggle = document.querySelector(".lang-toggle");
  if (langToggle) {
    langToggle.addEventListener("click", (e) => {
      e.preventDefault();
      toggleLang();
    });
  }

  els.themeToggle.addEventListener("click", () => {
    setTheme(currentTheme === "dark" ? "light" : "dark");
  });

  els.fileInput.addEventListener("change", () => {
    els.processBtn.disabled = !els.fileInput.files.length;
  });

  els.processBtn.addEventListener("click", handleProcess);
  els.downloadBtn.addEventListener("click", downloadOutput);
  els.templateBtn.addEventListener("click", downloadTemplate);
}

window.addEventListener("DOMContentLoaded", init);
