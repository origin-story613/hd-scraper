// Static-site version: all data comes from one deals.json fetched once,
// filtering/sorting/pagination happen entirely in the browser. This is what
// GitHub Pages serves — there's no backend here.

const PAGE_SIZE = 48;

const state = {
  allDeals: [],
  visible: [],
  shown: 0,
};

const els = {
  grid: document.getElementById("grid"),
  empty: document.getElementById("empty"),
  stats: document.getElementById("stats"),
  loadMore: document.getElementById("load-more"),
  search: document.getElementById("search"),
  category: document.getElementById("category"),
  zip: document.getElementById("zip"),
  minDiscount: document.getElementById("min-discount"),
  maxPrice: document.getElementById("max-price"),
  inStock: document.getElementById("in-stock"),
  sort: document.getElementById("sort"),
};

function money(n) {
  if (n === null || n === undefined) return "";
  return n.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function cardHtml(deal) {
  const img = deal.image_url
    ? `<img src="${deal.image_url}" alt="" loading="lazy" />`
    : `<span style="color:#aaa;font-size:12px;">No image</span>`;

  const badge = deal.badge ? `<span class="badge">${deal.badge}</span>` : "";
  const discount = deal.discount_percent
    ? `<span class="discount-pill">-${Math.round(deal.discount_percent)}%</span>`
    : "";
  const was = deal.original_price
    ? `<span class="price-was">${money(deal.original_price)}</span>`
    : "";
  const stockNote = deal.in_stock ? "" : `<div class="out-of-stock">Out of stock</div>`;

  return `
    <a class="card" href="${deal.product_url}" target="_blank" rel="noopener">
      <div class="card-img">${img}${badge}${discount}</div>
      <div class="card-body">
        <div class="card-brand">${deal.brand ?? ""}</div>
        <div class="card-title">${deal.title}</div>
        <div class="price-row">
          <span class="price-now">${money(deal.current_price)}</span>
          ${was}
        </div>
        <div class="card-meta">${deal.store_name ?? deal.zip_code ?? ""}</div>
        ${stockNote}
      </div>
    </a>
  `;
}

function applyFilters() {
  const search = els.search.value.trim().toLowerCase();
  const category = els.category.value;
  const zip = els.zip.value;
  const minDiscount = Number(els.minDiscount.value) || 0;
  const maxPrice = els.maxPrice.value ? Number(els.maxPrice.value) : null;
  const inStockOnly = els.inStock.checked;

  let items = state.allDeals.filter((d) => {
    if (search) {
      const hay = `${d.title} ${d.brand ?? ""}`.toLowerCase();
      if (!hay.includes(search)) return false;
    }
    if (category && d.category !== category) return false;
    if (zip && d.zip_code !== zip) return false;
    if ((d.discount_percent || 0) < minDiscount) return false;
    if (maxPrice !== null && d.current_price > maxPrice) return false;
    if (inStockOnly && !d.in_stock) return false;
    return true;
  });

  switch (els.sort.value) {
    case "price_asc":
      items.sort((a, b) => a.current_price - b.current_price);
      break;
    case "price_desc":
      items.sort((a, b) => b.current_price - a.current_price);
      break;
    case "discount_desc":
    default:
      items.sort((a, b) => (b.discount_percent || 0) - (a.discount_percent || 0));
      break;
  }

  state.visible = items;
  state.shown = 0;
  render({ reset: true });
}

function render({ reset }) {
  if (reset) {
    els.grid.innerHTML = "";
  }

  const nextBatch = state.visible.slice(state.shown, state.shown + PAGE_SIZE);
  state.shown += nextBatch.length;

  els.grid.insertAdjacentHTML("beforeend", nextBatch.map(cardHtml).join(""));
  els.empty.classList.toggle("hidden", state.visible.length > 0);
  els.loadMore.classList.toggle("hidden", state.shown >= state.visible.length);
  els.stats.textContent = `${state.visible.length.toLocaleString()} deal${state.visible.length === 1 ? "" : "s"}`;
}

function populateFilterOptions() {
  const categories = [...new Set(state.allDeals.map((d) => d.category).filter(Boolean))].sort();
  const zips = [...new Set(state.allDeals.map((d) => d.zip_code).filter(Boolean))].sort();

  for (const cat of categories) {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    els.category.appendChild(opt);
  }
  for (const zip of zips) {
    const opt = document.createElement("option");
    opt.value = zip;
    opt.textContent = zip;
    els.zip.appendChild(opt);
  }
}

async function init() {
  try {
    const res = await fetch("./deals.json", { cache: "no-store" });
    const data = await res.json();
    state.allDeals = data.deals ?? [];

    populateFilterOptions();
    applyFilters();

    if (data.generated_at) {
      const when = new Date(data.generated_at).toLocaleString();
      const suffix = els.stats.textContent;
      els.stats.textContent = `${suffix} · updated ${when}`;
    }
  } catch (err) {
    els.stats.textContent = "Couldn't load deals.json";
    els.empty.classList.remove("hidden");
    els.empty.textContent = "Deal data hasn't been generated yet — run the scraper workflow first.";
    console.error(err);
  }
}

let debounceTimer;
function debouncedApply() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(applyFilters, 250);
}

[els.category, els.zip, els.minDiscount, els.inStock, els.sort].forEach((el) =>
  el.addEventListener("change", applyFilters)
);
els.search.addEventListener("input", debouncedApply);
els.maxPrice.addEventListener("input", debouncedApply);
els.loadMore.addEventListener("click", () => render({ reset: false }));

init();
