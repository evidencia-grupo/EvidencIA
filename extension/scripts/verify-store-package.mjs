// Valida o build de produção antes do envio à Chrome Web Store.
// Uso: node scripts/verify-store-package.mjs [diretório]   (padrão: dist)
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const dist = resolve(process.argv[2] ?? "dist");
const errors = [];
const fail = (message) => errors.push(message);

const manifestPath = join(dist, "manifest.json");
if (!existsSync(manifestPath)) {
  console.error(`manifest.json ausente em ${dist}; rode npm run build:prod.`);
  process.exit(1);
}
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));

if (manifest.manifest_version !== 3) fail("manifest_version deve ser 3.");
if (!/^\d+(\.\d+){0,3}$/.test(manifest.version ?? "")) fail(`version inválida: ${manifest.version}`);
if (!manifest.name || manifest.name.length > 75) fail("name ausente ou com mais de 75 caracteres.");
if (!manifest.description || manifest.description.length > 132) fail("description ausente ou com mais de 132 caracteres.");

for (const size of ["16", "32", "48", "128"]) {
  const icon = manifest.icons?.[size];
  if (!icon || !existsSync(join(dist, icon))) fail(`ícone ${size}px ausente no pacote.`);
}

const allowedPermissions = new Set(["storage", "scripting"]);
for (const permission of manifest.permissions ?? []) {
  if (!allowedPermissions.has(permission)) fail(`permissão não justificada na listagem: ${permission}`);
}

const hosts = manifest.host_permissions ?? [];
if (!hosts.includes("https://www.youtube.com/*")) fail("host_permissions deve incluir https://www.youtube.com/*.");
for (const host of hosts) {
  const origin = host.replace(/\/\*$/, "");
  let url;
  try {
    url = new URL(origin);
  } catch {
    fail(`host_permission inválida: ${host}`);
    continue;
  }
  if (url.protocol !== "https:") fail(`host_permission sem HTTPS: ${host}`);
  if (["localhost", "127.0.0.1", "[::1]"].includes(url.hostname)) fail(`host_permission local no pacote: ${host}`);
  if (url.hostname.includes("*") && host !== "https://www.youtube.com/*") fail(`host_permission com curinga: ${host}`);
}

for (const file of ["background.js", "content.js", "src/panel/index.html"]) {
  if (!existsSync(join(dist, file))) fail(`arquivo esperado ausente: ${file}`);
}

// Manifest V3 proíbe código remoto e avaliação dinâmica.
const walk = (dir) => readdirSync(dir).flatMap((name) => {
  const path = join(dir, name);
  return statSync(path).isDirectory() ? walk(path) : [path];
});
for (const file of walk(dist).filter((path) => path.endsWith(".js"))) {
  const code = readFileSync(file, "utf8");
  if (/\beval\s*\(|new Function\s*\(/.test(code)) fail(`avaliação dinâmica de código em ${file}`);
  if (/<script[^>]+src=["']https?:/i.test(code) || /importScripts\(\s*["']https?:/.test(code)) fail(`código remoto em ${file}`);
}

if (errors.length) {
  console.error("Pacote NÃO está pronto para a Chrome Web Store:");
  for (const error of errors) console.error(`  - ${error}`);
  process.exit(1);
}
console.log(`Pacote verificado: ${manifest.name} ${manifest.version}; hosts: ${hosts.join(", ")}`);
