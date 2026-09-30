/* CAM-CHILE — Reproductor por proveedor
 *
 * Devuelve el HTML del popup para una cámara según su stream_type.
 * Nunca inyecta recursos desde hosts fuera de allowedHosts (config.js).
 */
(function () {
  "use strict";

  function safeUrl(url) {
    const cfg = window.CAMCHILE_CONFIG;
    try {
      const host = new URL(url).hostname.toLowerCase();
      const ok = cfg.allowedHosts.some((h) => host === h || host.endsWith("." + h));
      return ok ? url : null;
    } catch {
      return null;
    }
  }

  function youtubeEmbed(videoUrl) {
    let id = null;
    try {
      const u = new URL(videoUrl);
      if (u.hostname.endsWith("youtu.be")) {
        id = u.pathname.replace(/^\//, "");
      } else if (u.hostname.endsWith("youtube.com")) {
        id = u.searchParams.get("v");
      } else if (u.hostname.endsWith("youtube-nocookie.com")) {
        id = u.pathname.split("/").pop();
      }
    } catch {
      /* noop */
    }
    if (!id) return "<p>URL de YouTube no válida.</p>";
    return (
      `<iframe width="320" height="180" ` +
      `src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}" ` +
      `title="Stream de YouTube" frameborder="0" allow="autoplay; encrypted-media" ` +
      `referrerpolicy="strict-origin-when-cross-origin" loading="lazy"></iframe>`
    );
  }

  function popupHTML(cam) {
    const safe = safeUrl(cam.stream_url);
    const lines = [
      `<strong>${escapeHTML(cam.name)}</strong>`,
      `<small>${escapeHTML(cam.city || "")}${cam.region ? ", " + escapeHTML(cam.region) : ""}</small>`,
      `<small>Fuente: ${escapeHTML(cam.source_name || "")} · Estado: <code>${escapeHTML(cam.public_status)}</code></small>`,
    ];

    if (!safe) {
      lines.push('<p><em>Stream no permitido por la allowlist.</em></p>');
    } else if (cam.stream_type === "youtube" || cam.stream_type === "youtube_embed") {
      lines.push(youtubeEmbed(safe));
    } else if (cam.stream_type === "hls") {
      lines.push(
        `<video width="320" height="180" controls preload="none" src="${escapeAttr(safe)}"></video>`
      );
    } else if (cam.stream_type === "mp4") {
      lines.push(
        `<video width="320" height="180" controls preload="none" src="${escapeAttr(safe)}"></video>`
      );
    } else if (cam.stream_type === "iframe") {
      lines.push(
        `<iframe width="320" height="180" src="${escapeAttr(safe)}" frameborder="0" loading="lazy"></iframe>`
      );
    }

    if (cam.license_or_terms_url) {
      lines.push(
        `<small><a href="${escapeAttr(cam.license_or_terms_url)}" target="_blank" rel="noopener noreferrer">Licencia / términos</a></small>`
      );
    }

    return lines.join("<br>");
  }

  function escapeHTML(s) {
    return String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }
  function escapeAttr(s) {
    return escapeHTML(s);
  }

  window.CAMCHILE_PLAYER = { popupHTML };
})();