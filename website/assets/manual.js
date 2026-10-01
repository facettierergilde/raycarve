/* RayCarve manual viewer
 * Loads manual/<version>/<lang>.md and renders it. Versions come from versions.json.
 * URL: manual/?v=1.16.0&lang=de   (both optional; defaults: latest version, preferred language)
 */
(function () {
  "use strict";

  // ---------- Minimal Markdown renderer (headings, lists, tables, code, bold, links, hr, quotes) ----------
  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function inline(s) {
    var codes = [];
    s = s.replace(/`([^`]+)`/g, function (_, c) { codes.push(c); return "\u0000" + (codes.length - 1) + "\u0000"; });
    s = esc(s);
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (_, t, u) {
      var ext = /^https?:/.test(u) ? ' target="_blank" rel="noopener"' : "";
      return '<a href="' + u.replace(/"/g, "%22") + '"' + ext + ">" + t + "</a>";
    });
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|[^*\w])\*([^*\s][^*]*)\*(?!\w)/g, "$1<em>$2</em>");
    s = s.replace(/\u0000(\d+)\u0000/g, function (_, i) { return "<code>" + esc(codes[+i]) + "</code>"; });
    return s;
  }
  function slugify(t, used) {
    var s = t.toLowerCase()
      .replace(/[äÄ]/g, "ae").replace(/[öÖ]/g, "oe").replace(/[üÜ]/g, "ue")
      .replace(/<[^>]+>/g, "").replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "-") || "section";
    var base = s, n = 2;
    while (used[s]) s = base + "-" + n++;
    used[s] = true;
    return s;
  }

  function render(md) {
    var lines = md.replace(/\r\n?/g, "\n").split("\n");
    var html = [], toc = [], used = {}, i = 0, para = [];

    function flushPara() {
      if (para.length) { html.push("<p>" + inline(para.join(" ")) + "</p>"); para = []; }
    }
    function isListLine(l) { return /^\s*([-*+]|\d+[.)])\s+/.test(l); }
    function isBlockStart(l) {
      return /^#{1,6}\s/.test(l) || /^(\s*[-*_]){3,}\s*$/.test(l) || isListLine(l) || /^\s*\|/.test(l) || /^>/.test(l) || /^```/.test(l);
    }

    // Parse a list starting at line i (with given indent) -> returns html
    function parseList(indent) {
      var first = lines[i].match(/^(\s*)([-*+]|\d+[.)])\s+/);
      var ordered = /\d/.test(first[2]);
      var out = [ordered ? "<ol>" : "<ul>"];
      while (i < lines.length) {
        var m = lines[i].match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/);
        if (!m) break;
        var ind = m[1].length;
        if (ind < indent) break;
        if (ind > indent) { out.push(parseList(ind)); continue; }
        var item = [m[3]]; i++;
        // continuation lines (indented, not list items)
        while (i < lines.length && lines[i].trim() !== "" && !isListLine(lines[i]) && /^\s+/.test(lines[i])) {
          item.push(lines[i].trim()); i++;
        }
        var li = "<li>" + inline(item.join(" "));
        // nested list directly below
        while (i < lines.length) {
          var n = lines[i].match(/^(\s*)([-*+]|\d+[.)])\s+/);
          if (n && n[1].length > indent) { li += parseList(n[1].length); } else break;
        }
        out.push(li + "</li>");
        // allow a single blank line between items of the same list
        if (i < lines.length - 1 && lines[i].trim() === "") {
          var nx = lines[i + 1].match(/^(\s*)([-*+]|\d+[.)])\s+/);
          if (nx && nx[1].length >= indent) i++;
        }
      }
      out.push(ordered ? "</ol>" : "</ul>");
      return out.join("");
    }

    function splitRow(l) {
      return l.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(function (c) { return c.trim(); });
    }

    while (i < lines.length) {
      var line = lines[i];
      if (line.trim() === "") { flushPara(); i++; continue; }

      var h = line.match(/^(#{1,6})\s+(.*?)\s*#*\s*$/);
      if (h) {
        flushPara();
        var level = h[1].length, text = inline(h[2]), id = slugify(h[2], used);
        if (level === 2 || level === 3) toc.push({ level: level, id: id, text: text });
        var anchor = level > 1 ? '<a class="anchor" href="#' + id + '" aria-hidden="true">#</a>' : "";
        html.push("<h" + level + ' id="' + id + '">' + text + anchor + "</h" + level + ">");
        i++; continue;
      }
      if (/^(\s*[-*_]){3,}\s*$/.test(line)) { flushPara(); html.push("<hr>"); i++; continue; }
      if (/^```/.test(line)) {
        flushPara(); var code = []; i++;
        while (i < lines.length && !/^```/.test(lines[i])) code.push(lines[i++]);
        i++; html.push("<pre><code>" + esc(code.join("\n")) + "</code></pre>"); continue;
      }
      if (/^>/.test(line)) {
        flushPara(); var q = [];
        while (i < lines.length && /^>/.test(lines[i])) q.push(lines[i++].replace(/^>\s?/, ""));
        html.push("<blockquote>" + inline(q.join(" ")) + "</blockquote>"); continue;
      }
      if (isListLine(line)) {
        flushPara();
        html.push(parseList(line.match(/^\s*/)[0].length));
        continue;
      }
      if (/^\s*\|/.test(line) && i + 1 < lines.length && /^\s*\|?\s*:?-{2,}/.test(lines[i + 1])) {
        flushPara();
        var head = splitRow(line); i += 2;
        var rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(splitRow(lines[i++]));
        var t = '<div class="table-scroll"><table><thead><tr>' +
          head.map(function (c) { return "<th>" + inline(c) + "</th>"; }).join("") + "</tr></thead><tbody>" +
          rows.map(function (r) { return "<tr>" + r.map(function (c) { return "<td>" + inline(c) + "</td>"; }).join("") + "</tr>"; }).join("") +
          "</tbody></table></div>";
        html.push(t); continue;
      }
      if (para.length && isBlockStart(line)) flushPara();
      para.push(line.trim()); i++;
    }
    flushPara();
    return { html: html.join("\n"), toc: toc };
  }

  // ---------- Viewer ----------
  var doc = document.getElementById("doc");
  var tocList = document.getElementById("toc-list");
  var select = document.getElementById("version-select");
  var notice = document.getElementById("version-notice");
  var state = { versions: null, version: null };

  function t(de, en) { return RayCarve.getLang() === "de" ? de : en; }

  function updateUrl() {
    var p = new URLSearchParams(location.search);
    p.set("v", state.version);
    p.set("lang", RayCarve.getLang());
    history.replaceState(null, "", "?" + p.toString() + location.hash);
  }

  function showNotice() {
    var v = state.versions;
    if (state.version !== v.latest) {
      notice.innerHTML = t(
        "Du siehst das Handbuch für Version <strong>" + state.version + "</strong>. Die aktuelle Version ist <a href=\"?v=" + v.latest + "\">" + v.latest + "</a>.",
        "You are viewing the manual for version <strong>" + state.version + "</strong>. The latest version is <a href=\"?v=" + v.latest + "\">" + v.latest + "</a>."
      );
      notice.hidden = false;
    } else {
      notice.hidden = true;
    }
  }

  function fetchText(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error(url + ": HTTP " + r.status);
      return r.text();
    });
  }

  function load() {
    var lang = RayCarve.getLang();
    var dir = state.version + "/";
    doc.innerHTML = '<p class="doc-status">' + t("Lade Handbuch …", "Loading manual …") + "</p>";
    fetchText(dir + lang + ".md")
      .catch(function () {
        // fall back to the other language if a translation is missing for this version
        var other = lang === "de" ? "en" : "de";
        return fetchText(dir + other + ".md").then(function (txt) {
          return "> " + t("Für diese Version gibt es keine deutsche Übersetzung – hier die englische Fassung.",
                          "This version has no English translation – showing the German one.") + "\n\n" + txt;
        });
      })
      .then(function (md) {
        var r = render(md);
        doc.innerHTML = r.html;
        tocList.innerHTML = r.toc.map(function (e) {
          return '<li class="l' + e.level + '"><a href="#' + e.id + '">' + e.text.replace(/<a class="anchor".*$/, "") + "</a></li>";
        }).join("");
        var h1 = doc.querySelector("h1");
        document.title = (h1 ? h1.textContent : "RayCarve") + " · v" + state.version;
        showNotice();
        updateUrl();
        if (location.hash) {
          var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
          if (target) target.scrollIntoView();
        }
        spy();
      })
      .catch(function (err) {
        doc.innerHTML = '<div class="doc-status"><p><strong>' + t("Das Handbuch konnte nicht geladen werden.", "The manual could not be loaded.") +
          "</strong></p><p>" + t(
            "Wenn du die Seite lokal als Datei geöffnet hast, starte stattdessen einen kleinen Webserver im Ordner <code>website</code>, z. B. <code>python -m http.server</code>, und öffne <code>http://localhost:8000/manual/</code>.",
            "If you opened the page as a local file, start a small web server in the <code>website</code> folder instead, e.g. <code>python -m http.server</code>, and open <code>http://localhost:8000/manual/</code>."
          ) + "</p><p><code>" + esc(String(err.message || err)) + "</code></p></div>";
      });
  }

  // highlight the current section in the TOC
  var observer;
  function spy() {
    if (!("IntersectionObserver" in window)) return;
    if (observer) observer.disconnect();
    var links = {};
    tocList.querySelectorAll("a").forEach(function (a) { links[a.getAttribute("href").slice(1)] = a; });
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && links[e.target.id]) {
          tocList.querySelectorAll("a.active").forEach(function (a) { a.classList.remove("active"); });
          links[e.target.id].classList.add("active");
        }
      });
    }, { rootMargin: "-80px 0px -70% 0px" });
    doc.querySelectorAll("h2[id], h3[id]").forEach(function (h) { observer.observe(h); });
  }

  RayCarve.loadVersions().then(function (v) {
    state.versions = v;
    var want = new URLSearchParams(location.search).get("v");
    state.version = v.versions.indexOf(want) >= 0 ? want : v.latest;
    select.innerHTML = v.versions.map(function (x) {
      return '<option value="' + x + '">' + x + (x === v.latest ? " (" + t("aktuell", "latest") + ")" : "") + "</option>";
    }).join("");
    select.value = state.version;
    select.addEventListener("change", function () {
      state.version = select.value;
      history.replaceState(null, "", location.pathname + location.search);
      window.scrollTo(0, 0);
      load();
    });
    document.addEventListener("raycarve:lang", function () {
      select.querySelectorAll("option").forEach(function (o) {
        o.textContent = o.value + (o.value === v.latest ? " (" + t("aktuell", "latest") + ")" : "");
      });
      load();
    });
    load();
  }).catch(function (err) {
    doc.innerHTML = '<div class="doc-status"><p><strong>versions.json</strong> ' +
      t("konnte nicht geladen werden. Öffne die Seite über einen Webserver (z. B. GitHub Pages oder <code>python -m http.server</code>).",
        "could not be loaded. Open the page through a web server (e.g. GitHub Pages or <code>python -m http.server</code>).") + "</p></div>";
  });

  window.RayCarve.renderMarkdown = render; // handy for testing
})();
