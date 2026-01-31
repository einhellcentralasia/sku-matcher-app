const STRINGS = {
  en: {
    title: "SKU / Model Matcher",
    subtitle: "Upload → Process → Download",
    stepTitle: "Step 1. Upload input",
    stepHint: "Use the template: first sheet, single column header raw_name.",
    processBtn: "Process",
    downloadTitle: "Template",
    downloadHint: "Download an empty template.",
    downloadBtn: "Download template",
    mappingTitle: "Mapping file",
    mappingHint: "The app uses sku_model_list.xlsx from this repo.",
    mappingBtn: "Download mapping",
    resultsTitle: "Results",
    downloadOutput: "Download output.xlsx",
    colRaw: "raw_name",
    colSku: "sku",
    colModel: "model",
    colNote: "note",
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
    stepTitle: "Шаг 1. Загрузите файл",
    stepHint: "Используйте шаблон: первый лист, одна колонка raw_name.",
    processBtn: "Обработать",
    downloadTitle: "Шаблон",
    downloadHint: "Скачать пустой шаблон.",
    downloadBtn: "Скачать шаблон",
    mappingTitle: "Файл сопоставления",
    mappingHint: "Используется sku_model_list.xlsx из репозитория.",
    mappingBtn: "Скачать сопоставление",
    resultsTitle: "Результаты",
    downloadOutput: "Скачать output.xlsx",
    colRaw: "raw_name",
    colSku: "sku",
    colModel: "model",
    colNote: "note",
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
  resultsCard: document.getElementById("resultsCard"),
  resultsTick: document.getElementById("resultsTick"),
  resultsTable: document.getElementById("resultsTable"),
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

function renderTable(rows) {
  const tbody = els.resultsTable.querySelector("tbody");
  tbody.innerHTML = "";
  rows.slice(0, 200).forEach((row) => {
    const tr = document.createElement("tr");
    [row.raw_name, row.sku, row.model, row.note].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value || "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
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
    renderTable(latestRows);
    els.resultsCard.classList.remove("is-hidden");
    els.resultsTick.classList.remove("is-hidden");
    els.downloadBtn.disabled = false;
    setStatus(dict.statusDone(latestRows.length), "success");
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

  document.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.addEventListener("click", () => setLang(btn.dataset.lang));
  });

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
