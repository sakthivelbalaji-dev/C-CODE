/**
 * Cross-browser production build: legacy chunks + polyfills for older Safari/Chrome/Firefox/iOS.
 *
 * Install peer deps in frontend/:
 *   npm i -D @vitejs/plugin-legacy terser
 * (Also: @vitejs/plugin-react, vite — per your app version.)
 *
 * If you already have a vite.config, merge the `legacy` plugin and `build.cssTarget`/`build.target`.
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import legacy from "@vitejs/plugin-legacy";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    legacy({
      targets: [
        "Chrome >= 73",
        "Edge >= 79",
        "Safari >= 12.1",
        "Firefox >= 67",
        "iOS >= 12",
      ],
      modernPolyfills: true,
      polyfills: true,
      renderLegacyChunks: true,
    }),
  ],
  build: {
    outDir: path.resolve(__dirname, "../backend/dist"),
    emptyOutDir: true,
    target: "baseline-widely-available",
    cssTarget: ["chrome80", "safari14", "firefox78"],
    chunkSizeWarningLimit: 1200,
  },
});
