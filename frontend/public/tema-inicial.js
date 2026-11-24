// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// FE-30 R5: fija el tema guardado en <html> antes de pintar. Solo lee jubys-audit-storage; no escribe nada.
(function () {
  var tema = "light";
  try {
    var guardado = JSON.parse(window.localStorage.getItem("jubys-audit-storage") || "null");
    if (guardado && guardado.state && guardado.state.theme === "dark") tema = "dark";
  } catch (e) {
    tema = "light";
  }
  var clases = document.documentElement.classList;
  clases.remove("dark", "theme-dark", "theme-light");
  if (tema === "dark") clases.add("dark", "theme-dark");
  else clases.add("theme-light");
})();
