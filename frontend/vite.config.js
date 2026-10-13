import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function xiaoheiDirectoryIndex() {
  const serveIndex = (server) => {
    server.middlewares.use((req, _res, next) => {
      const [pathname, query] = (req.url || "").split("?");
      if (pathname === "/games/xiaohei" || pathname === "/games/xiaohei/") {
        req.url = `/games/xiaohei/index.html${query ? `?${query}` : ""}`;
      }
      next();
    });
  };
  return {
    name: "xiaohei-directory-index",
    configureServer: serveIndex,
    configurePreviewServer: serveIndex,
  };
}

export default defineConfig({
  plugins: [react(), xiaoheiDirectoryIndex()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/docs": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000"
    }
  }
});
