"use strict";

const DATASETS = {
  health: {
    label: "Health",
    sheet: "Health",
    path: "res/var/data/health.json",
    facets: [
      { key: "functionalCategories", param: "category", label: "Functional category" },
      { key: "carePhases", param: "stage", label: "Care phase" },
    ],
    searchFields: [
      "name", "producer", "designer", "purpose", "description", "category",
      "functionalCategories", "carePhases", "manufacturingProcesses", "hardwareLicense",
    ],
    details: [
      { key: "producer", label: "Producer or maker" },
      { key: "designer", label: "Designer" },
      { key: "functionalCategories", label: "Functional categories" },
      { key: "carePhases", label: "Care phases" },
      { key: "manufacturingProcesses", label: "Manufacturing processes" },
      { key: "priceUsd", label: "Price", format: "usd" },
      { key: "hardwareLicense", label: "Hardware license" },
      { key: "oshwaUid", label: "OSHWA UID" },
      { key: "technologyReadinessLevel", label: "Technology readiness level", format: "range" },
      { key: "medicalCertification", label: "Medical certification" },
      { key: "euMedicalDeviceClass", label: "EU medical device class" },
    ],
  },
  food: {
    label: "Food",
    sheet: "Food",
    path: "res/var/data/food.json",
    facets: [
      { key: "subCategories", param: "category", label: "Subcategory" },
      { key: "valueChainStages", param: "stage", label: "Value-chain stage" },
    ],
    searchFields: [
      "name", "producer", "designer", "purpose", "description", "category",
      "subCategories", "valueChainStages", "manufacturingProcesses", "hardwareLicense",
    ],
    details: [
      { key: "producer", label: "Producer or maker" },
      { key: "designer", label: "Designer" },
      { key: "subCategories", label: "Subcategories" },
      { key: "valueChainStages", label: "Value-chain stages" },
      { key: "manufacturingProcesses", label: "Manufacturing processes" },
      { key: "priceUsd", label: "Price (source text)" },
      { key: "tariffCode", label: "Tariff code" },
      { key: "hardwareLicense", label: "Hardware license" },
      { key: "oshwaUid", label: "OSHWA UID" },
      { key: "technologyReadinessLevel", label: "Technology readiness level", format: "range" },
      { key: "ceCertificate", label: "CE certificate" },
    ],
  },
  construction: {
    label: "Construction",
    sheet: "Construction",
    path: "res/var/data/construction.json",
    facets: [
      { key: "subCategories", param: "category", label: "Subcategory" },
      { key: "valueChainStages", param: "stage", label: "Value-chain stage" },
    ],
    searchFields: [
      "name", "producer", "designer", "purpose", "description", "category",
      "subCategories", "valueChainStages", "manufacturingProcesses", "hardwareLicense",
    ],
    details: [
      { key: "producer", label: "Producer or maker" },
      { key: "designer", label: "Designer" },
      { key: "subCategories", label: "Subcategories" },
      { key: "valueChainStages", label: "Value-chain stages" },
      { key: "manufacturingProcesses", label: "Manufacturing processes" },
      { key: "priceUsd", label: "Price (source text)" },
      { key: "tariffCode", label: "Tariff code" },
      { key: "hardwareLicense", label: "Hardware license" },
      { key: "oshwaUid", label: "OSHWA UID" },
      { key: "technologyReadinessLevel", label: "Technology readiness level", format: "range" },
      { key: "ceCertificate", label: "CE certificate" },
    ],
  },
};

const NAME_COLLATOR = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function hasValue(value) {
  if (value === null || value === undefined || value === "") return false;
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

function valueList(value) {
  if (!hasValue(value)) return [];
  return Array.isArray(value) ? value : [value];
}

function formatRange(value) {
  if (!hasValue(value)) return "";
  if (typeof value !== "object") return String(value);
  if (value.minimum === value.maximum) return String(value.minimum);
  return `${value.minimum}–${value.maximum}`;
}

function formatUsd(value) {
  if (!hasValue(value)) return "";
  const formatter = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
  if (typeof value === "number") return formatter.format(value);
  if (typeof value === "object") {
    return `${formatter.format(value.minimum)}–${formatter.format(value.maximum)}`;
  }
  return String(value);
}

function formatDetail(value, format) {
  if (!hasValue(value)) return "";
  if (format === "usd") return formatUsd(value);
  if (format === "range") return formatRange(value);
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url : null;
  } catch (error) {
    return null;
  }
}

async function loadDataset(config) {
  const response = await fetch(config.path);
  if (!response.ok) throw new Error(`Request failed with status ${response.status}`);
  const document = await response.json();
  validateDataset(document, config);
  return document;
}

function validateDataset(document, config) {
  const source = document && document.source;
  if (document?.schemaVersion !== "1.0.0") {
    throw new Error(`Unsupported ${config.label} schema version`);
  }
  if (source?.sheet !== config.sheet || !Array.isArray(document.records)) {
    throw new Error(`Invalid ${config.label} dataset envelope`);
  }
  if (document.records.some((record) => typeof record.name !== "string" || !record.name.trim())) {
    throw new Error(`${config.label} dataset contains an invalid record`);
  }
}

