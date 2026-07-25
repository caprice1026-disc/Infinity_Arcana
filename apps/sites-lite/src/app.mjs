import { drawSpread } from "./engine.mjs";
import { exportStore, openStore } from "./storage.mjs";

const contentBase = globalThis.INFINITY_ARCANA_CONTENT_BASE || (location.pathname.includes("/apps/sites-lite") ? "/packages/content" : "./content");
const app = document.querySelector("#app");
const state = { content: null, store: null, lastDraw: null };

async function getJson(relativePath) { return (await fetch(`${contentBase}/${relativePath}`)).json(); }
async function loadContent() {
  const manifest = await getJson("manifest.json");
  const [cards, spreads, assets, archetypes] = await Promise.all([
    Promise.all(manifest.files.cards.map(getJson)),
    Promise.all(manifest.files.spreads.map(getJson)),
    getJson(manifest.files.assetCatalog),
    Promise.all(manifest.files.archetypes.map(getJson))
  ]);
  return { manifest, cards, spreads: Object.fromEntries(spreads.map((spread) => [spread.id, spread])), assets: Object.fromEntries(assets.assets.map((asset) => [asset.id, asset])), roots: Object.fromEntries(assets.assetRoots.map((root) => [root.id, root])), archetypes: Object.fromEntries(archetypes.map((item) => [item.id, item])) };
}
function localized(value) { if (typeof value === "string") return value; return value?.[state.content.manifest.defaultLocale || "ja-JP"] || Object.values(value || {})[0] || ""; }
function assetUrl(assetId) { const asset = state.content.assets[assetId]; const variant = asset.variants.find((item) => item.id === asset.defaultVariantId); const root = state.content.roots[variant.source.rootId]; if (root.basePath === "assets") return new URL(`./assets/${variant.source.path}`, document.baseURI).href; return `/${root.basePath}/${variant.source.path}`; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>\"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[character])); }
function cardById(id) { return state.content.cards.find((card) => card.id === id); }
function section(id, body) { return `<section id="${id}" class="${location.hash.slice(1) === id || (!location.hash && id === "home") ? "active" : ""}">${body}</section>`; }
function shell() {
  const spreadOptions = Object.values(state.content.spreads).map((spread) => `<option value="${spread.id}">${localized(spread.name)}</option>`).join("");
  app.innerHTML = [
    section("home", `<h1>知識の迷宮で、問いを読む。</h1><p class="lead">答えを増やす前に、いま何を知れば判断できるのかを見つける。知識領域アルカナのカードが、問いを静かに照らします。</p><p><a href="#draw"><button>一枚引く</button></a></p>`),
    section("draw", `<h2>カードを引く</h2><div class="panel"><label>スプレッド<select id="spread">${spreadOptions}</select></label><label>相談内容<textarea id="question" maxlength="1000" placeholder="任意の問いを書いてください"></textarea></label><button id="draw-button">カードを引く</button></div><div id="draw-results" class="cards" aria-live="polite"></div>`),
    section("collection", `<h2>図鑑</h2><p class="lead">引いたカードはこの端末に記録されます。</p><div id="collection-list" class="cards"></div>`),
    section("history", `<h2>履歴</h2><div id="history-list"></div>`),
    section("settings", `<h2>設定・データ</h2><div class="panel"><button id="export-button">データをエクスポート</button><label>データをインポート<input id="import-input" type="file" accept="application/json"></label><p id="storage-note" class="lead"></p></div>`)
  ].join("");
  document.querySelector("#draw-button").addEventListener("click", draw);
  document.querySelector("#export-button").addEventListener("click", exportData);
  document.querySelector("#import-input").addEventListener("change", importData);
  window.addEventListener("hashchange", () => { document.querySelectorAll("section").forEach((item) => item.classList.toggle("active", item.id === (location.hash.slice(1) || "home"))); });
}
async function draw() {
  const spread = state.content.spreads[document.querySelector("#spread").value];
  const cards = state.content.cards.map((card) => ({ id: card.id, archetypeId: card.archetypeId }));
  const seed = `${crypto.randomUUID()}-${Date.now()}`;
  const draws = await drawSpread(cards, spread.positions.sort((a, b) => a.order - b.order).map((position) => position.id), { seed, ...spread.constraints });
  state.lastDraw = { id: crypto.randomUUID(), requestVersion: "1.0.0", contentReleaseId: state.content.manifest.releaseId, drawPolicyId: spread.drawPolicyId, randomAlgorithm: "sha256-counter-v1", seed, spreadId: spread.id, locale: "ja-JP", question: document.querySelector("#question").value, draws, createdAt: new Date().toISOString() };
  await state.store.put("readings", state.lastDraw);
  for (const drawResult of draws) await state.store.put("collection", { id: drawResult.cardId, cardId: drawResult.cardId, firstSeenAt: new Date().toISOString() });
  renderDraw(); renderCollection(); renderHistory();
}
function renderDraw() {
  const results = document.querySelector("#draw-results"); if (!results || !state.lastDraw) return;
  results.innerHTML = state.lastDraw.draws.map((drawResult) => { const card = cardById(drawResult.cardId); return `<article class="card"><img src="${assetUrl(card.visual.cardBackAssetId)}" alt="カードの裏面"><button class="secondary reveal" data-card="${card.id}">裏面をめくる</button><div class="card-face" hidden><img src="${assetUrl(card.visual.primaryAssetId)}" alt="${localized(card.visual.altText)}"><h3>${localized(card.name)}</h3><p>${drawResult.orientation === "reversed" ? "逆位置" : "正位置"}｜${drawResult.positionId}</p><p>${localized(card.localizedContent.meanings[drawResult.orientation]?.core)}</p></div></article>`; }).join("") + `<div class="panel" style="grid-column:1/-1"><button id="interpret-button" class="secondary">Geminiで鑑定する</button><div id="interpretation" aria-live="polite"></div></div>`;
  results.querySelectorAll(".reveal").forEach((button) => button.addEventListener("click", () => { button.hidden = true; button.previousElementSibling.hidden = true; button.nextElementSibling.hidden = false; }));
  results.querySelector("#interpret-button").addEventListener("click", interpret);
}
async function interpret() { const output = document.querySelector("#interpretation"); output.textContent = "鑑定中…"; try { const response = await fetch("/api/readings/interpret", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ requestVersion: "1.0.0", locale: "ja-JP", question: state.lastDraw.question, draws: state.lastDraw.draws }) }); if (!response.ok) throw new Error("鑑定APIが利用できません"); const result = await response.json(); state.lastDraw.interpretation = result; await state.store.put("readings", state.lastDraw); await renderHistory(); const interpretations = (result.cardInterpretations || []).map((item) => `<li>${escapeHtml(item.interpretation)}</li>`).join(""); const advice = (result.advice || []).map((item) => `<li>${escapeHtml(item)}</li>`).join(""); output.innerHTML = `<h3>${result.fallbackUsed ? "定型解釈" : "Geminiの鑑定"}</h3><p>${escapeHtml(result.summary)}</p><ul>${interpretations}${advice}</ul><p>${escapeHtml(result.reflectionQuestion || "")}</p><small>${escapeHtml(result.disclaimerCode || "内省のための手がかりです。")}</small>`; } catch (error) { output.textContent = error.message; } }
async function renderCollection() { const list = document.querySelector("#collection-list"); if (!list) return; const entries = await state.store.all("collection"); list.innerHTML = entries.map((entry) => { const card = cardById(entry.cardId); return `<article class="card"><img src="${assetUrl(card.visual.primaryAssetId)}" alt="${localized(card.visual.altText)}"><h3>${localized(card.name)}</h3><p>${localized(card.subtitle)}</p></article>`; }).join("") || "<p class='lead'>まだカードはありません。</p>"; }
async function renderHistory() { const list = document.querySelector("#history-list"); if (!list) return; const entries = await state.store.all("readings"); list.innerHTML = entries.sort((a, b) => b.createdAt.localeCompare(a.createdAt)).map((entry) => `<article class="panel"><strong>${new Date(entry.createdAt).toLocaleString("ja-JP")}</strong><p>${escapeHtml(entry.question || "問いなし")}</p><p>${entry.draws.map((item) => `${escapeHtml(item.cardId)}（${escapeHtml(item.orientation)}）`).join("、")}</p>${entry.interpretation ? `<p>${escapeHtml(entry.interpretation.summary)}</p>` : ""}</article>`).join("") || "<p class='lead'>履歴はありません。</p>"; }
async function exportData() { const blob = new Blob([JSON.stringify(await exportStore(state.store), null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "infinite-arcana-data.json"; link.click(); URL.revokeObjectURL(link.href); }
async function importData(event) { const file = event.target.files[0]; if (!file) return; await state.store.replaceAll(JSON.parse(await file.text())); await renderCollection(); await renderHistory(); }
async function start() { state.content = await loadContent(); state.store = await openStore(); shell(); await renderCollection(); await renderHistory(); }
start().catch((error) => { app.innerHTML = `<section class="active"><h1>読み込みに失敗しました</h1><p class="lead">${error.message}</p></section>`; });
