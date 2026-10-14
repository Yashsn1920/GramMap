import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

// Pilot district (Bengaluru North), centred on Doddaballapura.
const PILOT_CENTER: [number, number] = [77.53, 13.29];

// Vector tiles from Martin, proxied by Vite at /tiles (see vite.config.ts).
const tiles = (table: string) => [`${window.location.origin}/tiles/${table}/{z}/{x}/{y}`];

const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      maxzoom: 19,
      attribution: "© OpenStreetMap contributors",
    },
    villages: {
      type: "vector",
      tiles: tiles("geo_village"),
      promoteId: { geo_village: "lgd_code" },
      attribution: "Boundaries: KSRSAC / KGIS",
    },
    districts: { type: "vector", tiles: tiles("geo_district") },
  },
  layers: [
    { id: "osm", type: "raster", source: "osm" },
    {
      id: "village-fill",
      type: "fill",
      source: "villages",
      "source-layer": "geo_village",
      filter: ["==", ["get", "is_pilot"], true],
      paint: {
        "fill-color": "#2563eb",
        "fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.35, 0.08],
      },
    },
    {
      id: "village-line",
      type: "line",
      source: "villages",
      "source-layer": "geo_village",
      filter: ["==", ["get", "is_pilot"], true],
      paint: { "line-color": "#1d4ed8", "line-width": ["interpolate", ["linear"], ["zoom"], 9, 0.3, 14, 1.5] },
    },
    {
      id: "district-line",
      type: "line",
      source: "districts",
      "source-layer": "geo_district",
      paint: { "line-color": "#b91c1c", "line-width": 2.5 },
    },
  ],
};

export default function BaseMap() {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: container.current!,
      style: STYLE,
      center: PILOT_CENTER,
      zoom: 9.5,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(new maplibregl.ScaleControl(), "bottom-left");

    // Hover highlight and a name label for villages.
    const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false });
    let hovered: string | number | undefined;
    map.on("mousemove", "village-fill", (e) => {
      const f = e.features?.[0];
      if (!f) return;
      if (hovered !== undefined) {
        map.setFeatureState({ source: "villages", sourceLayer: "geo_village", id: hovered }, { hover: false });
      }
      hovered = f.id;
      if (hovered !== undefined) {
        map.setFeatureState({ source: "villages", sourceLayer: "geo_village", id: hovered }, { hover: true });
      }
      map.getCanvas().style.cursor = "pointer";
      popup
        .setLngLat(e.lngLat)
        .setHTML(`<strong>${f.properties.name}</strong><br/>LGD ${f.properties.lgd_code}`)
        .addTo(map);
    });
    map.on("mouseleave", "village-fill", () => {
      if (hovered !== undefined) {
        map.setFeatureState({ source: "villages", sourceLayer: "geo_village", id: hovered }, { hover: false });
      }
      hovered = undefined;
      map.getCanvas().style.cursor = "";
      popup.remove();
    });
    return () => map.remove();
  }, []);

  return <div ref={container} className="map" data-testid="map" />;
}
