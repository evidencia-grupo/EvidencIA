// Gera os ícones PNG da extensão a partir de assets/logo-icon.svg (fonte única).
// Uso: node scripts/generate-icons.mjs
// Regra da Chrome Web Store: no ícone de 128 px a arte ocupa 96x96 com 16 px de margem transparente.
import { chromium } from "@playwright/test";
import { mkdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const svg = readFileSync(resolve(root, "assets/logo-icon.svg"), "utf8");
const outDir = resolve(root, "public/icons");
mkdirSync(outDir, { recursive: true });

// tamanho final -> lado da arte (o restante é margem transparente)
const sizes = { 16: 16, 32: 32, 48: 48, 128: 96 };

const browser = await chromium.launch();
try {
  for (const [size, art] of Object.entries(sizes).map(([s, a]) => [Number(s), a])) {
    const page = await browser.newPage({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
    const pad = (size - art) / 2;
    await page.setContent(
      `<html><body style="margin:0;background:transparent">` +
        `<div style="width:${size}px;height:${size}px;padding:${pad}px;box-sizing:border-box">` +
        svg.replace(/width="80" height="80"/, `width="${art}" height="${art}"`) +
        `</div></body></html>`,
    );
    await page.screenshot({ path: resolve(outDir, `icon-${size}.png`), omitBackground: true });
    await page.close();
    console.log(`public/icons/icon-${size}.png`);
  }
} finally {
  await browser.close();
}
