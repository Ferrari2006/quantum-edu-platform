import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function gameDirectoryIndex() {
  const serveIndex = (server) => {
    server.middlewares.use((req, _res, next) => {
      const [pathname, query] = (req.url || "").split("?");
      const game = ["xiaohei", "quantum-orb"].find(
        (name) => pathname === `/games/${name}` || pathname === `/games/${name}/`
      );
      if (game) {
        req.url = `/games/${game}/index.html${query ? `?${query}` : ""}`;
      }
      next();
    });
  };
  return {
    name: "game-directory-index",
    configureServer: serveIndex,
    configurePreviewServer: serveIndex,
  };
}

export default defineConfig({
  plugins: [react(), gameDirectoryIndex()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/docs": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000"
    }
  }
});
