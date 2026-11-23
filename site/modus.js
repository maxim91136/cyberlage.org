(function () {
  "use strict";
  var an = false;
  try { an = localStorage.getItem("modus") === "krieg"; } catch (e) { }
  if (an) document.documentElement.classList.add("krieg");
  document.addEventListener("DOMContentLoaded", function () {
    var b = document.getElementById("modus");
    if (!b) return;
    var de = (document.documentElement.lang || "de") === "de";
    var set = function () {
      var on = document.documentElement.classList.contains("krieg");
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.textContent = on ? "WAR ■" : "WAR □";
      b.setAttribute("aria-label", de ? "Cyberwar-Modus umschalten" : "Toggle cyberwar mode");
    };
    b.addEventListener("click", function () {
      var on = document.documentElement.classList.toggle("krieg");
      try { localStorage.setItem("modus", on ? "krieg" : "normal"); } catch (e) { }
      set();
    });
    set();
  });
})();
