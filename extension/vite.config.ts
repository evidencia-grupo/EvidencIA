import { defineConfig, loadEnv } from "vite";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import preact from "@preact/preset-vite";
import { resolve } from "path";

const configDir = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const raw = process.env.VITE_API_BASE_URL || env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  const backend = new URL(raw);
  if (backend.username || backend.password || !["http:", "https:"].includes(backend.protocol)
    || (mode === "production" && (backend.protocol !== "https:" || !process.env.VITE_API_BASE_URL && !env.VITE_API_BASE_URL))) {
    throw new Error("Build de produção exige VITE_API_BASE_URL HTTPS explícita, sem credenciais.");
  }
  const manifest = JSON.parse(readFileSync(resolve(configDir, "manifest.json"), "utf8"));
  manifest.host_permissions = ["https://www.youtube.com/*", `${backend.origin}/*`];
  return {
  plugins: [preact(), {
    name: "explicit-backend-permissions",
    generateBundle() { this.emitFile({ type: "asset", fileName: "manifest.json", source: JSON.stringify(manifest, null, 2) }); },
  }],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        panel: resolve(configDir, "src/panel/index.html"),
        background: resolve(configDir, "src/background/service-worker.ts"),
        content: resolve(configDir, "src/content/content-script.ts"),
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === "background") return "background.js";
          if (chunkInfo.name === "content") return "content.js";
          return "assets/[name]-[hash].js";
        },
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]",
      },
    },
  },
  resolve: {
    alias: {
      "@shared": resolve(configDir, "../shared"),
    },
  },
  };
});
