import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = resolve(__dirname, "..");
const manifest = JSON.parse(readFileSync(resolve(root, "manifest.json"), "utf8"));

describe("manifest pronto para a Chrome Web Store", () => {
  it("respeita os limites de nome, descrição e versão", () => {
    expect(manifest.manifest_version).toBe(3);
    expect(manifest.name.length).toBeLessThanOrEqual(75);
    expect(manifest.description.length).toBeLessThanOrEqual(132);
    expect(manifest.version).toMatch(/^\d+(\.\d+){0,3}$/);
  });

  it("declara ícones 16/32/48/128 que existem em public/", () => {
    for (const size of ["16", "32", "48", "128"]) {
      expect(manifest.icons[size]).toBe(`icons/icon-${size}.png`);
      expect(existsSync(resolve(root, "public", manifest.icons[size]))).toBe(true);
    }
    for (const icon of Object.values(manifest.action.default_icon) as string[]) {
      expect(existsSync(resolve(root, "public", icon))).toBe(true);
    }
  });

  it("pede apenas permissões usadas e justificadas na listagem", () => {
    expect(manifest.permissions).toEqual(["storage", "scripting"]);
    expect(manifest.host_permissions).not.toContain("<all_urls>");
    expect(manifest.content_scripts[0].matches).toEqual(["https://www.youtube.com/*"]);
  });
});
