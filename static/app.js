(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const DEFAULTS = { gender: "Male", age: 45, hypertension: 0, heart_disease: 0, smoking_history: "never", bmi: 27.3, HbA1c_level: 5.7, blood_glucose_level: 120 };
  const PRESETS = {
    healthy:    { gender: "Female", age: 28, hypertension: 0, heart_disease: 0, smoking_history: "never", bmi: 22.4, HbA1c_level: 4.9, blood_glucose_level: 92 },
    borderline: { gender: "Male", age: 52, hypertension: 1, heart_disease: 0, smoking_history: "former", bmi: 29.8, HbA1c_level: 6.1, blood_glucose_level: 140 },
    high:       { gender: "Male", age: 63, hypertension: 1, heart_disease: 1, smoking_history: "current", bmi: 34.5, HbA1c_level: 7.8, blood_glucose_level: 220 },
  };
  const NUM = ["age", "bmi", "HbA1c_level", "blood_glucose_level"];
  const form = $("#form");
  let ctrl = null, timer = null, last = null;

  /* ---------- theme ---------- */
  const root = document.documentElement;
  try { const t = localStorage.getItem("theme"); if (t) root.dataset.theme = t; } catch (e) {}
  $("#theme").addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  /* ---------- tabs ---------- */
  const tabs = $$('[role=tab]');
  function showTab(t) {
    tabs.forEach(b => { const on = b === t; b.setAttribute("aria-selected", on); b.tabIndex = on ? 0 : -1; $("#" + b.getAttribute("aria-controls")).hidden = !on; });
    if (t.id === "t-model") loadModel();
    history.replaceState(null, "", "#" + t.id.slice(2));
  }
  tabs.forEach((b, i) => {
    b.addEventListener("click", () => showTab(b));
    b.addEventListener("keydown", e => {
      const n = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (n) { const t = tabs[(i + n + tabs.length) % tabs.length]; t.focus(); showTab(t); }
    });
  });

  /* ---------- form <-> state ---------- */
  function read() {
    const d = { gender: form.gender.value, smoking_history: form.smoking_history.value,
      hypertension: form.hypertension.checked ? 1 : 0, heart_disease: form.heart_disease.checked ? 1 : 0 };
    NUM.forEach(k => d[k] = parseFloat(form[k].value));
    return d;
  }
  function write(d) {
    $$('input[name=gender]').forEach(r => r.checked = r.value === d.gender);
    form.smoking_history.value = d.smoking_history;
    form.hypertension.checked = !!d.hypertension; form.heart_disease.checked = !!d.heart_disease;
    NUM.forEach(k => { form[k].value = d[k]; syncRange(k); });
    bmiCat();
  }
  function syncRange(k) {
    const r = $("#" + k + "-r"), v = parseFloat(form[k].value);
    if (!r) return;
    r.value = isNaN(v) ? r.min : v;
    r.style.setProperty("--p", ((Math.min(Math.max(v, r.min), r.max) - r.min) / (r.max - r.min) * 100) + "%");
  }
  function bmiCat() {
    const b = parseFloat(form.bmi.value);
    $("#bmi-cat").textContent = isNaN(b) ? "" : b < 18.5 ? "Underweight" : b < 25 ? "Healthy range" : b < 30 ? "Overweight" : "Obese range";
  }
  const LIM = { age: [0, 120], bmi: [10, 100], HbA1c_level: [3, 15], blood_glucose_level: [50, 500] };
  function validate(d) {
    let bad = [];
    NUM.forEach(k => { const [lo, hi] = LIM[k], ok = !isNaN(d[k]) && d[k] >= lo && d[k] <= hi; form[k].classList.toggle("invalid", !ok); if (!ok) bad.push(`${$(`label[for=${k}]`).firstChild.textContent.trim()} must be between ${lo} and ${hi}`); });
    const e = $("#form-err"); e.hidden = !bad.length; e.textContent = bad.join(". ") + (bad.length ? "." : "");
    return !bad.length;
  }

  NUM.forEach(k => {
    const r = $("#" + k + "-r");
    r.addEventListener("input", () => { form[k].value = r.value; syncRange(k); if (k === "bmi") bmiCat(); schedule(); });
    form[k].addEventListener("input", () => { syncRange(k); if (k === "bmi") bmiCat(); schedule(); });
  });
  form.addEventListener("change", schedule);
  form.addEventListener("submit", e => e.preventDefault());
  $$("[data-preset]").forEach(b => b.addEventListener("click", () => { write(PRESETS[b.dataset.preset]); schedule(0); }));
  $("#reset").addEventListener("click", () => { write(DEFAULTS); schedule(0); });

  /* ---------- predict ---------- */
  function schedule(ms = 250) { clearTimeout(timer); timer = setTimeout(predict, ms); }
  async function predict() {
    const d = read();
    if (!validate(d)) return;
    ctrl && ctrl.abort(); ctrl = new AbortController();
    $("#result").classList.add("loading");
    try {
      const r = await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(d), signal: ctrl.signal });
      if (!r.ok) throw new Error(r.status === 422 ? "Some values are outside the accepted range." : "The server returned an error (" + r.status + ").");
      last = await r.json(); render(last, d); setStatus(true);
    } catch (e) {
      if (e.name === "AbortError") return;
      const el = $("#form-err"); el.hidden = false;
      el.textContent = (e instanceof TypeError ? "Can't reach the API. Check that the server is running, then change a value to retry." : e.message);
      setStatus(false);
    } finally { $("#result").classList.remove("loading"); }
  }

  const SUB = {
    low: "Readings are in a range the model rarely links to diabetes.",
    moderate: "Some readings raise risk. Consider a routine check-up.",
    high: "Several readings match patterns seen in diabetic patients. Clinical testing is advised.",
    "very high": "Readings strongly match patterns seen in diabetic patients. See a clinician soon.",
  };
  function render(r, d) {
    const pct = r.probability * 100, lv = r.risk_level;
    const res = $("#result"); res.className = "panel result risk-" + lv.split(" ")[0];
    $("#pct").textContent = pct > 99 ? ">99%" : pct < 1 ? "<1%" : (pct < 10 ? pct.toFixed(1) : Math.round(pct)) + "%";
    $("#g-fg").style.strokeDashoffset = 364.4 * (1 - r.probability);
    $("#badge").textContent = lv.charAt(0).toUpperCase() + lv.slice(1) + " risk";
    $("#verdict").textContent = r.label;
    $("#verdict-sub").textContent = SUB[lv];
    $("#disclaimer").textContent = r.disclaimer;
    // strips
    const s = $("#strips"); s.replaceChildren(
      strip("HbA1c", d.HbA1c_level, "%", 3, 10, [5.7, 6.5], [3, 5, 5.7, 6.5, 8, 10]),
      strip("Blood glucose", d.blood_glucose_level, "mg/dL", 50, 300, [140, 200], [50, 100, 140, 200, 250, 300]));
    // drivers
    drivers($("#drivers"), r.drivers.map(x => ({ label: x.label, sub: x.value, v: x.impact })));
    const w = $("#warnings"); w.hidden = !r.warnings.length; w.replaceChildren(...r.warnings.map(t => el("li", null, t)));
  }
  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function strip(name, v, unit, min, max, cuts, ticks) {
    const pos = x => Math.min(Math.max((x - min) / (max - min), 0), 1) * 100;
    const wrap = el("div", "strip");
    const h = el("div", "strip-h"); h.append(el("b", null, name), el("span", null, v + " " + unit)); wrap.append(h);
    const bar = el("div", "bar");
    [["b-ok", 0, cuts[0]], ["b-mid", cuts[0], cuts[1]], ["b-hi", cuts[1], max]].forEach(([c, a, b]) => { const i = el("i", c); i.style.width = (pos(b) - pos(a)) + "%"; bar.append(i); });
    const pin = el("div", "pin"); pin.style.left = pos(v) + "%"; pin.title = name + ": " + v + " " + unit; bar.append(pin); wrap.append(bar);
    const sc = el("div", "scale"); ticks.forEach(t => { const x = el("span", null, t); x.style.left = pos(t) + "%"; x.style.transform = pos(t) <= 0 ? "none" : pos(t) >= 100 ? "translateX(-100%)" : "translateX(-50%)"; sc.append(x); }); wrap.append(sc);
    return wrap;
  }
  function drivers(host, rows) {
    const mx = Math.max(...rows.map(r => Math.abs(r.v)), 0.01);
    host.replaceChildren(...rows.map(r => {
      const row = el("div", "drv"), l = el("div", "drv-l"); l.append(el("span", null, r.label), el("small", null, r.sub || ""));
      const t = el("div", "drv-t"), b = el("div", "drv-b " + (r.v > 0 ? "up" : "down")), w = Math.abs(r.v) / mx * 50;
      b.style.width = w + "%"; b.style.left = r.v > 0 ? "50%" : (50 - w) + "%"; t.append(b);
      t.setAttribute("role", "img"); t.setAttribute("aria-label", `${r.label} ${r.v > 0 ? "raises" : "lowers"} risk by ${Math.abs(r.v).toFixed(2)}`);
      row.append(l, t); return row;
    }));
  }

  /* ---------- status ---------- */
  function setStatus(ok) { const s = $("#status"); s.className = "status " + (ok ? "ok" : "down"); s.lastElementChild.textContent = ok ? "API online" : "API offline"; }
  fetch("/api/health").then(r => r.json()).then(h => setStatus(h.model_loaded)).catch(() => setStatus(false));

  /* ---------- model tab ---------- */
  let modelLoaded = false;
  async function loadModel() {
    if (modelLoaded) return;
    try {
      const m = await (await fetch("/api/model-info")).json(), x = m.metrics, f = v => (v * 100).toFixed(1) + "%";
      $("#model-sub").textContent = `${m.algorithm}, class weights ${m.class_weight}. Measured on ${x.test_rows.toLocaleString()} held-out patients.`;
      const cards = [["Recall", x.recall, "Share of diabetic patients the model catches"], ["Precision", x.precision, "Share of positive flags that are correct"],
        ["Accuracy", x.accuracy, "Share of all predictions that are correct"], ["F1 score", x.f1, "Balance of precision and recall"], ["ROC AUC", x.roc_auc, "How well it ranks diabetic above non-diabetic"]];
      $("#metrics").replaceChildren(...cards.map(([n, v, d]) => { const c = el("div", "metric"); c.append(el("b", null, f(v)), el("span", null, n), el("small", null, d)); return c; }));
      const c = x.confusion, cf = $("#confusion"), cell = (cls, n, t) => { const e = el("div", "c " + cls); e.append(el("b", null, n.toLocaleString()), el("span", null, t)); return e; };
      cf.replaceChildren(el("div"), el("div", "h", "Predicted no diabetes"), el("div", "h", "Predicted diabetes"),
        el("div", "h", "Actually no diabetes"), cell("good", c.tn, "Correct"), cell("bad", c.fp, "False alarm"),
        el("div", "h", "Actually diabetes"), cell("bad", c.fn, "Missed"), cell("good", c.tp, "Caught"));
      $("#conf-note").textContent = `Out of ${(c.fn + c.tp).toLocaleString()} diabetic patients, ${c.tp.toLocaleString()} were caught.`;
      drivers($("#coefs"), m.feature_importance.map(i => ({ label: i.label, sub: "weight " + i.coefficient.toFixed(2), v: i.coefficient })));
      $("#model-note").textContent = `Only ${(x.positive_rate * 100).toFixed(1)}% of patients in the data have diabetes, so the model is tuned with balanced class weights to avoid missing them. The trade-off is precision: about ${Math.round((1 - x.precision) * 100)}% of positive flags are false alarms. That suits screening, where a missed case costs more than an extra test, but a positive result is a prompt for confirmation, not a diagnosis. HbA1c and blood glucose carry the most weight, followed by age.`;
      modelLoaded = true;
    } catch (e) { $("#model-sub").textContent = "Couldn't load model details. Check that the API is running and reload."; }
  }

  /* ---------- api tab / copy ---------- */
  const curl = () => `curl -X POST ${location.origin}/api/predict \\\n  -H "Content-Type: application/json" \\\n  -d '${JSON.stringify(read(), null, 2)}'`;
  function toast(t) { const e = $("#toast"); e.textContent = t; e.classList.add("show"); setTimeout(() => e.classList.remove("show"), 1800); }
  async function copy() { try { await navigator.clipboard.writeText(curl()); toast("Request copied"); } catch (e) { toast("Copy isn't available in this browser"); } }
  $("#copy").addEventListener("click", copy); $("#copy2").addEventListener("click", copy);
  tabs.find(t => t.id === "t-api").addEventListener("click", () => $("#curl").textContent = curl());
  $("#print").addEventListener("click", () => print());

  /* ---------- init ---------- */
  write(DEFAULTS); predict();
  const h = location.hash.slice(1); const t = tabs.find(b => b.id === "t-" + h); if (t) showTab(t);
})();
