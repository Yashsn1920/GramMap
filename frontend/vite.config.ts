import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In Docker the backend and tile server are reached by service name; locally on localhost.
const api = process.env.VITE_API_PROXY ?? "http://localhost:8000";
const tiles = process.env.VITE_TILES_PROXY ?? "http://localhost:3000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": api,
      "/tiles": { target: tiles, rewrite: (p) => p.replace(/^\/tiles/, "") },
    },
  },
});
