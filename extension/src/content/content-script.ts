import { extractCaptionsFromPage } from "./caption-parser";
import type { AnalyzeRequest } from "../../../shared/types/api";

let currentVideoId: string | null = null;
let panelIframe: HTMLIFrameElement | null = null;
let badgeContainer: HTMLDivElement | null = null;
let generation = 0;
let panelReady = false;
let panelState: unknown = null;
let activeController: AbortController | null = null;
let injectionTimer: ReturnType<typeof setTimeout> | undefined;
const panelOrigin = chrome.runtime.getURL("").replace(/\/$/, "");

function publish(message: unknown) {
  panelState = message;
  if (panelReady) panelIframe?.contentWindow?.postMessage(message, panelOrigin);
}

function closePanel() {
  togglePanel(false);
  badgeContainer?.shadowRoot?.querySelector<HTMLButtonElement>("button")?.focus();
}

window.addEventListener("message", (event) => {
  if (event.source !== panelIframe?.contentWindow || event.origin !== panelOrigin) return;
  if (event.data?.type === "PANEL_READY") {
    panelReady = true;
    if (panelState) publish(panelState);
    if (panelIframe?.style.display === "block") panelIframe.contentWindow?.postMessage({ type: "FOCUS_PANEL" }, panelOrigin);
  } else if (event.data?.type === "CLOSE_PANEL") closePanel();
});
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && panelIframe?.style.display === "block") closePanel();
});

function getVideoIdFromUrl(): string | null {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("v");
}

function initSidePanel() {
  if (panelIframe?.isConnected) return;
  panelReady = false;

  panelIframe = document.createElement("iframe");
  panelIframe.title = "Checagem factual do vídeo";
  panelIframe.id = "evidencia-side-panel";
  panelIframe.src = chrome.runtime.getURL("src/panel/index.html");
  panelIframe.setAttribute("sandbox", "allow-scripts allow-same-origin");
  panelIframe.style.cssText = `
    position: fixed;
    top: 56px;
    right: 0;
    width: min(380px, 100vw);
    height: calc(100vh - 56px);
    border: none;
    border-left: 1px solid #3F3F3F;
    background: #1F1F1F;
    z-index: 2040;
    box-shadow: -4px 0 16px rgba(0, 0, 0, 0.5);
    display: none;
    transition: transform 0.3s ease-in-out;
  `;
  document.body.appendChild(panelIframe);
}

function togglePanel(visible: boolean) {
  if (visible) initSidePanel();
  if (panelIframe) {
    panelIframe.style.display = visible ? "block" : "none";
    if (visible && panelReady) {
      panelIframe.focus();
      panelIframe.contentWindow?.postMessage({ type: "FOCUS_PANEL" }, panelOrigin);
    }
    badgeContainer?.shadowRoot?.querySelector("button")?.setAttribute("aria-expanded", String(visible));
  }
}