async function loadLandingCount(domain, config) {
  const target = document.querySelector(`[data-count-domain="${domain}"]`);
  if (!target) return;
  try {
    const dataset = await loadDataset(config);
    const noun = dataset.records.length === 1 ? "project" : "projects";
    target.textContent = `${dataset.records.length} ${noun}`;
  } catch (error) {
    target.textContent = "Dataset unavailable";
    console.error(`Unable to load ${config.label} count`, error);
  }
}

function initLanding() {
  return Promise.all(
    Object.entries(DATASETS).map(([domain, config]) => loadLandingCount(domain, config)),
  );
}

function readState(config) {
  const parameters = new URLSearchParams(window.location.search);
  const selections = {};
  for (const facet of config.facets) {
    selections[facet.param] = new Set(parameters.getAll(facet.param));
  }
  return {
    query: parameters.get("q") || "",
    sort: parameters.get("sort") === "desc" ? "desc" : "asc",
    selections,
  };
}

function facetValues(records, facet) {
  const values = new Set();
  for (const record of records) {
    for (const value of valueList(record[facet.key])) values.add(String(value));
  }
  return [...values].sort(NAME_COLLATOR.compare);
}

function sanitizeSelections(records, config, state) {
  for (const facet of config.facets) {
    const available = new Set(facetValues(records, facet));
    const selected = state.selections[facet.param];
    state.selections[facet.param] = new Set([...selected].filter((value) => available.has(value)));
  }
}

function writeState(config, state) {
  const url = new URL(window.location.href);
  const parameters = url.searchParams;
  state.query.trim() ? parameters.set("q", state.query.trim()) : parameters.delete("q");
  state.sort === "desc" ? parameters.set("sort", "desc") : parameters.delete("sort");
  for (const facet of config.facets) {
    parameters.delete(facet.param);
    const selected = [...state.selections[facet.param]].sort(NAME_COLLATOR.compare);
    for (const value of selected) parameters.append(facet.param, value);
  }
  window.history.replaceState(null, "", url);
}

function searchText(record, config) {
  const parts = [];
  for (const field of config.searchFields) {
    for (const value of valueList(record[field])) parts.push(String(value));
  }
  return parts.join(" ").toLocaleLowerCase("en");
}

function matchesFacets(record, config, state) {
  return config.facets.every((facet) => {
    const selected = state.selections[facet.param];
    if (!selected.size) return true;
    return valueList(record[facet.key]).some((value) => selected.has(String(value)));
  });
}

function filteredRecords(records, config, state) {
  const query = state.query.trim().toLocaleLowerCase("en");
  const result = records.filter((record) => {
    const matchesQuery = !query || searchText(record, config).includes(query);
    return matchesQuery && matchesFacets(record, config, state);
  });
  result.sort((left, right) => NAME_COLLATOR.compare(left.name, right.name));
  if (state.sort === "desc") result.reverse();
  return result;
}

function primaryTags(record, config) {
  const tags = [];
  for (const facet of config.facets) {
    const value = valueList(record[facet.key])[0];
    if (value) tags.push(String(value));
  }
  return tags;
}

function createTagList(record, config) {
  const tags = primaryTags(record, config);
  if (!tags.length && !record.flagship) return null;
  const list = makeElement("ul", "tag-list");
  if (record.flagship) list.append(makeElement("li", "tag tag--featured", "Featured"));
  for (const tag of tags) list.append(makeElement("li", "tag", tag));
  return list;
}

function createRecordSummary(record, config) {
  const summary = makeElement("summary", "record__summary");
  const identity = makeElement("span", "record__identity");
  const title = makeElement("span", "record__name", record.name);
  title.setAttribute("role", "heading");
  title.setAttribute("aria-level", "3");
  identity.append(title);
  if (record.producer) identity.append(makeElement("span", "record__producer", record.producer));
  const overview = makeElement("span", "record__overview");
  overview.append(makeElement("span", "record__purpose", record.purpose || "Purpose summary not provided."));
  const tags = createTagList(record, config);
  if (tags) overview.append(tags);
  summary.append(identity, overview);
  return summary;
}

function appendDefinition(list, label, value) {
  if (!value) return;
  list.append(makeElement("dt", "record__term", label));
  list.append(makeElement("dd", "record__definition", value));
}

function createDefinitionList(record, config) {
  const list = makeElement("dl", "record__facts");
  for (const field of config.details) {
    appendDefinition(list, field.label, formatDetail(record[field.key], field.format));
  }
  return list.childElementCount ? list : null;
}

function sourceLabel(url, index, total) {
  const host = url.hostname.replace(/^www\./, "");
  return total > 1 ? `Source ${index + 1}: ${host}` : `Open project source: ${host}`;
}

function createSourceLinks(record) {
  const urls = valueList(record.urls).map(safeUrl).filter(Boolean);
  if (!urls.length && !record.sourceLinkText) return null;
  const section = makeElement("div", "record__sources");
  section.append(makeElement("h4", "record__subheading", "Project sources"));
  if (urls.length) {
    const list = makeElement("ul", "source-list");
    urls.forEach((url, index) => {
      const item = makeElement("li");
      const link = makeElement("a", "source-link", sourceLabel(url, index, urls.length));
      link.href = url.href;
      item.append(link);
      list.append(item);
    });
    section.append(list);
  } else {
    section.append(makeElement("p", "record__source-text", record.sourceLinkText));
  }
  return section;
}

