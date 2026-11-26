/* Matrix-Modus: reine Optik, standardmäßig aus, per Schalter neben ALARM zuschaltbar (Stufen: aus, 1 dezent, 2 kräftiger).
   Auf Unterseiten (Berichte, Audit, Links) gilt die gewählte Stufe ohne eigenen Schalter.
   Modul: Zum Entfernen die Zeilen <!--matrix--> in site/index.html und pipeline/berichtseiten.py löschen (dann sind matrix.js und matrix.css ohne Wirkung).
   Hält sich an prefers-reduced-motion (dann keine Bewegung), pausiert bei verstecktem Reiter und außerhalb des Bildes.
   Keine Daten, keine Netzwerkzugriffe. Schreibt nur "matrix" in localStorage. ?matrix=1 / ?matrix=0 schaltet für den Aufruf. */
(function () {
  "use strict";
  var GL = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ0123456789", R = document.documentElement, an = false, stufe = 0;
  try { var g = localStorage.getItem("matrix"); stufe = g === "2" ? 2 : (g === "1" || g === "an") ? 1 : 0; } catch (e) { }
  var q = /[?&]matrix=([012])/.exec(location.search); if (q) stufe = +q[1];
  an = stufe > 0;
  var ruhe = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var zu = function (n) { return GL.charAt(Math.floor(Math.random() * GL.length)); };
  var cv = null, cx = null, timer = null, spalten = [], sichtbar = true, flimmer = null, titel = null, io = null;

  /* Überschrift: entschlüsselt sich von links nach rechts, danach selten ein kurzes Flimmern einzelner Zeichen (kein Blitzen der Fläche). */
  function textknoten() {
    var h = document.querySelector("main h1"), w = [], n;
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
    var t = textknoten(); if (!t.length) return; titel = t;
    var t0 = Date.now(), tick = setInterval(function () {
      var z = Math.floor((Date.now() - t0) / 22);
      if (z >= 70 || !an) { clearInterval(tick); zurueck(t); return; }
      mische(t, z, 0);
    }, 40);
  }
  function glitchPlanen() {
    clearTimeout(flimmer);
    if (!an || ruhe) return;
    flimmer = setTimeout(function () {
      if (an && !document.hidden) {
        var t = textknoten(); mische(t, null, 3);
        setTimeout(function () { zurueck(t); }, 160);
      }
      glitchPlanen();
    }, stufe === 2 ? 8000 + Math.random() * 10000 : 20000 + Math.random() * 25000);
  }

  /* Regen: dünn, blass, nur im Kopfbereich oben. Farbe folgt --green (im Alarm-Modus rot). */
  function abstand() { return stufe === 2 ? 12 : 18; }
  function groesse() {
    var m = cv.parentNode, w = m.clientWidth, h = m.clientHeight, i;
    cv.width = w; cv.height = h; cx.font = "13px ui-monospace,Menlo,Consolas,monospace";
    spalten = []; for (i = 0; i < Math.ceil(w / abstand()); i++) spalten.push(Math.random() * -20);
  }
  function zeichne() {
    if (!sichtbar || document.hidden) return;
    var h = cv.height, farbe = getComputedStyle(R).getPropertyValue("--green").trim() || "#6fe0a0";
    cx.globalCompositeOperation = "destination-out"; cx.fillStyle = "rgba(0,0,0,.16)"; cx.fillRect(0, 0, cv.width, h);
    cx.globalCompositeOperation = "source-over"; cx.fillStyle = farbe;
    for (var i = 0; i < spalten.length; i++) {
      cx.fillText(zu(), i * abstand() + 2, spalten[i] * 15);
      if (spalten[i] * 15 > h && Math.random() > .96) spalten[i] = Math.random() * -8; else spalten[i] += stufe === 2 ? .8 : .5;
    }
  }
  function regenAn() {
    var m = document.querySelector("header.marke, header.kopf"); if (!m || ruhe) return;
    if (!cv) {
      cv = document.createElement("canvas"); cv.className = "matrix-regen"; cv.setAttribute("aria-hidden", "true");
      m.insertBefore(cv, m.firstChild); cx = cv.getContext("2d");
      if (window.IntersectionObserver) { io = new IntersectionObserver(function (es) { sichtbar = es[0].isIntersecting; }); io.observe(m); }
      window.addEventListener("resize", function () { if (cv) groesse(); });
    }
    groesse(); clearInterval(timer); timer = setInterval(zeichne, stufe === 2 ? 55 : 70);
  }
  function regenAus() { clearInterval(timer); timer = null; if (cv) { cx.clearRect(0, 0, cv.width, cv.height); } }

  function setze(neu, speichern) {
    stufe = neu; an = neu > 0; R.classList.toggle("matrix", an); R.classList.toggle("matrix2", neu === 2);
    if (speichern) { try { localStorage.setItem("matrix", an ? String(neu) : "aus"); } catch (e) { } }
    if (an) { regenAn(); glitchPlanen(); } else { regenAus(); clearTimeout(flimmer); if (titel) zurueck(titel); }
    var b = document.getElementById("matrix-knopf");
    if (b) {
      var de = (R.lang || "de") === "de";
      b.setAttribute("aria-pressed", an ? "true" : "false");
      b.textContent = "MATRIX " + (neu === 2 ? "■■" : an ? "■" : "□");
      b.setAttribute("aria-label", (de ? "Matrix-Optik umschalten, Stufe " : "Toggle Matrix look, level ") + neu);
    }
  }
  document.addEventListener("DOMContentLoaded", function () {
    var m = document.getElementById("modus");
    if (m) {   /* Schalter nur auf der Startseite */
      var b = document.createElement("button");
      b.type = "button"; b.id = "matrix-knopf"; b.className = "spr mono";
      m.parentNode.insertBefore(b, m.nextSibling);
      b.addEventListener("click", function () { var n = (stufe + 1) % 3; setze(n, true); if (n === 1) entschluesseln(); });
    }
    setze(stufe, false); if (an) entschluesseln();
  });
})();