function injectTriggerBadge() {
  if (location.pathname !== "/watch") return;
  const videoId = getVideoIdFromUrl();
  if (!videoId) return;
  if (videoId === currentVideoId && badgeContainer?.isConnected) return;

  currentVideoId = videoId;
  initSidePanel();

  // Encontra o container abaixo do título do vídeo do YouTube
  const targetArea =
    document.querySelector("#above-the-fold") ||
    document.querySelector("#top-row") ||
    document.querySelector("ytd-watch-metadata");

  if (!targetArea) {
    clearTimeout(injectionTimer);
    injectionTimer = setTimeout(injectTriggerBadge, 250);
    return;
  }

  // Remove container anterior se houver
  if (badgeContainer) {
    badgeContainer.remove();
  }

  // Cria elemento com Shadow DOM para total isolamento de CSS (RNF-02)
  badgeContainer = document.createElement("div");
  badgeContainer.id = "evidencia-badge-host";
  const shadowRoot = badgeContainer.attachShadow({ mode: "open" });

  const style = document.createElement("style");
  style.textContent = `
    .evidencia-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: #1F1F1F;
      color: #FFFFFF;
      border: 1px solid #3F3F3F;
      border-radius: 18px;
      padding: 6px 14px;
      font-family: Roboto, Arial, sans-serif;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      margin: 8px 0;
    }
    .evidencia-btn:hover {
      background: #272727;
      border-color: #2BA640;
    }
    .evidencia-btn:focus-visible { outline: 3px solid #FBC02D; outline-offset: 3px; }
    .evidencia-icon {
      width: 16px;
      height: 16px;
      fill: #2BA640;
    }
    .evidencia-loading {
      cursor: wait;
    }
  `;

  const button = document.createElement("button");
  button.className = "evidencia-btn";
  button.innerHTML = `
    <svg aria-hidden="true" class="evidencia-icon" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
    <span>Verificar Veracidade</span>
  `;

  // Impede que atalhos globais do player também consumam Enter/Espaço.
  for (const eventName of ["keydown", "keyup"]) {
    button.addEventListener(eventName, (event) => {
      if (["Enter", " "].includes((event as KeyboardEvent).key)) event.stopPropagation();
    });
  }
  button.type = "button";
  button.setAttribute("aria-expanded", "false");
  const status = document.createElement("span");
  status.setAttribute("role", "status");
  status.style.cssText = "position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)";
  shadowRoot.appendChild(status);
  button.addEventListener("click", async () => {
    if (button.getAttribute("aria-disabled") === "true") return;
    const run = ++generation;
    const controller = new AbortController();
    activeController = controller;
    const deadline = Date.now() + 9500;
    const active = () => run === generation && getVideoIdFromUrl() === videoId;
    button.setAttribute("aria-disabled", "true");
    button.classList.add("evidencia-loading");
    button.querySelector("span")!.textContent = "Analisando...";
    status.textContent = "Analisando vídeo";
    togglePanel(true);
    publish({ type: "ANALYSIS_START" });
    let timer: ReturnType<typeof setTimeout> | undefined;
    const checkActive = () => {
      if (!active()) throw new Error("Checagem encerrada. Tente novamente.");
      if (Date.now() >= deadline) throw new Error("Tempo limite de 10 segundos excedido. Tente novamente.");
    };
    try {
      const work = async () => {
        const cached = await chrome.runtime.sendMessage({ type: "GET_CACHE", videoId });
        checkActive();
        if (cached?.success && cached.data) return cached.data;
        const captions = await extractCaptionsFromPage(videoId, controller.signal);
        checkActive();
        if (!captions) return null;
        const payload: AnalyzeRequest = {
          videoId,
          videoTitle: captions.videoTitle,
          channelName: captions.channelName,
          uploadDate: captions.uploadDate,
          durationSeconds: captions.durationSeconds,
          transcript: captions.transcript,
          language: captions.language,
        };
        const response = await chrome.runtime.sendMessage({ type: "ANALYZE_VIDEO", payload, deadline });
        checkActive();
        if (!response?.success) throw new Error(response?.error || "Não foi possível checar o vídeo. Tente novamente.");
        return response.data;
      };
      const data = await Promise.race([
        work(),
        new Promise<never>((_, reject) => {
          timer = setTimeout(() => reject(new Error("Tempo limite de 10 segundos excedido. Tente novamente.")), Math.max(0, deadline - Date.now()));
        }),
      ]);
      if (!active()) return;
      publish(data ? { type: "ANALYSIS_SUCCESS", data } : { type: "NO_CAPTIONS_AVAILABLE" });
      button.querySelector("span")!.textContent = data ? `Veracidade: ${data.score}%` : "Sem legendas — tentar novamente";
      status.textContent = data ? "Checagem concluída" : "Legendas indisponíveis";
    } catch (error) {
      if (!active()) return;
      publish({ type: "ANALYSIS_ERROR", error: error instanceof Error ? error.message : "Falha na checagem. Tente novamente." });
      button.querySelector("span")!.textContent = "Tentar novamente";
      status.textContent = "Falha na checagem";
    } finally {
      clearTimeout(timer);
      controller.abort();
      if (active()) {
        generation++;
        button.setAttribute("aria-disabled", "false");
        button.classList.remove("evidencia-loading");
      }
    }
  });

  shadowRoot.appendChild(style);
  shadowRoot.appendChild(button);
  targetArea.prepend(badgeContainer);
}

// O YouTube é uma SPA — escuta evento nativo de navegação
window.addEventListener("yt-navigate-finish", () => {
  generation++;
  activeController?.abort();
  clearTimeout(injectionTimer);
  currentVideoId = null;
  badgeContainer?.remove();
  badgeContainer = null;
  panelState = null;
  togglePanel(false);
  if (window.location.pathname === "/watch") {
    injectTriggerBadge();
  } else {
    togglePanel(false);
  }
});

// Executa na carga inicial se já estiver em /watch
if (window.location.pathname === "/watch") {
  injectTriggerBadge();
}
