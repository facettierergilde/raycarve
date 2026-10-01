/* RayCarve website — shared script: language switch, version info, copy button */
(function () {
  "use strict";

  // ---------- Language ----------
  var LANGS = ["de", "en"];

  function storedLang() {
    try { return localStorage.getItem("raycarve-lang"); } catch (e) { return null; }
  }
  function detectLang() {
    var q = new URLSearchParams(location.search).get("lang");
    if (LANGS.indexOf(q) >= 0) return q;
    var s = storedLang();
    if (LANGS.indexOf(s) >= 0) return s;
    var nav = (navigator.languages && navigator.languages[0]) || navigator.language || "en";
    return /^de\b/i.test(nav) ? "de" : "en";
  }
  function setLang(lang, persist) {
    document.documentElement.setAttribute("data-lang", lang);
    document.documentElement.setAttribute("lang", lang);
    document.querySelectorAll(".lang-switch button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.setLang === lang));
    });
    var t = document.querySelector('meta[name="title-' + lang + '"]');
    if (t) document.title = t.content;
    if (persist) { try { localStorage.setItem("raycarve-lang", lang); } catch (e) {} }
    document.dispatchEvent(new CustomEvent("raycarve:lang", { detail: lang }));
  }
  window.RayCarve = window.RayCarve || {};
  window.RayCarve.getLang = function () { return document.documentElement.getAttribute("data-lang") || "en"; };
  window.RayCarve.setLang = setLang;

  setLang(detectLang(), false);

  document.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-set-lang]");
    if (b) setLang(b.dataset.setLang, true);
  });

  // ---------- Versions ----------
  // versions.json is the single source of truth for released versions.
  // build.cmd updates it automatically when a new version is built.
  function base() {
    var el = document.querySelector('meta[name="site-root"]');
    return el ? el.content : "./";
  }
  window.RayCarve.loadVersions = function () {
    return fetch(base() + "versions.json", { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error("versions.json: HTTP " + r.status);
      return r.json();
    });
  };

  function fillVersionInfo(v) {
    document.querySelectorAll("[data-version]").forEach(function (el) { el.textContent = v.latest; });
    document.querySelectorAll("[data-blender-min]").forEach(function (el) { el.textContent = v.blender_min; });
    document.querySelectorAll("[data-download]").forEach(function (el) {
      el.setAttribute("href", base() + "downloads/RayCarve-" + v.latest + ".zip");
      el.setAttribute("download", "RayCarve-" + v.latest + ".zip");
    });
    var older = document.getElementById("older-versions");
    if (older) {
      var prev = (v.versions || []).filter(function (x) { return x !== v.latest; });
      if (prev.length) {
        var links = prev.map(function (x) {
          return '<a href="' + base() + "downloads/RayCarve-" + x + '.zip">' + x + "</a>";
        }).join(", ");
        older.querySelector(".list").innerHTML = links;
        older.hidden = false;
      }
    }
  }
  if (document.querySelector("[data-version], [data-download]")) {
    window.RayCarve.loadVersions().then(fillVersionInfo).catch(function () { /* keep static fallback */ });
  }

  // ---------- Copy to clipboard ----------
  document.addEventListener("click", function (ev) {
    var b = ev.target.closest("[data-copy]");
    if (!b || !navigator.clipboard) return;
    navigator.clipboard.writeText(b.dataset.copy).then(function () {
      var old = b.innerHTML;
      b.innerHTML = RayCarve.getLang() === "de" ? "Kopiert ✓" : "Copied ✓";
      setTimeout(function () { b.innerHTML = old; }, 1600);
    });
  });

  // ---------- Header style over the dark hero ----------
  var header = document.querySelector(".site-header");
  var hero = document.querySelector(".hero");
  if (header && hero && "IntersectionObserver" in window) {
    header.classList.add("on-hero");
    new IntersectionObserver(function (entries) {
      header.classList.toggle("on-hero", entries[0].isIntersecting);
    }, { rootMargin: "-61px 0px 0px 0px" }).observe(hero);
  }
})();
