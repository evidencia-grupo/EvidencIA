import { test as base, expect, chromium, type BrowserContext, type Worker } from "@playwright/test";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const test = base.extend<{ extension: { context: BrowserContext; worker: Worker } }>({
  extension: async ({}, use) => {
    const path = resolve("dist");
    const context = await chromium.launchPersistentContext("", {
      channel: "chromium",
      headless: true,
      args: [`--disable-extensions-except=${path}`, `--load-extension=${path}`],
    });
    let worker = context.serviceWorkers()[0];
    if (!worker) {
      let interval: NodeJS.Timeout | undefined;
      const pollPromise = new Promise<Worker>((res) => {
        interval = setInterval(() => {
          const sw = context.serviceWorkers()[0];
          if (sw) {
            clearInterval(interval);
            res(sw);
          }
        }, 50);
      });
      worker = await Promise.race([context.waitForEvent("serviceworker"), pollPromise]);
      if (interval) clearInterval(interval);
    }
    await use({ context, worker });
    await context.close();
  },
});

async function setup(context: BrowserContext, id = "video", captions = true, failCaptions = false) {
  let captionCalls = 0;
  await context.route("https://www.youtube.com/**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/api/timedtext") {
      captionCalls++;
      if (failCaptions) {
        await route.fulfill({ status: 503, body: "Service Unavailable" });
        return;
      }
      await route.fulfill({
        contentType: "text/xml",
        body: `<transcript><text>Um estudo apresenta dados sobre a relacao entre exercicio fisico e qualidade de vida.</text></transcript>`,
      });
    } else {
      await route.fulfill({
        contentType: "text/html",
        body: `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Vídeo de teste - Ausência de legendas</title></head><body>
        <main><h1 class="ytd-watch-metadata">Vídeo Teste</h1><div id="channel-name">Canal de testes</div><div id="above-the-fold"></div><div id="movie_player"></div><video></video><a href="#footer">Próximo</a></main>
        <script>
        window.ytInitialPlayerResponse = {
          videoDetails: { videoId: new URLSearchParams(location.search).get('v') },
          captions: {
            playerCaptionsTracklistRenderer: {
              captionTracks: ${captions ? JSON.stringify([{ baseUrl: "https://www.youtube.com/api/timedtext?v=" + id, languageCode: "pt" }]) : "[]"}
            }
          }
        };
        window.__evidencia_perf__ = { click: 0, alertTime: null, blocking: 0 };
        new PerformanceObserver(list => {
          for (const entry of list.getEntries()) window.__evidencia_perf__.blocking += Math.max(0, entry.duration - 50);
        }).observe({ type: 'longtask', buffered: true });
        document.addEventListener('click', () => {
          window.__evidencia_perf__.click = performance.timeOrigin + performance.now();
        }, true);
        </script></body></html>`,
      });
    }
  });

  const page = await context.newPage();
  await page.goto(`https://www.youtube.com/watch?v=${id}`);
  const button = page.getByRole("button", { name: "Checar Alegações" });
  await expect(button).toBeVisible();
  const panel = page.frameLocator("#evidencia-side-panel");
  await expect(panel.getByRole("button", { name: /Fechar painel/, includeHidden: true })).toBeAttached();
  return { page, button, panel, captionCalls: () => captionCalls, recover: () => { failCaptions = false; } };
}

test("Ausência de legendas: Cenário 1 — Vídeo sem legendas notifica em até 1s e encerra com segurança sem bloquear a aba", async ({ extension }) => {
  const { page, button, panel, captionCalls } = await setup(extension.context, "no-captions-video", false);

  // Monitora reprodução do vídeo e tarefas longas
  await page.evaluate(() => {
    (window as any).pauses = 0;
    document.querySelector("video")!.pause = () => {
      (window as any).pauses++;
    };
  });

  const panelFrame = await page.locator("#evidencia-side-panel").elementHandle().then(handle => handle!.contentFrame());
  await panelFrame!.evaluate(() => {
    new MutationObserver(() => {
      if (document.querySelector('[role="alert"]')) (window as any).alertTime ??= performance.timeOrigin + performance.now();
    }).observe(document.body, { childList: true, subtree: true });
  });
  await button.click();

  // Alerta deve ser exibido com role="alert" informando a impossibilidade técnica
  const alert = panel.getByRole("alert");
  await expect(alert).toContainText("Este vídeo não tem legendas");
  await expect(alert).toContainText("Sem as legendas não conseguimos analisar");

  const alertTime = await panelFrame!.evaluate(() => (window as any).alertTime);
  const clickTime = await page.evaluate(() => (window as any).__evidencia_perf__.click);
  expect(alertTime - clickTime).toBeLessThanOrEqual(1000);

  // Player não deve ter sido pausado nem a aba bloqueada
  expect(await page.evaluate(() => (window as any).pauses)).toBe(0);
  const blocking = await page.evaluate(() => (window as any).__evidencia_perf__.blocking);
  expect(blocking).toBeLessThanOrEqual(50);

  // Nenhuma chamada externa a timedtext
  expect(captionCalls()).toBe(0);

  // Botão no player informa o status e permite nova tentativa
  await expect(page.getByRole("button", { name: /Sem legendas/ })).toBeEnabled();

  // Botão de nova tentativa também acessível no painel
  await expect(panel.getByRole("button", { name: "Tentar novamente" })).toBeVisible();

  // Validação de acessibilidade WCAG no painel com o alerta ativo

  if (panelFrame) {
    await panelFrame.evaluate(readFileSync(resolve("node_modules/axe-core/axe.min.js"), "utf8"));
    const axeResults = await panelFrame.evaluate(() => (window as any).axe.run(document));
    expect(axeResults.violations).toEqual([]);
  }
});

test("Ausência de legendas: Cenário 2 — Falha temporária da API do YouTube exibe botão de nova tentativa no painel", async ({ extension }) => {
  const { button, panel, recover } = await setup(extension.context, "temp-fail-video", true, true);
  await button.click();

  // Painel deve exibir o alerta com o erro e o botão de nova tentativa
  const alert = panel.getByRole("alert");
  await expect(alert).toContainText("Não conseguimos checar este vídeo agora");
  const retryBtn = panel.getByRole("button", { name: "Tentar novamente" });
  await expect(retryBtn).toBeVisible();

  recover();

  // Aciona nova tentativa pelo botão dentro do painel
  await retryBtn.click();

  // Verifica que o painel volta ao estado de carregamento e processa com sucesso
  await expect(panel.getByRole("heading", { name: /Alegações Analisadas/ })).toBeVisible({ timeout: 10000 });
});
