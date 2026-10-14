// Gera as imagens da listagem da Chrome Web Store (1280x800 e tile 440x280) com a extensão real
// carregada de dist/. A página de vídeo é simulada localmente; o resultado vem do cache local
// (nenhuma chamada de rede). A fonte exibida é real e foi conferida em 14/10/2026:
// https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dengue
// Uso: npm run build && node scripts/store-screenshots.mjs
import { chromium } from "@playwright/test";
import { mkdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const out = resolve(root, "store");
mkdirSync(out, { recursive: true });

const catalog = JSON.parse(
  readFileSync(resolve(root, "../shared/reflection-catalog.ts"), "utf8").match(/REFLECTION_QUESTIONS = (\[.*\]) as const;/s)[1],
);
const videoId = "demo-listing";
const published = "2026-03-10T00:00:00Z";
const entry = {
  analysisMode: "evidence_first",
  videoId,
  videoTitle: "Vacinação contra a dengue: o que mudou no SUS",
  channelName: "Canal de exemplo",
  publishedAt: published,
  processingTimeMs: 2400,
  limitations: [],
  claims: [
    {
      id: "clm-01",
      text: "A vacina contra a dengue foi incorporada ao SUS em dezembro de 2023.",
      uncertainty: "contextualized",
      temporalContext: { videoPublishedAt: published, note: "As alegações foram apresentadas em 2026; confira se houve mudanças depois." },
      evidence: [
        {
          sourceId: "gov-saude-dengue",
          relation: "contextualizes",
          title: "Dengue — Ministério da Saúde",
          url: "https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/d/dengue",
          publisher: "Ministério da Saúde",
          publishedAt: "",
          snippet: "Em 21 de dezembro de 2023, a vacina contra dengue foi incorporada no Sistema Único de Saúde (SUS).",
          provenance: { dataset: "Exemplo ilustrativo", indexedAt: "2026-10-14T00:00:00Z" },
        },
      ],
      reflectionQuestions: catalog.slice(0, 3),
    },
    {
      id: "clm-02",
      text: "Uma única dose da vacina garante proteção para toda a vida.",
      uncertainty: "insufficient_evidence",
      temporalContext: { videoPublishedAt: published },
      evidence: [],
      reflectionQuestions: catalog.slice(3, 6),
    },
  ],
  cacheVersion: 3,
  timestamp: Date.now() - 60_000,
  ttl: 86_400_000,
};

const videoPage = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>${entry.videoTitle}</title>
<style>body{margin:0;background:#0f0f0f;color:#f1f1f1;font-family:Roboto,Arial,sans-serif}main{max-width:820px;padding:24px 32px}
#movie_player{aspect-ratio:16/9;background:linear-gradient(135deg,#222,#3a3a3a);border-radius:12px;display:grid;place-items:center;color:#aaa;font-size:20px}
h1{font-size:20px;margin:16px 0 4px}#channel-name{color:#aaa;font-size:14px}</style></head>
<body><main><div id="movie_player">Vídeo de exemplo</div><video hidden></video>
<h1 class="ytd-watch-metadata">${entry.videoTitle}</h1><div id="channel-name">${entry.channelName}</div><div id="above-the-fold"></div></main>
<script>window.ytInitialPlayerResponse={videoDetails:{videoId:"${videoId}",title:${JSON.stringify(entry.videoTitle)},author:${JSON.stringify(entry.channelName)}},
captions:{playerCaptionsTracklistRenderer:{captionTracks:[{baseUrl:"https://www.youtube.com/api/timedtext?v=${videoId}",languageCode:"pt"}]}}};</script></body></html>`;

const dist = resolve(root, "dist");
const context = await chromium.launchPersistentContext("", {
  channel: "chromium",
  headless: true,
  viewport: { width: 1280, height: 800 },
  args: [`--disable-extensions-except=${dist}`, `--load-extension=${dist}`],
});
try {
  const worker = context.serviceWorkers()[0] ?? (await context.waitForEvent("serviceworker"));
  await worker.evaluate(async (data) => chrome.storage.local.set({ [data.videoId]: data }), entry);
  await context.route("https://www.youtube.com/**", (route) => route.fulfill({ contentType: "text/html", body: videoPage }));

  const page = await context.newPage();
  await page.goto(`https://www.youtube.com/watch?v=${videoId}`);
  const button = page.getByRole("button", { name: "Checar Alegações" });
  await button.waitFor();
  await page.screenshot({ path: resolve(out, "screenshot-1-botao.png") });

  await button.click();
  const panel = page.frameLocator("#evidencia-side-panel");
  await panel.getByText(entry.claims[0].text).first().waitFor();
  await page.waitForTimeout(400);
  await page.screenshot({ path: resolve(out, "screenshot-2-alegacoes.png") });

  await panel.getByRole("button", { name: new RegExp(entry.claims[0].text.slice(0, 30)) }).first().click();
  await panel.getByText("Dengue — Ministério da Saúde").first().waitFor();
  await page.waitForTimeout(400);
  await page.screenshot({ path: resolve(out, "screenshot-3-evidencias.png") });

  const svg = readFileSync(resolve(root, "assets/logo-icon.svg"), "utf8").replace(/width="80" height="80"/, 'width="112" height="112"');
  const tile = await context.newPage();
  await tile.setViewportSize({ width: 440, height: 280 });
  await tile.setContent(`<html><body style="margin:0;width:440px;height:280px;background:linear-gradient(135deg,#1b1b1b,#2b2b2b);
    display:flex;align-items:center;gap:20px;padding:0 32px;box-sizing:border-box;font-family:Arial,sans-serif;color:#fff">${svg}
    <div><div style="font-size:34px;font-weight:700">EvidencIA</div>
    <div style="font-size:16px;color:#ddd;margin-top:8px;line-height:1.35">Alegações de vídeos do YouTube<br>com evidências e perguntas para refletir</div></div></body></html>`);
  await tile.screenshot({ path: resolve(out, "promo-tile-440x280.png") });
  console.log("store/: screenshot-1-botao.png, screenshot-2-alegacoes.png, screenshot-3-evidencias.png, promo-tile-440x280.png");
} finally {
  await context.close();
}
