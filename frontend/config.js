/* CAM-CHILE — Frontend config
 *
 * Lee API_BASE y ALLOWED_HOSTS desde <meta>. Si no existen, usa defaults seguros.
 * Nunca harcodear URLs de producción en este archivo.
 */
(function () {
  "use strict";

  function meta(name, fallback) {
    const el = document.querySelector(`meta[name="${name}"]`);
    if (!el) return fallback;
    const v = (el.getAttribute("content") || "").trim();
    return v || fallback;
  }

  function csv(s) {
    return (s || "")
      .split(",")
      .map((x) => x.trim().toLowerCase())
      .filter(Boolean);
  }

  window.CAMCHILE_CONFIG = Object.freeze({
    apiBase: meta("api-base", "http://localhost:8000"),
    allowedHosts: csv(
      meta(
        "allowed-hosts",
        "youtube.com,youtu.be,youtube-nocookie.com,webcams.travel,skylinewebcams.com"
      )
    ),
  });
})();