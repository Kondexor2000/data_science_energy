const colors = ["#38bdf8", "#16a34a", "#facc15", "#84cc16", "#64748b"];
const series = [
  ["hydro_twh", "Woda"],
  ["wind_twh", "Wiatr"],
  ["solar_twh", "Słońce"],
  ["other_renewables_twh", "Pozostałe OZE"],
  ["fossil_twh", "Paliwa kopalne"],
];
const number = (value, digits = 1) =>
  value == null || !Number.isFinite(Number(value))
    ? "brak danych"
    : Number(value).toLocaleString("pl-PL", { maximumFractionDigits: digits, minimumFractionDigits: digits });
const validShare = (rows) => rows.filter((row) => row.renewables_share_pct != null && Number.isFinite(Number(row.renewables_share_pct)));

function linearFit(rows) {
  const xs = rows.map((row) => Number(row.year));
  const ys = rows.map((row) => Number(row.renewables_share_pct));
  const meanX = xs.reduce((sum, value) => sum + value, 0) / xs.length;
  const meanY = ys.reduce((sum, value) => sum + value, 0) / ys.length;
  const slope = xs.reduce((sum, x, i) => sum + (x - meanX) * (ys[i] - meanY), 0) /
    xs.reduce((sum, x) => sum + (x - meanX) ** 2, 0);
  return { slope, intercept: meanY - slope * meanX };
}

