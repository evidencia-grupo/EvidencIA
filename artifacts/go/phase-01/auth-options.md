# Auditoria de Opções de Autenticação: Extensão Chrome ↔ Backend Proxy

**Data:** 2026-10-07  
**Fase:** Fase 1 — Baseline, Hardening e Segurança (H1 — Autenticação)  
**Contexto de Ameaça:** Extensões de navegador (Manifest V3) distribuídas ao público não podem reter segredos estáticos com segurança, pois qualquer segredo embutido em código fonte JS/WASM ou storage é extraível por engenharia reversa.

---

## 1. O Problema Atual
Atualmente, as chamadas para `/api/v1/analyze` e `/api/v1/feedback` originadas do service worker da extensão (`extension/src/background/service-worker.ts`) trafegam apenas com cabeçalhos HTTP normais:
```http
POST /api/v1/analyze HTTP/1.1
Content-Type: application/json
X-Client-Version: 1.0.0
```
Não há verificação de identidade ou autorização na camada da API. Qualquer agente ou script automatizado pode enviar requisições arbitrárias para o backend proxy, arriscando esgotamento de quota ou sobrecarga.

---

## 2. Comparativo de Abordagens de Autenticação

| Critério | Solução A: API Key Estática Embutida | Solução B: Token de Instalação Efêmero (App Check / PoW) | Solução C: Assinatura de Requisição (Signed Request / HMAC com Par de Chaves) | Solução D: Sessão Temporária / Token JWT Anônimo (Handshake Onboarding) |
| :--- | :---: | :---: | :---: | :---: |
| **Segurança** | **Muito Baixa** (vaza imediatamente na descompactação do `.crx`) | **Alta** (atesta integridade e unicidade do cliente) | **Média/Alta** (garante integridade do payload contra MITM) | **Alta** (tempo de vida curto, emitido pós handshake) |
| **Revogação** | Péssima (revogar quebra todos os usuários legítimos) | Excelente (revogação pontual por ID de instalação) | Boa (revogação da chave pública do cliente) | Excelente (expiração automática em 1h a 24h) |
| **Rotação** | Crítica (requer nova submissão na Chrome Web Store) | Automática (renovada em background pelo service worker) | Contínua (novo par gerado na extensão periodicamente) | Automática (refresh token transparente) |
| **Viabilidade na Extensão Pública** | Inviável para segurança real (apenas ofuscação) | **Totalmente Viável** (`chrome.storage.local` + endpoint de onboarding) | Viável via Web Crypto API nativa do Chrome | **Totalmente Viável** (armazena JWT no `chrome.storage.session` ou `local`) |
| **UX (Fricção do Usuário)** | Nenhuma (transparente) | Nenhuma (transparente no primeiro acesso) | Nenhuma (transparente em background) | Nenhuma (transparente em background) |
| **Custo de Infraestrutura** | Zero | Baixo (Redis/SQLite para registro de instâncias) | Baixo (computação CPU de verificação criptográfica) | Baixo (validação stateless de assinatura JWT) |
| **Complexidade de Implementação** | Muito Baixa | Média | Alta | Baixa/Média |

---

## 3. Avaliação Técnica Detalhada das Alternativas

### Opção A: API Key Estática Global
- **Como funciona:** Uma chave fixa `X-Evidencia-API-Key: abc...` é incluída no `service-worker.ts`.
- **Vulnerabilidade:** Extensões Chrome são clientes públicos. Ao abrir o DevTools ou descompactar o `.crx`, qualquer usuário extrai a chave em segundos. Se a chave for revogada no backend por abuso, **todos os usuários da extensão no mundo param de funcionar**.
- **Veredito:** **REJEITADA** para ambientes de produção.

### Opção B: Token de Instalação com Validação de Origem (Installation Token / App Check)
- **Como funciona:** Na primeira inicialização (`chrome.runtime.onInstalled`), a extensão gera um identificador único de instalação UUIDv4 no `chrome.storage.local` e realiza um handshake em `POST /api/v1/auth/register`. O backend valida a origem (`chrome-extension://<EXTENSION_ID>`) e emite um token assinado vinculado àquele ID.
- **Vantagens:** Permite ao backend rastrear instâncias abusivas e bloquear um token específico sem afetar os demais usuários. Não exige login do usuário (100% anônimo, preservando LGPD).
- **Veredito:** **RECOMENDADA (Solução Principal).**

### Opção C: Requisições Assinadas Criptograficamente (Web Crypto API)
- **Como funciona:** A extensão gera um par de chaves ECDSA localmente. Toda requisição carrega uma assinatura do payload e um timestamp no header. O backend armazena as chaves públicas das instâncias ativas.
- **Vantagens:** Impossibilita replay attacks e adulteração em trânsito.
- **Desvantagens:** Maior complexidade de código e overhead computacional no service worker.
- **Veredito:** **ALTERNATIVA AVANÇADA** (pode suceder a Opção B se houver ataques de replay).

### Opção D: Sessão Efêmera com JWT Anônimo (Token de Curta Duração)
- **Como funciona:** O cliente solicita um token anônimo com validade de 2 horas. As rotas `/api/v1/analyze` e `/api/v1/feedback` exigem `Authorization: Bearer <token>`.
- **Vantagens:** Stateless, rápido, fácil de implementar com FastAPI `HTTPBearer` e `PyJWT`.
- **Veredito:** **RECOMENDADA (Componente da Opção B).**

---

## 4. Recomendação Técnica Oficial

Recomendamos a combinação de **Opção B + Opção D**:
1. **Fase de Onboarding Transparente:**
   - A extensão chama `POST /api/v1/auth/token` passando um `installation_id` aleatório gerado localmente e o cabeçalho `Origin: chrome-extension://<id>`.
2. **Emissão de Token JWT Efêmero:**
   - O backend valida a origem permitida e devolve um JWT assinado com chave assimétrica (ou HMAC segura interna no backend) com TTL de 24 horas.
3. **Proteção dos Endpoints:**
   - As rotas `/api/v1/analyze`, `/api/v1/feedback` e `/api/v1/classify` validam o JWT no header `Authorization: Bearer ...`.
   - Requisições sem token ou expiradas recebem `401 Unauthorized` e a extensão renova o token automaticamente em background sem intervenção do usuário.

Essa decisão exige aprovação do responsável técnico/humano (Gate **H1 — Autenticação**).
