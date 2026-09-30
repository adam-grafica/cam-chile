/* CAM-CHILE — Mapa (Leaflet)
 *
 * Inicializa el mapa centrado en Chile, carga cámaras vía API y dibuja
 * marcadores accesibles. El popup del reproductor lo construye player.js.
 */
(function () {
  "use strict";

  const cfg = window.CAMCHILE_CONFIG;
  if (!cfg) {
    console.error("config.js no cargado");
    return;
  }

  const state = {
    map: null,
    cameras: [],
    markers: [],
    filters: { region: "", source_name: "", public_status: "" },
  };

  const cameraIcon = L.divIcon({
    html: "📹",
    className: "camera-marker",
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });

  function isHostAllowed(url) {
    try {
      const host = new URL(url).hostname.toLowerCase();
      return cfg.allowedHosts.some(
        (h) => host === h || host.endsWith("." + h)
      );
    } catch {
      return false;
    }
  }

  async function loadCameras() {
    const url = cfg.apiBase.replace(/\/$/, "") + "/api/cameras";
    try {
      const resp = await fetch(url, { credentials: "omit" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const cameras = await resp.json();
      state.cameras = cameras;
      renderAll();
      populateFilters();
      setStatus(`${cameras.length} cámaras cargadas`);
    } catch (e) {
      console.error("Error cargando cámaras:", e);
      setStatus("Error cargando catálogo", true);
      document.getElementById("count").textContent = "—";
    }
  }

  function renderAll() {
    state.markers.forEach((m) => state.map.removeLayer(m));
    state.markers = [];

    const filtered = state.cameras.filter((c) => {
      if (state.filters.region && c.region !== state.filters.region) return false;
      if (state.filters.source_name && c.source_name !== state.filters.source_name) return false;
      if (
        state.filters.public_status &&
        c.public_status !== state.filters.public_status
      )
        return false;
      return c.latitude != null && c.longitude != null;
    });

    document.getElementById("count").textContent = filtered.length;

    for (const cam of filtered) {
      const marker = L.marker([cam.latitude, cam.longitude], { icon: cameraIcon }).addTo(
        state.map
      );
      marker.bindPopup(() => window.CAMCHILE_PLAYER.popupHTML(cam), {
        maxWidth: 360,
      });
      state.markers.push(marker);
    }
  }

  function populateFilters() {
    const regions = [...new Set(state.cameras.map((c) => c.region).filter(Boolean))].sort();
    const sources = [...new Set(state.cameras.map((c) => c.source_name).filter(Boolean))].sort();
    fillSelect("filter-region", regions);
    fillSelect("filter-source", sources);
  }

  function fillSelect(id, values) {
    const sel = document.getElementById(id);
    const first = sel.firstElementChild.cloneNode(true);
    sel.innerHTML = "";
    sel.appendChild(first);
    for (const v of values) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      sel.appendChild(opt);
    }
  }

  function setStatus(text, isError) {
    const el = document.getElementById("status-line");
    el.textContent = text;
    el.classList.toggle("error", !!isError);
  }

  function bindFilters() {
    ["region", "source_name", "public_status"].forEach((key) => {
      const id = key === "region" ? "filter-region" : key === "source_name" ? "filter-source" : "filter-status";
      const el = document.getElementById(id);
      el.addEventListener("change", () => {
        state.filters[key] = el.value;
        renderAll();
      });
    });
  }

  function init() {
    state.map = L.map("map").setView([-35.6751, -71.543], 6);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
      maxZoom: 18,
    }).addTo(state.map);
    bindFilters();
    loadCameras();
    // Expone para tests de Playwright
    window.CAMCHILE_STATE = state;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();