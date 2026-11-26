/* Matrix-Modus: reine Optik, standardmäßig aus. Schalter neben ALARM mit zwei Quadraten:
   erstes Quadrat = Stufe 1 (dezent: Überschrift entschlüsselt sich, blasser Regen im Kopf),
   zweites Quadrat = Stufe 2 (kräftiger: zusätzlich blasser Regen über die ganze Seite, Flimmern auch auf Zwischenüberschriften).
   Auf Unterseiten (Berichte, Audit, Links) gilt die gewählte Stufe ohne eigenen Schalter.
   Modul: Zum Entfernen die Zeilen <!--matrix--> in site/index.html und pipeline/berichtseiten.py löschen (dann sind matrix.js und matrix.css ohne Wirkung).
   Hält sich an prefers-reduced-motion (dann keine Bewegung), pausiert bei verstecktem Reiter und außerhalb des Bildes.
   Keine Daten, keine Netzwerkzugriffe. Schreibt nur "matrix" in localStorage. ?matrix=0/1/2 gilt für den Aufruf. */
(function () {
  "use strict";
  var GL = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ0123456789", R = document.documentElement, an = false, stufe = 0;
  try { var g = localStorage.getItem("matrix"); stufe = g === "2" ? 2 : (g === "1" || g === "an") ? 1 : 0; } catch (e) { }
  var q = /[?&]matrix=([012])/.exec(location.search); if (q) stufe = +q[1];
  an = stufe > 0;
  var ruhe = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var zu = function () { return GL.charAt(Math.floor(Math.random() * GL.length)); };
  var kopf = null, voll = null, flimmer = null, titel = null, sichtbar = true;

  /* Überschriften: entschlüsseln sich von links nach rechts, danach selten ein kurzes Flimmern einzelner Zeichen (kein Blitzen der Fläche). */
  function textknoten(h) {
    var w = [], n;
    if (!h) return w;
    var tw = document.createTreeWalker(h, NodeFilter.SHOW_TEXT);
    while ((n = tw.nextNode())) if (n.data.trim()) w.push({ k: n, ori: n.data });
    return w;
  }
  function mische(t, fest, anzahl) {
    t.forEach(function (e) {
      if (e.k.data !== (e.gesetzt || e.ori)) return;      /* Text wurde inzwischen ersetzt (Sprachwechsel): nichts anfassen */
      var s = "", i, hit = {};
      if (anzahl) for (i = 0; i < anzahl; i++) hit[Math.floor(Math.random() * e.ori.length)] = 1;
      for (i = 0; i < e.ori.length; i++) {
        var c = e.ori.charAt(i);
        s += (c === " " || (fest !== null && i < fest && !anzahl) || (anzahl && !hit[i])) ? c : zu();
      }
      e.k.data = e.gesetzt = s;
    });
  }
  function zurueck(t) { t.forEach(function (e) { if (e.k.data === (e.gesetzt || e.ori)) e.k.data = e.ori; e.gesetzt = null; }); }
  function entschluesseln() {
    if (ruhe) return;
    var t = textknoten(document.querySelector("main h1")); if (!t.length) return; titel = t;
    var t0 = Date.now(), tick = setInterval(function () {
      var z = Math.floor((Date.now() - t0) / 22);
      if (z >= 70 || !an) { clearInterval(tick); zurueck(t); return; }
      mische(t, z, 0);
    }, 40);
  }
  function imBild(h) { var r = h.getBoundingClientRect(); return r.bottom > 0 && r.top < window.innerHeight; }
  function glitchPlanen() {
    clearTimeout(flimmer);
    if (!an || ruhe) return;
    flimmer = setTimeout(function () {
      if (an && !document.hidden) {
        var ziele = [].slice.call(document.querySelectorAll(stufe === 2 ? "main h1, main h2" : "main h1")).filter(imBild);
        if (ziele.length) {
          var t = textknoten(ziele[Math.floor(Math.random() * ziele.length)]); mische(t, null, stufe === 2 ? 4 : 3);
          setTimeout(function () { zurueck(t); }, 160);
        }
      }
      glitchPlanen();
    }, stufe === 2 ? 5000 + Math.random() * 7000 : 20000 + Math.random() * 25000);
  }

  /* Regen: blass, Farbe folgt --green (im Alarm-Modus rot). "kopf" nur im Kopfbereich oben, "voll" (nur Stufe 2) fest über die ganze Seite hinter dem Inhalt. */
  function neu(cls, host, fest) {
    var cv = document.createElement("canvas"); cv.className = cls; cv.setAttribute("aria-hidden", "true");
    if (fest) document.body.insertBefore(cv, document.body.firstChild); else host.insertBefore(cv, host.firstChild);
    var o = { cv: cv, cx: cv.getContext("2d"), host: host, fest: fest, sp: [], timer: null, abst: 18 };
    if (window.IntersectionObserver && !fest) new IntersectionObserver(function (es) { o.sicht = es[0].isIntersecting; }).observe(host);
    o.sicht = true;
    window.addEventListener("resize", function () { if (o.timer) groesse(o); });
    return o;
  }
  function groesse(o) {
    var w = o.fest ? window.innerWidth : o.host.clientWidth, h = o.fest ? window.innerHeight : o.host.clientHeight, i;
    o.cv.width = w; o.cv.height = h; o.cx.font = "13px ui-monospace,Menlo,Consolas,monospace";
    o.abst = o.fest ? 26 : (stufe === 2 ? 12 : 18);
    o.sp = []; for (i = 0; i < Math.ceil(w / o.abst); i++) o.sp.push(Math.random() * -30);
  }
  function zeichne(o) {
    if (!o.sicht || document.hidden) return;
    var h = o.cv.height, cx = o.cx, farbe = getComputedStyle(R).getPropertyValue("--green").trim() || "#6fe0a0";
    cx.globalCompositeOperation = "destination-out"; cx.fillStyle = o.fest ? "rgba(0,0,0,.1)" : "rgba(0,0,0,.16)"; cx.fillRect(0, 0, o.cv.width, h);
    cx.globalCompositeOperation = "source-over"; cx.fillStyle = farbe;
    for (var i = 0; i < o.sp.length; i++) {
      cx.fillText(zu(), i * o.abst + 2, o.sp[i] * 15);
      if (o.sp[i] * 15 > h && Math.random() > (o.fest ? .985 : .96)) o.sp[i] = Math.random() * -(o.fest ? 30 : 8); else o.sp[i] += o.fest ? .6 : (stufe === 2 ? .8 : .5);
    }
  }
  function starte(o, ms) { groesse(o); clearInterval(o.timer); o.timer = setInterval(function () { zeichne(o); }, ms); }
  function stoppe(o) { if (!o) return; clearInterval(o.timer); o.timer = null; o.cx.clearRect(0, 0, o.cv.width, o.cv.height); }
  function regen() {
    if (ruhe) return;
    var m = document.querySelector("header.marke, header.kopf");
    if (m) { if (!kopf) kopf = neu("matrix-regen", m, false); starte(kopf, stufe === 2 ? 55 : 70); }
    if (stufe === 2) { if (!voll) voll = neu("matrix-voll", document.body, true); starte(voll, 80); } else stoppe(voll);
  }

  function setze(neuStufe, speichern) {
    stufe = neuStufe; an = neuStufe > 0; R.classList.toggle("matrix", an); R.classList.toggle("matrix2", neuStufe === 2);
    if (speichern) { try { localStorage.setItem("matrix", an ? String(neuStufe) : "aus"); } catch (e) { } }
    if (an) { regen(); glitchPlanen(); } else { stoppe(kopf); stoppe(voll); clearTimeout(flimmer); if (titel) zurueck(titel); }
    var gr = document.getElementById("matrix-knopf");
    if (gr) {
      var de = (R.lang || "de") === "de", b = gr.querySelectorAll("button");
      [1, 2].forEach(function (s, i) {
        var ein = stufe >= s;
        b[i].textContent = ein ? "■" : "□"; b[i].setAttribute("aria-pressed", ein ? "true" : "false");
        b[i].setAttribute("aria-label", de ? (s === 1 ? "Matrix dezent" : "Matrix kräftiger, ganze Seite") : (s === 1 ? "Matrix subtle" : "Matrix stronger, whole page"));
      });
    }
  }
  document.addEventListener("DOMContentLoaded", function () {
    var m = document.getElementById("modus");
    if (m) {   /* Schalter nur auf der Startseite */
      var gr = document.createElement("span");
      gr.id = "matrix-knopf"; gr.className = "mono matrix-grp"; gr.setAttribute("role", "group"); gr.setAttribute("aria-label", "Matrix");
      gr.appendChild(document.createTextNode("MATRIX "));
      for (var i = 0; i < 2; i++) { var qb = document.createElement("button"); qb.type = "button"; qb.className = "mq"; gr.appendChild(qb); }
      m.parentNode.insertBefore(gr, m.nextSibling);
      var b = gr.querySelectorAll("button");
      b[0].addEventListener("click", function () { var n = stufe === 0 ? 1 : 0; setze(n, true); if (n === 1) entschluesseln(); });
      b[1].addEventListener("click", function () { var n = stufe === 2 ? 1 : 2; setze(n, true); if (n === 2 && !titel) entschluesseln(); });
    }
    setze(stufe, false); if (an) entschluesseln();
  });
})();
