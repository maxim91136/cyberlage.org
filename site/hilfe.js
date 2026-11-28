(function () {
  "use strict";
  /* Hilfe für Erstbesucher, ohne Cookie, ohne Tracking und ohne Speicherung:
     Fachwörter im Fließtext sind antippbar und zeigen die Erklärung aus der Begriffe-Liste (eine einzige Quelle, in der Seitensprache).
     Nur wo der Browser das native popover kann; sonst bleibt der Text unverändert. */
  var de = (document.documentElement.lang || "de") === "de";

  if (!("popover" in HTMLElement.prototype)) return;
  var ERLAUBT = ["KEV", "EPSS", "CVSS", "CVE", "CISA", "CERT-Bund", "EUVD", "ENISA", "Infocon", "DShield", "MSRC", "NCSC-NL", "NVD", "LTSC",
    "RansomLook", "Perzentil", "Percentile", "Median", "Patch Day", "Out-of-band", "BSI Cyber Index"];
  var BEREICH = "#hero-kurz,#fazit,#rd-kon,#radar .fine,#i-faq,#i-methode,#i-begruendung,main .lead";
  var AUSGENOMMEN = "a,button,summary,dt,h1,h2,h3,h4,script,style,.bg,[popover]";
  var ZEICHEN = "A-Za-z0-9ÄÖÜäöüß";

  function begriffe() {
    var m = {}, dl = document.querySelector("#i-begriffe dl");
    if (!dl) return m;
    Array.prototype.forEach.call(dl.querySelectorAll("dt"), function (dt) {
      var dd = dt.nextElementSibling; if (!dd) return;
      dt.textContent.replace(/\(.*?\)/g, "").split("/").forEach(function (n) {
        n = n.trim(); if (ERLAUBT.indexOf(n) > -1) m[n] = dd.textContent;
      });
    });
    return m;
  }
  function block(n, c) { return n.closest("p,dd,li,td,div") || c; }

  function ausfuehren() {
    var m = begriffe(), namen = Object.keys(m).sort(function (a, b) { return b.length - a.length; });
    if (!namen.length) return;
    var re = new RegExp("(^|[^" + ZEICHEN + "-])(" + namen.map(function (s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }).join("|") + ")(?![" + ZEICHEN + "])", "g");
    var gesehen = new WeakMap();
    Array.prototype.forEach.call(document.querySelectorAll(BEREICH), function (c) {
      Array.prototype.forEach.call(c.querySelectorAll(".bg"), function (b) {   // schon umgesetzte Wörter zählen mit: je Absatz nur das erste Vorkommen
        var bl = block(b, c), s = gesehen.get(bl) || {}; s[b.getAttribute("data-bg")] = 1; gesehen.set(bl, s);
      });
      var w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT, { acceptNode: function (n) {
        var p = n.parentElement; return !p || p.closest(AUSGENOMMEN) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      } }), liste = [];
      while (w.nextNode()) liste.push(w.currentNode);
      liste.forEach(function (n) {
        var bl = block(n.parentElement, c), s = gesehen.get(bl) || {}; gesehen.set(bl, s);
        var t = n.nodeValue, frag = document.createDocumentFragment(), pos = 0, mm, neu = false;
        re.lastIndex = 0;
        while ((mm = re.exec(t))) {
          var term = mm[2], start = mm.index + mm[1].length;
          if (s[term]) continue;
          s[term] = 1; neu = true;
          frag.appendChild(document.createTextNode(t.slice(pos, start)));
          var b = document.createElement("button"); b.type = "button"; b.className = "bg"; b.setAttribute("data-bg", term); b.textContent = term;
          b.setAttribute("aria-haspopup", "dialog"); frag.appendChild(b); pos = start + term.length;
        }
        if (neu) { frag.appendChild(document.createTextNode(t.slice(pos))); n.parentNode.replaceChild(frag, n); }
      });
    });
  }

  var timer = null, obs = new MutationObserver(function () { clearTimeout(timer); timer = setTimeout(lauf, 300); });
  function beobachte() { Array.prototype.forEach.call(document.querySelectorAll(BEREICH), function (c) { obs.observe(c, { childList: true, subtree: true }); }); }
  function lauf() { obs.disconnect(); try { ausfuehren(); } catch (e) { /* Hilfe ist nur Zugabe */ } beobachte(); }

  var pop = document.createElement("div");
  pop.id = "bg-pop"; pop.setAttribute("popover", "auto"); pop.setAttribute("role", "dialog"); pop.tabIndex = -1;
  pop.innerHTML = '<b class="bg-t"></b><p class="bg-d"></p><p class="bg-m mono"><a href="#info" data-offen="i-begriffe"></a></p>';
  document.body.appendChild(pop);
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".bg");
    if (b) {
      var term = b.getAttribute("data-bg");
      pop.querySelector(".bg-t").textContent = term;
      pop.querySelector(".bg-d").textContent = begriffe()[term] || "";
      pop.querySelector("a").textContent = de ? "Alle Begriffe ▸" : "All terms ▸";
      pop.setAttribute("aria-label", term);
      try { pop.showPopover(); pop.focus(); } catch (x) { }
      return;
    }
    if (e.target.closest && e.target.closest("#bg-pop a")) { try { pop.hidePopover(); } catch (x) { } }
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", lauf); else lauf();
})();
