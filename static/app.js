/* Diccionario bilingüe REALITER: cliente sin dependencias externas. */
"use strict";
const state = { words: [], selectedId: null, total: 0, editKey: "", localEdit: false, passwordNeeded: false, panel: "dictionary" };
const $ = (id) => document.getElementById(id);

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}
function announce(message, error = false) {
  const node = $("notice");
  node.textContent = message;
  node.className = error ? "notice error" : "notice";
  node.hidden = false;
  window.scrollTo({ top: 310, behavior: "smooth" });
}
function clearNotice() { $("notice").hidden = true; }
function editHeaders() {
  return { "Content-Type": "application/json", ...(state.editKey ? { "X-Edit-Key": state.editKey } : {}) };
}
async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Error HTTP ${response.status}`);
  return data;
}
function requireEditor() {
  if (state.localEdit || state.editKey) return true;
  if (!state.passwordNeeded) { announce("Solo puedes modificar este diccionario desde la computadora donde se ejecuta, o configurar EDIT_PASSWORD para edición remota.", true); return false; }
  const key = window.prompt("Clave de edición del taller (no se guarda en el navegador):");
  if (!key) return false;
  state.editKey = key;
  $("auth-button").textContent = "Cambiar contraseña";
  return true;
}
function showPanel(name) {
  clearNotice();
  state.panel = name;
  document.querySelectorAll(".tab").forEach(button => {
    const active = button.dataset.panel === name;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  ["dictionary", "new", "yaml"].forEach(section => {
    const item = $(section + "-panel");
    item.hidden = section !== name;
    item.classList.toggle("visible", section === name);
  });
  if (name === "yaml") loadYaml();
}
function audioButton(text, lang, path, compact = false) {
  const button = element("button", compact ? "example-audio" : "audio-button");
  button.type = "button";
  button.title = `Escuchar audio ${lang === "ro-RO" ? "en rumano" : "en español"}`;
  button.setAttribute("aria-label", button.title);
  button.textContent = compact ? "▶" : `▶ Escuchar ${lang === "ro-RO" ? "RO" : "ES"}`;
  button.addEventListener("click", async () => {
    try {
      if (path) {
        window.speechSynthesis?.cancel();
        const sound = new Audio("/media/" + encodeURIComponent(path));
        await sound.play();
      } else {
        if (!("speechSynthesis" in window)) throw new Error("El navegador no admite síntesis de voz.");
        window.speechSynthesis.cancel();
        const voice = new SpeechSynthesisUtterance(text);
        voice.lang = lang;
        voice.rate = 0.87;
        const voices = window.speechSynthesis.getVoices();
        const matching = voices.find(v => v.lang.toLowerCase() === lang.toLowerCase()) || voices.find(v => v.lang.toLowerCase().startsWith(lang.substring(0, 2).toLowerCase()));
        if (matching) voice.voice = matching;
        window.speechSynthesis.speak(voice);
      }
    } catch (e) { announce("No fue posible reproducir este audio. Revisa el navegador o el archivo cargado.", true); }
  });
  return button;
}
function renderResults() {
  const list = $("result-list");
  list.replaceChildren();
  $("total-count").textContent = `${state.total} entradas en YAML`;
  $("result-count").textContent = `${state.words.length} coincidencia${state.words.length === 1 ? "" : "s"}`;
  if (!state.words.length) {
    list.append(element("div", "results-empty", "No hay coincidencias. Prueba con otra palabra o agrega una nueva."));
    $("detail").replaceChildren(element("div", "empty", "No se encontraron entradas para esta búsqueda."));
    return;
  }
  if (!state.words.some(w => w.id === state.selectedId)) state.selectedId = state.words[0].id;
  for (const word of state.words) {
    const button = element("button", "result-item" + (word.id === state.selectedId ? " active" : ""));
    button.type = "button";
    const left = element("span");
    left.append(element("strong", "", word.es), element("small", "", word.ro));
    button.append(left, element("span", "arrow", "›"));
    button.addEventListener("click", () => { state.selectedId = word.id; renderResults(); });
    list.append(button);
  }
  renderDetail();
}
function makeExample(ex) {
  const card = element("div", "example-card");
  [["ES", ex.es, "es-ES", ex.audio_es], ["RO", ex.ro, "ro-RO", ex.audio_ro]].forEach(([name, phrase, locale, path]) => {
    const row = element("div", "example-lang");
    row.append(element("span", "language-pill", name), element("span", "example-sentence", phrase), audioButton(phrase, locale, path, true));
    card.append(row);
  });
  return card;
}
function renderDetail() {
  const word = state.words.find(w => w.id === state.selectedId);
  if (!word) return;
  const detail = $("detail");
  detail.replaceChildren();
  const top = element("div", "detail-top");
  const topLeft = element("div");
  topLeft.append(element("span", "word-kind", "Entrada lexicográfica · Español / Rumano"));
  const pair = element("div", "word-pair");
  pair.append(element("h3", "", word.es), element("span", "separator", "↔"), element("h3", "", word.ro));
  topLeft.append(pair);
  const audioLine = element("div", "audio-line");
  audioLine.append(audioButton(word.es, "es-ES", word.audio_es), audioButton(word.ro, "ro-RO", word.audio_ro));
  topLeft.append(audioLine);
  top.append(topLeft);
  detail.append(top, element("div", "detail-divider"), element("div", "field-label", "Significado"), element("p", "meaning-text", word.significado), element("div", "detail-divider"));
  const h = element("div", "examples-heading");
  h.append(element("h4", "", `Ejemplos de uso (${word.ejemplos.length})`));
  const add = element("button", "mini-button", "＋ Agregar ejemplo");
  add.type = "button";
  add.addEventListener("click", () => {
    if (!requireEditor()) return;
    $("example-form").hidden = false;
    $("example-form").scrollIntoView({ behavior: "smooth", block: "nearest" });
  });
  h.append(add);
  detail.append(h);
  if (!word.ejemplos.length) detail.append(element("p", "", "Todavía no hay ejemplos registrados."));
  for (const example of word.ejemplos) detail.append(makeExample(example));

  const exampleForm = document.createElement("form");
  exampleForm.id = "example-form";
  exampleForm.className = "example-form";
  exampleForm.hidden = true;
  exampleForm.innerHTML = `<h4>Nuevo ejemplo para esta palabra</h4>
    <div class="form-grid"><label>Oración en español<textarea name="es" rows="2" required maxlength="500"></textarea></label>
    <label>Oración en rumano<textarea name="ro" rows="2" required maxlength="500"></textarea></label>
    <label>Audio del ejemplo · ES (opcional)<input id="append-audio-es" type="file" accept="audio/*,.wav,.mp3,.ogg,.m4a,.webm"></label>
    <label>Audio del ejemplo · RO (opcional)<input id="append-audio-ro" type="file" accept="audio/*,.wav,.mp3,.ogg,.m4a,.webm"></label></div>
    <div class="form-footer"><span>Se añadirá como un nuevo elemento de <code>ejemplos:</code></span><button type="submit" class="button button-primary">Guardar ejemplo</button></div>`;
  exampleForm.addEventListener("submit", submitExample);
  detail.append(exampleForm);
}
async function loadWords() {
  const q = $("search-input").value;
  const result = await requestJson("/api/entries?q=" + encodeURIComponent(q));
  state.words = result.palabras;
  state.total = result.total;
  renderResults();
}
async function toAudioPayload(inputId) {
  const file = $(inputId)?.files?.[0];
  if (!file) return null;
  if (file.size > 2 * 1024 * 1024) throw new Error(`El archivo ${file.name} supera 2 MB.`);
  return await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error(`No se pudo leer ${file.name}.`));
    reader.onload = () => resolve({ filename: file.name, content: String(reader.result).split(",")[1] });
    reader.readAsDataURL(file);
  });
}
async function submitWord(ev) {
  ev.preventDefault();
  if (!requireEditor()) return;
  const button = ev.submitter;
  button.disabled = true;
  const form = new FormData(ev.currentTarget);
  try {
    const payload = Object.fromEntries(form.entries());
    Object.assign(payload, {
      audio_es: await toAudioPayload("word-audio-es"), audio_ro: await toAudioPayload("word-audio-ro"),
      ejemplo_audio_es: await toAudioPayload("example-audio-es"), ejemplo_audio_ro: await toAudioPayload("example-audio-ro"),
    });
    const result = await requestJson("/api/words", { method: "POST", headers: editHeaders(), body: JSON.stringify(payload) });
    ev.currentTarget.reset();
    showPanel("dictionary");
    $("search-input").value = result.palabra.es;
    state.selectedId = result.palabra.id;
    await loadWords();
    announce(`Guardamos «${result.palabra.es} ↔ ${result.palabra.ro}» en diccionario.yaml.`);
  } catch (e) { announce(e.message, true); }
  finally { button.disabled = false; }
}
async function submitExample(ev) {
  ev.preventDefault();
  if (!requireEditor()) return;
  const id = state.selectedId;
  const button = ev.submitter;
  button.disabled = true;
  const form = new FormData(ev.currentTarget);
  try {
    const payload = { es: form.get("es"), ro: form.get("ro"), audio_es: await toAudioPayload("append-audio-es"), audio_ro: await toAudioPayload("append-audio-ro") };
    await requestJson(`/api/words/${encodeURIComponent(id)}/examples`, { method: "POST", headers: editHeaders(), body: JSON.stringify(payload) });
    await loadWords();
    announce("Se añadió el nuevo ejemplo en la lista YAML de esta palabra.");
  } catch (e) { announce(e.message, true); }
  finally { button.disabled = false; }
}
async function loadYaml() {
  try {
    const response = await fetch("/api/yaml");
    if (!response.ok) throw new Error("No se pudo recuperar el YAML.");
    $("yaml-editor").value = await response.text();
    $("yaml-hint").textContent = "Edita con cuidado y conserva la sangría. Los errores de sintaxis se detectan al guardar.";
  } catch (e) { announce(e.message, true); }
}
async function saveYaml() {
  if (!requireEditor()) return;
  const btn = $("save-yaml");
  btn.disabled = true;
  try {
    const saved = await requestJson("/api/yaml", { method: "PUT", headers: editHeaders(), body: JSON.stringify({ yaml: $("yaml-editor").value }) });
    await loadYaml();
    await loadWords();
    announce(`YAML válido. Se guardaron ${saved.total} entradas. Vuelve a la pestaña «Explorar diccionario» para ver los cambios.`);
  } catch (e) { announce(`No se guardó el YAML: ${e.message}`, true); }
  finally { btn.disabled = false; }
}
async function init() {
  try {
    const status = await requestJson("/api/status");
    state.localEdit = status.local_edit;
    state.passwordNeeded = status.password_needed;
    $("auth-button").textContent = status.local_edit ? "Edición local activa" : status.password_needed ? "Introducir clave" : "Solo lectura";
    $("auth-button").addEventListener("click", () => {
      if (!state.passwordNeeded) { announce(state.localEdit ? "La edición está habilitada en este equipo." : "Esta instalación es de solo lectura para visitantes remotos."); return; }
      const key = window.prompt("Clave de edición del taller:");
      if (key) { state.editKey = key; $("auth-button").textContent = "Cambiar contraseña"; announce("Clave registrada para esta sesión. Se comprobará al guardar."); }
    });
    await loadWords();
  } catch (e) { announce(`No se pudo conectar al servidor: ${e.message}`, true); }
  document.querySelectorAll(".tab").forEach(button => button.addEventListener("click", () => showPanel(button.dataset.panel)));
  $("new-form").addEventListener("submit", submitWord);
  $("save-yaml").addEventListener("click", saveYaml);
  let debounce;
  $("search-input").addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => loadWords().catch(e => announce(e.message, true)), 180);
  });
}
document.addEventListener("DOMContentLoaded", init);
