const state = {
  offset: 0,
  limit: 48,
  total: 0,
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

function buildQuery(extra = {}) {
  const params = new URLSearchParams();
  if (els.search.value.trim()) params.set("search", els.search.value.trim());
  if (els.category.value) params.set("category", els.category.value);
  if (els.zip.value) params.set("zip_code", els.zip.value);
  if (Number(els.minDiscount.value) > 0) params.set("min_discount", els.minDiscount.value);
  if (els.maxPrice.value) params.set("max_price", els.maxPrice.value);
  if (els.inStock.checked) params.set("in_stock_only", "true");
  params.set("sort", els.sort.value);
  params.set("limit", state.limit);
  params.set("offset", extra.offset ?? 0);
  return params.toString();
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

async function loadDeals({ reset = true } = {}) {
  if (reset) {
    state.offset = 0;
    els.grid.innerHTML = "";
  }

  const res = await fetch(`/api/deals?${buildQuery({ offset: state.offset })}`);
  const data = await res.json();

  state.total = data.total;
  state.offset += data.items.length;

  els.grid.insertAdjacentHTML("beforeend", data.items.map(cardHtml).join(""));
  els.empty.classList.toggle("hidden", els.grid.children.length > 0);
  els.loadMore.classList.toggle("hidden", state.offset >= state.total);
  els.stats.textContent = `${data.total.toLocaleString()} active deal${data.total === 1 ? "" : "s"}`;
}

async function loadMeta() {
  const res = await fetch("/api/meta");
  const meta = await res.json();

  for (const cat of meta.categories) {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    els.category.appendChild(opt);
  }
  for (const zip of meta.zip_codes) {
    const opt = document.createElement("option");
    opt.value = zip;
    opt.textContent = zip;
    els.zip.appendChild(opt);
  }

  if (meta.last_scraped) {
    const when = new Date(meta.last_scraped + "Z").toLocaleString();
    els.stats.textContent = `${meta.total_deals.toLocaleString()} active deals · last updated ${when}`;
  }
}

let debounceTimer;
function debouncedReload() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => loadDeals({ reset: true }), 300);
}

[els.category, els.zip, els.minDiscount, els.inStock, els.sort].forEach((el) =>
  el.addEventListener("change", () => loadDeals({ reset: true }))
);
els.search.addEventListener("input", debouncedReload);
els.maxPrice.addEventListener("input", debouncedReload);
els.loadMore.addEventListener("click", () => loadDeals({ reset: false }));

loadMeta();
loadDeals({ reset: true });