function svgChart(rows, { value, min, max, forecast = [], label }) {
  const width = 760;
  const height = 300;
  const pad = { left: 48, right: 18, top: 16, bottom: 35 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const all = [...rows, ...forecast];
  const firstYear = Number(all[0].year);
  const lastYear = Number(all[all.length - 1].year);
  const x = (year) => pad.left + ((Number(year) - firstYear) / Math.max(1, lastYear - firstYear)) * plotW;
  const y = (amount) => pad.top + ((max - amount) / (max - min)) * plotH;
  const path = (items) => items.map((row, i) =>
    `${i ? "L" : "M"}${x(row.year).toFixed(1)},${y(Number(row[value])).toFixed(1)}`
  ).join(" ");
  const ticks = [0, 1, 2, 3, 4].map((index) => min + ((max - min) * index) / 4);
  const yearTicks = [...new Set([firstYear, Math.round((firstYear + lastYear) / 2), lastYear])];
  return `<svg viewBox="0 0 ${width} ${height}" aria-label="${label}">
    ${ticks.map((tick) => `<line class="grid-line" x1="${pad.left}" y1="${y(tick)}" x2="${width - pad.right}" y2="${y(tick)}"></line><text class="axis-label" x="${pad.left - 8}" y="${y(tick) + 4}" text-anchor="end">${Math.round(tick)}</text>`).join("")}
    ${yearTicks.map((year) => `<text class="axis-label" x="${x(year)}" y="${height - 8}" text-anchor="middle">${year}</text>`).join("")}
    <path class="chart-line" d="${path(rows)}"></path>
    ${forecast.length ? `<path class="forecast-line" d="${path([rows[rows.length - 1], ...forecast])}"></path>` : ""}
  </svg>`;
}

function renderShareChart(rows) {
  const clean = validShare(rows);
  const model = linearFit(clean);
  const lastYear = Number(clean[clean.length - 1].year);
  const horizon = Number(document.querySelector("#horizon").value);
  const forecast = Array.from({ length: horizon }, (_, index) => {
    const year = lastYear + index + 1;
    return { year, renewables_share_pct: Math.max(0, Math.min(100, model.intercept + model.slope * year)) };
  });
  document.querySelector("#share-chart").innerHTML = svgChart(clean, {
    value: "renewables_share_pct", min: 0, max: 100, forecast, label: "Udział OZE w latach historycznych i scenariusz trendu",
  });
}

function renderMixChart(rows) {
  if (!rows.length) {
    document.querySelector("#mix-chart").textContent = "Brak kompletnych danych o składnikach miksu.";
    return;
  }
  const width = 760;
  const height = 300;
  const pad = { left: 48, right: 18, top: 16, bottom: 35 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const maxTotal = Math.max(...rows.map((row) => series.reduce((sum, [key]) => sum + (Number(row[key]) || 0), 0)));
  const firstYear = Number(rows[0].year);
  const lastYear = Number(rows[rows.length - 1].year);
  const x = (year) => pad.left + ((Number(year) - firstYear) / Math.max(1, lastYear - firstYear)) * plotW;
  const y = (amount) => pad.top + plotH - (amount / maxTotal) * plotH;
  const points = rows.map((row) => ({ year: Number(row.year), amounts: series.map(([key]) => Number(row[key]) || 0) }));
  let lower = points.map((point) => ({ year: point.year, value: 0 }));
  const shapes = series.map(([, name], index) => {
    const upper = points.map((point, i) => ({
      year: point.year,
      value: lower[i].value + point.amounts[index],
    }));
    const line = upper.map((point, i) => `${i ? "L" : "M"}${x(point.year).toFixed(1)},${y(point.value).toFixed(1)}`).join(" ");
    const reverse = lower.slice().reverse().map((point) => `L${x(point.year).toFixed(1)},${y(point.value).toFixed(1)}`).join(" ");
    const color = colors[index];
    lower = upper;
    return `<path class="mix-area" fill="${color}" d="${line} ${reverse} Z"><title>${name}</title></path>`;
  }).join("");
  const ticks = [0, 1, 2, 3, 4].map((index) => (maxTotal * index) / 4);
  const years = [...new Set([firstYear, Math.round((firstYear + lastYear) / 2), lastYear])];
  document.querySelector("#mix-chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-label="Produkcja energii elektrycznej w TWh według źródła">
    ${ticks.map((tick) => `<line class="grid-line" x1="${pad.left}" y1="${y(tick)}" x2="${width - pad.right}" y2="${y(tick)}"></line><text class="axis-label" x="${pad.left - 8}" y="${y(tick) + 4}" text-anchor="end">${Math.round(tick)}</text>`).join("")}
    ${years.map((year) => `<text class="axis-label" x="${x(year)}" y="${height - 8}" text-anchor="middle">${year}</text>`).join("")}
    ${shapes}
  </svg>`;
  document.querySelector("#mix-legend").innerHTML = series.map(([, name], index) =>
    `<li><span class="swatch" style="background:${colors[index]}"></span>${name}</li>`
  ).join("");
}

function renderValidation(rows) {
  const clean = validShare(rows);
  const test = clean.slice(-3);
  const train = clean.slice(0, -3);
  if (train.length < 3 || test.length !== 3) {
    document.querySelector("#model-mae").textContent = "n/d";
    document.querySelector("#baseline-mae").textContent = "n/d";
    return;
  }
  const model = linearFit(train);
  const baseline = Number(train[train.length - 1].renewables_share_pct);
  const errors = test.map((row) => {
    const actual = Number(row.renewables_share_pct);
    const prediction = Math.max(0, Math.min(100, model.intercept + model.slope * Number(row.year)));
    return [Math.abs(actual - prediction), Math.abs(actual - baseline)];
  });
  document.querySelector("#model-mae").textContent = number(errors.reduce((sum, pair) => sum + pair[0], 0) / errors.length, 2);
  document.querySelector("#baseline-mae").textContent = number(errors.reduce((sum, pair) => sum + pair[1], 0) / errors.length, 2);
}

function renderTable(rows) {
  const recent = rows.slice(-10).reverse();
  document.querySelector("#data-rows").innerHTML = recent.map((row) =>
    `<tr><td>${Number(row.year)}</td><td>${number(row.generation_twh)}</td><td>${number(row.renewables_twh)}</td><td>${number(row.renewables_share_pct)}%</td><td>${number(row.carbon_intensity_gco2e_kwh, 0)}</td></tr>`
  ).join("");
}

function render(rows) {
  const clean = validShare(rows);
  if (!clean.length) throw new Error("Zbiór nie zawiera kompletnych danych o udziale OZE.");
  const latest = clean[clean.length - 1];
  const previous = clean.length > 1 ? clean[clean.length - 2] : latest;
  document.querySelector("#renewables").textContent = `${number(latest.renewables_share_pct)}%`;
  document.querySelector("#renewables-change").textContent =
    `${number(Number(latest.renewables_share_pct) - Number(previous.renewables_share_pct))} p.p. r/r`;
  document.querySelector("#generation").textContent = `${number(latest.generation_twh)} TWh`;
  document.querySelector("#generation-year").textContent = `rok ${Number(latest.year)}`;
  document.querySelector("#intensity").textContent = number(latest.carbon_intensity_gco2e_kwh, 0);
  renderShareChart(rows);
  renderMixChart(rows.filter((row) => series.every(([key]) => row[key] != null)));
  renderValidation(rows);
  renderTable(rows);
  document.querySelector("#dashboard").hidden = false;
  document.querySelector("#status").hidden = true;
}

document.querySelector("#horizon").addEventListener("change", () => {
  if (window.energyRows) renderShareChart(window.energyRows);
});

fetch("./data/poland_energy.json")
  .then((response) => {
    if (!response.ok) throw new Error(`Nie udało się pobrać danych (HTTP ${response.status}).`);
    return response.json();
  })
  .then((rows) => {
    if (!Array.isArray(rows) || rows.length === 0) throw new Error("Plik danych jest pusty lub ma nieprawidłowy format.");
    window.energyRows = rows;
    render(rows);
  })
  .catch((error) => {
    const status = document.querySelector("#status");
    status.classList.add("error");
    status.textContent = `${error.message} Dane są przygotowywane przy wdrożeniu; spróbuj ponownie później.`;
  });
