(function () {
  "use strict";
  /* Alarm-Modus mit zwei Stufen: 1 = bisheriger Alarm, 2 = kräftiger auf der ganzen Seite.
     Gespeichert: "alarm" (Stufe 1, wie bisher), "alarm2" (Stufe 2), sonst "normal". */
  var R = document.documentElement, stufe = 0;
  try { var v = localStorage.getItem("modus"); stufe = v === "alarm2" ? 2 : v === "alarm" ? 1 : 0; } catch (e) { }
  if (stufe > 0) R.classList.add("alarm");
  if (stufe === 2) R.classList.add("alarm2");
  document.addEventListener("DOMContentLoaded", function () {
    var b = document.getElementById("modus");
    if (!b) return;
    var b2 = document.createElement("button");
    b2.type = "button"; b2.id = "modus2"; b2.className = "spr mono";
    b.parentNode.insertBefore(b2, b.nextSibling);
    var de = (R.lang || "de") === "de";
    var set = function (s, speichern) {
      stufe = s;
      R.classList.toggle("alarm", s > 0); R.classList.toggle("alarm2", s === 2);
      b.setAttribute("aria-pressed", s > 0 ? "true" : "false");
      b.textContent = (de ? "ALARM " : "ALERT ") + (s > 0 ? "■" : "□");
      b.setAttribute("aria-label", de ? "Alarm-Modus umschalten" : "Toggle alert mode");
      b2.setAttribute("aria-pressed", s === 2 ? "true" : "false");
      b2.textContent = s === 2 ? "■" : "□";
      b2.setAttribute("aria-label", de ? "Alarm kräftiger, ganze Seite" : "Alert stronger, whole page");
      if (speichern) { try { localStorage.setItem("modus", s === 2 ? "alarm2" : s === 1 ? "alarm" : "normal"); } catch (e) { } }
    };
    b.addEventListener("click", function () { set(stufe === 0 ? 1 : 0, true); });
    b2.addEventListener("click", function () { set(stufe === 2 ? 1 : 2, true); });
    set(stufe, false);
  });
})();
