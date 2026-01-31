import * as XLSX from "xlsx";

function normalizeModel(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
}

function normalizeModelAlnum(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, "");
}

function hasDigitBoundaryMatch(haystack, needle) {
  const source = haystack.toLowerCase();
  const target = needle.toLowerCase();
  if (!target) return false;
  let idx = source.indexOf(target);
  while (idx !== -1) {
    const before = idx === 0 ? "" : source[idx - 1];
    const after = idx + target.length >= source.length ? "" : source[idx + target.length];
    if (!/\d/.test(before) && !/\d/.test(after)) {
      return true;
    }
    idx = source.indexOf(target, idx + 1);
  }
  return false;
}

function sheetToRows(sheet) {
  return XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    raw: false,
    defval: "",
  });
}

function parseReference(workbook) {
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const rows = sheetToRows(sheet);
  if (!rows.length) throw new Error("REF_BAD_SCHEMA");
  const header = rows[0].map((cell) => String(cell || "").trim().toLowerCase());
  const idxSku = header.indexOf("sku");
  const idxModel = header.indexOf("model");
  const idxRawModel = header.indexOf("raw_model");
  if (idxSku === -1 || idxModel === -1 || idxRawModel === -1) {
    throw new Error("REF_BAD_SCHEMA");
  }

  const items = [];
  for (let i = 1; i < rows.length; i += 1) {
    const row = rows[i];
    items.push({
      sku: String(row[idxSku] || "").trim(),
      model: String(row[idxModel] || "").trim(),
      raw_model: String(row[idxRawModel] || "").trim(),
    });
  }
  return items;
}

function parseInput(workbook) {
  const sheetName = workbook.SheetNames[0];
  const sheet = workbook.Sheets[sheetName];
  const rows = sheetToRows(sheet);
  if (!rows.length) throw new Error("BAD_HEADER");
  const header = rows[0].map((cell) => String(cell || "").trim().toLowerCase());
  const nonEmpty = header.filter(Boolean);
  if (nonEmpty.length !== 1 || nonEmpty[0] !== "raw_name") {
    throw new Error("BAD_HEADER");
  }

  return rows.slice(1).map((row) => String(row[0] || ""));
}

export async function onRequestPost({ request, env }) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    if (!file || typeof file.arrayBuffer !== "function") {
      return new Response(JSON.stringify({ ok: false, error: "NO_FILE" }), { status: 400 });
    }

    const inputBuffer = await file.arrayBuffer();
    const inputWb = XLSX.read(new Uint8Array(inputBuffer), { type: "array" });
    const rawNames = parseInput(inputWb);

    const refRes = await env.ASSETS.fetch(new URL("/sku_model_list.xlsx", request.url));
    if (!refRes.ok) {
      return new Response(JSON.stringify({ ok: false, error: "REF_MISSING" }), { status: 500 });
    }
    const refBuffer = await refRes.arrayBuffer();
    const refWb = XLSX.read(new Uint8Array(refBuffer), { type: "array" });
    const refItems = parseReference(refWb);

    const skuList = refItems.map((row) => row.sku).filter(Boolean);
    const skuSorted = [...skuList].sort((a, b) => b.length - a.length);
    const modelBySku = new Map(refItems.map((row) => [row.sku.toLowerCase(), row.model]));

    const rawModelNormalized = refItems.map((row) => normalizeModel(row.raw_model));
    const rawModelNormalizedAlnum = refItems.map((row) => normalizeModelAlnum(row.raw_model));

    const rmToSku = new Map();
    const rmToModel = new Map();
    const rmToSkuAlnum = new Map();
    const rmToModelAlnum = new Map();

    rawModelNormalized.forEach((key, idx) => {
      if (key && !rmToSku.has(key)) {
        rmToSku.set(key, refItems[idx].sku);
        rmToModel.set(key, refItems[idx].model);
      }
    });

    rawModelNormalizedAlnum.forEach((key, idx) => {
      if (key && !rmToSkuAlnum.has(key)) {
        rmToSkuAlnum.set(key, refItems[idx].sku);
        rmToModelAlnum.set(key, refItems[idx].model);
      }
    });

    const results = rawNames.map((raw) => ({
      raw_name: raw,
      sku: "not found",
      model: "not found",
      note: "",
    }));

    // Pass 1: SKU match with digit boundaries
    results.forEach((row) => {
      const lower = row.raw_name.toLowerCase();
      for (const sku of skuSorted) {
        if (hasDigitBoundaryMatch(lower, sku)) {
          row.sku = sku;
          row.model = modelBySku.get(sku.toLowerCase()) || "not found";
          return;
        }
      }
    });

    // Pass 2: exact normalized raw_model match
    results.forEach((row, idx) => {
      if (row.sku !== "not found") return;
      const normalized = normalizeModel(rawNames[idx]);
      if (rmToSku.has(normalized)) {
        row.sku = rmToSku.get(normalized) || "not found";
        row.model = rmToModel.get(normalized) || "not found";
      }
    });

    // Pass 3: exact punctuation-stripped match + note
    results.forEach((row, idx) => {
      if (row.sku !== "not found") return;
      const normalized = normalizeModelAlnum(rawNames[idx]);
      if (rmToSkuAlnum.has(normalized)) {
        row.sku = rmToSkuAlnum.get(normalized) || "not found";
        row.model = rmToModelAlnum.get(normalized) || "not found";
        row.note = "check: matched after removing punctuation";
      }
    });

    return new Response(JSON.stringify({ ok: true, rows: results }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    const code = err && err.message ? err.message : "SERVER_ERROR";
    const status = code === "BAD_HEADER" || code === "REF_BAD_SCHEMA" ? 400 : 500;
    return new Response(JSON.stringify({ ok: false, error: code }), { status });
  }
}