function createRecord(record, config) {
  const item = makeElement("details", "record");
  item.append(createRecordSummary(record, config));
  const body = makeElement("div", "record__body");
  if (record.description) body.append(makeElement("p", "record__description", record.description));
  const facts = createDefinitionList(record, config);
  if (facts) body.append(facts);
  const sources = createSourceLinks(record);
  if (sources) body.append(sources);
  body.append(makeElement("p", "record__provenance", `Source worksheet row ${record.sourceRow}`));
  item.append(body);
  return item;
}

function renderResults(records, config) {
  const container = document.querySelector("[data-results]");
  const fragment = document.createDocumentFragment();
  if (!records.length) {
    fragment.append(makeElement("p", "empty-state", "No projects match the current search and filters."));
  } else {
    for (const record of records) fragment.append(createRecord(record, config));
  }
  container.replaceChildren(fragment);
  const count = document.querySelector("[data-results-count]");
  const noun = records.length === 1 ? "project" : "projects";
  count.textContent = `${records.length} ${noun}`;
}

function createFacetOption(facet, value, index, state, onChange) {
  const item = makeElement("li", "filter-option");
  const checkbox = makeElement("input", "filter-option__input");
  checkbox.type = "checkbox";
  checkbox.id = `${facet.param}-${index}`;
  checkbox.value = value;
  checkbox.checked = state.selections[facet.param].has(value);
  checkbox.addEventListener("change", () => {
    const selected = state.selections[facet.param];
    checkbox.checked ? selected.add(value) : selected.delete(value);
    onChange();
  });
  const label = makeElement("label", "filter-option__label", value);
  label.htmlFor = checkbox.id;
  item.append(checkbox, label);
  return item;
}

function renderFacets(records, config, state, onChange) {
  const container = document.querySelector("[data-facets]");
  const fragment = document.createDocumentFragment();
  for (const facet of config.facets) {
    const fieldset = makeElement("fieldset", "filter-group");
    fieldset.append(makeElement("legend", "filter-group__title", facet.label));
    const list = makeElement("ul", "filter-options");
    const values = facetValues(records, facet);
    values.forEach((value, index) => {
      list.append(createFacetOption(facet, value, index, state, onChange));
    });
    fieldset.append(list);
    fragment.append(fieldset);
  }
  container.replaceChildren(fragment);
}

function syncControls(state) {
  document.querySelector("[data-search]").value = state.query;
  document.querySelector("[data-sort]").value = state.sort;
  for (const checkbox of document.querySelectorAll("[data-facets] input")) {
    const parameter = checkbox.id.split("-")[0];
    checkbox.checked = state.selections[parameter]?.has(checkbox.value) || false;
  }
}

function resetState(config, state) {
  state.query = "";
  state.sort = "asc";
  for (const facet of config.facets) state.selections[facet.param].clear();
  syncControls(state);
}

function bindControls(config, state, update) {
  const form = document.querySelector("[data-controls]");
  const search = document.querySelector("[data-search]");
  const sort = document.querySelector("[data-sort]");
  const reset = document.querySelector("[data-reset]");
  form.addEventListener("submit", (event) => event.preventDefault());
  search.addEventListener("input", () => {
    state.query = search.value;
    update();
  });
  sort.addEventListener("change", () => {
    state.sort = sort.value;
    update();
  });
  reset.addEventListener("click", () => {
    resetState(config, state);
    update();
    search.focus();
  });
}

function showCatalogError(config, error) {
  const container = document.querySelector("[data-results]");
  const message = makeElement("p", "error-state", `${config.label} data could not be loaded.`);
  message.setAttribute("role", "alert");
  container.replaceChildren(message);
  document.querySelector("[data-results-count]").textContent = "Data unavailable";
  console.error(`Unable to load ${config.label} data`, error);
}

function configureFilterPanel() {
  const panel = document.querySelector("[data-filter-panel]");
  if (panel) panel.open = window.matchMedia("(min-width: 800px)").matches;
}

async function initCatalog(domain) {
  const config = DATASETS[domain];
  if (!config) throw new Error(`Unknown portfolio domain: ${domain}`);
  configureFilterPanel();
  try {
    const dataset = await loadDataset(config);
    const state = readState(config);
    sanitizeSelections(dataset.records, config, state);
    const update = () => {
      renderResults(filteredRecords(dataset.records, config, state), config);
      writeState(config, state);
    };
    renderFacets(dataset.records, config, state, update);
    bindControls(config, state, update);
    syncControls(state);
    document.querySelector("[data-total-count]").textContent = `${dataset.records.length} projects`;
    update();
  } catch (error) {
    showCatalogError(config, error);
  }
}

const page = document.body.dataset.page;
if (page === "landing") initLanding();
if (page === "catalog") initCatalog(document.body.dataset.domain);
