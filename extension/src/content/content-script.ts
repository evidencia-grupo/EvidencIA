import { extractCaptionsFromPage } from "./caption-parser";
import type { AnalyzeRequest } from "../../../shared/types/api";

console.log("[EvidencIA] Content script inicializado em", window.location.href);

let currentVideoId: string | null = null;
let panelIframe: HTMLIFrameElement | null = null;
let badgeContainer: HTMLDivElement | null = null;

function getVideoIdFromUrl(): string | null {
  const urlParams = new URLSearchParams(window.location.search);
  return urlParams.get("v");
}

function initSidePanel() {
  if (panelIframe) return;

  panelIframe = document.createElement("iframe");
  panelIframe.id = "evidencia-side-panel";
  panelIframe.src = chrome.runtime.getURL("src/panel/index.html");
  panelIframe.setAttribute("sandbox", "allow-scripts allow-same-origin");
  panelIframe.style.cssText = `
    position: fixed;
    top: 56px;
    right: 0;
    width: 380px;
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
  initSidePanel();
  if (panelIframe) {
    panelIframe.style.display = visible ? "block" : "none";
  }
}

function injectTriggerBadge() {
  const videoId = getVideoIdFromUrl();
  if (!videoId) return;
  if (videoId === currentVideoId && badgeContainer) return;

  currentVideoId = videoId;

  // Encontra o container abaixo do título do vídeo do YouTube
  const targetArea =
    document.querySelector("#above-the-fold") ||
    document.querySelector("#top-row") ||
    document.querySelector("ytd-watch-metadata");

  if (!targetArea) {
    setTimeout(injectTriggerBadge, 1000);
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
    .evidencia-icon {
      width: 16px;
      height: 16px;
      fill: #2BA640;
    }
    .evidencia-loading {
      opacity: 0.7;
      cursor: wait;
    }
  `;

  const button = document.createElement("button");
  button.className = "evidencia-btn";
  button.innerHTML = `
    <svg class="evidencia-icon" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg>
    <span>Verificar Veracidade</span>
  `;

  button.addEventListener("click", async () => {
    // 1. Confirmação visual imediata <= 1s (RNF-01 / HU01 / HU03)
    button.classList.add("evidencia-loading");
    button.querySelector("span")!.textContent = "Analisando...";
    togglePanel(true);

    try {
      // 2. Extrai metadados do vídeo
      const videoTitle =
        document.querySelector("h1.ytd-watch-metadata")?.textContent?.trim() ||
        document.title;
      const channelName =
        document.querySelector("#channel-name")?.textContent?.trim() || "Canal YouTube";

      // 3. Extrai legendas (HU05 / HU10)
      const captions = await extractCaptionsFromPage(videoId);

      if (!captions) {
        button.querySelector("span")!.textContent = "Sem Legendas";
        button.classList.remove("evidencia-loading");
        // Notifica o painel sobre a ausência de legendas (HU10)
        panelIframe?.contentWindow?.postMessage(
          { type: "NO_CAPTIONS_AVAILABLE" },
          "*"
        );
        return;
      }

      const requestPayload: AnalyzeRequest = {
        videoId,
        videoTitle,
        channelName,
        transcript: captions.transcript,
        language: captions.language,
      };

      // 4. Solicita análise ao Service Worker
      chrome.runtime.sendMessage(
        { type: "ANALYZE_VIDEO", payload: requestPayload },
        (response) => {
          button.classList.remove("evidencia-loading");
          if (response?.success) {
            button.querySelector("span")!.textContent = `Veracidade: ${response.data.score}%`;
            panelIframe?.contentWindow?.postMessage(
              { type: "ANALYSIS_SUCCESS", data: response.data },
              "*"
            );
          } else {
            button.querySelector("span")!.textContent = "Erro na Checagem";
            panelIframe?.contentWindow?.postMessage(
              { type: "ANALYSIS_ERROR", error: response?.error },
              "*"
            );
          }
        }
      );
    } catch (err) {
      button.classList.remove("evidencia-loading");
      button.querySelector("span")!.textContent = "Erro Inesperado";
      console.error("[EvidencIA] Erro na checagem:", err);
    }
  });

  shadowRoot.appendChild(style);
  shadowRoot.appendChild(button);
  targetArea.prepend(badgeContainer);
}

// O YouTube é uma SPA — escuta evento nativo de navegação
window.addEventListener("yt-navigate-finish", () => {
  if (window.location.pathname === "/watch") {
    setTimeout(injectTriggerBadge, 500);
  } else {
    togglePanel(false);
  }
});

// Executa na carga inicial se já estiver em /watch
if (window.location.pathname === "/watch") {
  setTimeout(injectTriggerBadge, 1000);
}
