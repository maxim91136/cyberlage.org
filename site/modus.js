(function () {
  "use strict";
  var an = false;
  try { an = localStorage.getItem("modus") === "alarm"; } catch (e) { }
  if (an) document.documentElement.classList.add("alarm");
  document.addEventListener("DOMContentLoaded", function () {
    var b = document.getElementById("modus");
    if (!b) return;
    var de = (document.documentElement.lang || "de") === "de";
    var set = function () {
      var on = document.documentElement.classList.contains("alarm");
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.textContent = (de ? "ALARM " : "ALERT ") + (on ? "■" : "□");
      b.setAttribute("aria-label", de ? "Alarm-Modus umschalten" : "Toggle alert mode");
    };
    b.addEventListener("click", function () {
      var on = document.documentElement.classList.toggle("alarm");
      try { localStorage.setItem("modus", on ? "alarm" : "normal"); } catch (e) { }
      set();
    });
    set();
  });
})();
