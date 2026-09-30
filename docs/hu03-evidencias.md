# HU03 — Evidências de validação local

## Revalidação em 30/09/2026

- Tipagem, build, Ruff, 63 testes Vitest, 10 testes Pytest (com warnings tratados como erro) e 7 cenários Playwright aprovados.
- Cobertura da extensão: 99,74% de linhas/instruções, 95,68% de ramificações e 100% de funções. Backend: 97,62% com ramificações.
- O cenário de cache agora recarrega a página do vídeo e confirma a recuperação do armazenamento local com fetch do worker bloqueado e sem nova extração de legendas.
- Medição desta execução no Chromium: feedback 12,0ms; síntese simulada 443,9ms; reabertura do painel por cache 31,7ms; cache após recarregar o vídeo 13,8ms. Uma execução não representa P90 de produção.
- Parecer: confirmação visual e cache aprovados no ambiente controlado. A síntese em até 10s foi aprovada somente com mock, backend localhost e legendas controladas. O critério factual permanece pendente.
- O responsável definiu que será usada uma IA própria e autorizou manter a integração como **ainda em preparação**. Não fechar a issue como integralmente aceita até integrar e homologar esse pipeline.

## Validação anterior

Data: 28/09/2026. macOS arm64; Node 24.21.0; Python 3.14.6; Chromium 153.0.8010.12 headless, perfil descartável. Extensão compilada carregada com Manifest V3, content script isolado, iframe real e Service Worker real.

## Resultados

- TypeScript estrito, Vite e Ruff: aprovados.
- Vitest: 63 testes aprovados; 99,74% de linhas/instruções, 95,68% de ramificações, 100% de funções. Todos os arquivos excedem 80% nas quatro métricas.
- Pytest: 10 testes aprovados, sem warnings com `-W error`; cobertura com ramificações 97,62%. Serviço de análise e schemas com 100%.
- Playwright: 7 cenários aprovados (18,9s de duração da suíte, incluindo o cenário de timeout). Mais 10 execuções do cenário de latência, todas aprovadas.
- axe-core: zero violações WCAG 2.1 A/AA nos estados exercitados (carregamento, falha, resultado e quatro classificações). A regra `video-caption` pede revisão do elemento de vídeo da página de teste; ela não é uma violação identificada na extensão. A auditoria automática não equivale à certificação WCAG integral.
- Teclado real via Playwright: Tab, Shift+Tab, Enter, Espaço, Escape, foco visível, fechamento e retorno ao botão aprovados.

## Latência: 10 execuções

Valores em milissegundos; P90 pelo método nearest-rank. Cada execução usa contexto Chromium novo, primeira análise e reabertura com cache aquecido.

| Medida | Mínimo | P90 | Máximo | Limite |
|---|---:|---:|---:|---:|
| Feedback | 13.9 | 23.1 | 23.3 | ≤ 1.000 |
| Síntese simulada | 426 | 435.8 | 437.6 | ≤ 10.000 |
| Cache local | 31.2 | 31.8 | 31.8 | < 100 |
| Tempo excedente de tarefas longas | 0 | 0 | 0 | ≤ 50 |

Os testes interceptam somente as páginas/legendas do YouTube com conteúdo controlado e usam o FastAPI real em localhost, configurado com o provedor mock (espera simulada de 400ms). Não há IA real nem tráfego de busca externo. O teste de cache impede fetch do worker e conta extrações de legendas. O relógio do browser mede clique até requestAnimationFrame após inserção do resultado; não é captura física dos pixels.

O indicador de bloqueio soma o excedente de 50ms das tarefas longas observadas na página controlada; não demonstra impacto de TBT no YouTube real sob carga. Não houve interferência no método pause do player no cenário sem legendas.

[Dados brutos, ambiente e hashes do build](hu03-medicoes.json). [Resumo da auditoria de acessibilidade](hu03-acessibilidade.json). Relatórios completos podem ser gerados novamente com os comandos em [HU03.md](../HU03.md); a CI arquiva os relatórios de cobertura e Playwright.

## O que permanece externo à homologação local

A equipe informou que ainda implementará IA e busca. Após isso, repetir os testes com vídeos reais, rede definida e fontes verificáveis para validar qualidade factual e P90 de produção. A extração de legendas foi validada contra fixtures em mundo MAIN/ISOLATED reais, não contra a disponibilidade atual da API interna do YouTube. A matriz/catálogo do portal externo não foi alterada. Estes resultados não justificam fechar a issue como homologada em produção.
