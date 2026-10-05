import { defineConfig } from "vitest/config";
import preact from "@preact/preset-vite";
export default defineConfig({
  plugins: [preact()],
  test: {
    include: ["src/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts", "src/**/*.tsx"],
      exclude: ["src/**/*.test.*"],
      reporter: ["text", "json-summary", "html"],
      thresholds: { perFile: true, lines: 81, statements: 81, functions: 81, branches: 81 },
    },
  },
});
