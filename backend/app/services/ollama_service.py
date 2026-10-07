import json
import logging
from typing import Dict, List, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """
    Serviço cliente para o motor de IA local Ollama executando o modelo Qwen 2.5-3B.
    Realiza inferência 100% offline em português brasileiro (PT-BR),
    guiado pelas diretrizes dos datasets ClaimPT e FactChecks.br.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout_seconds or settings.OLLAMA_TIMEOUT_SECONDS

    async def is_available(self) -> bool:
        """Verifica se o daemon do Ollama está em execução e acessível."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def extract_claims_with_qwen(self, transcript: str, video_title: str) -> Optional[List[Dict]]:
        """
        Extrai proposições atômicas checáveis (ClaimPT criteria) utilizando o Qwen 2.5-3B local.
        Retorna lista de alegações estruturadas ou None em caso de falha/indisponibilidade.
        """
        system_prompt = (
            "Você é um especialista em checagem de fatos e análise de desinformação em português do Brasil. "
            "Sua tarefa é ler a transcrição de um vídeo e extrair de 0 a 4 alegações factuais atômicas centrais. "
            "Diretrizes (baseadas no padrão ClaimPT e agências brasileiras IFCN):\n"
            "1. Ignore saudações, pedidos de inscrição, opiniões subjetivas ou conversas fiadas.\n"
            "2. Isole somente afirmações sobre fatos, dados, saúde, ciência ou economia que possam ser comprovadas ou desmentidas.\n"
            "3. Para cada alegação, defina o texto, um termo de busca curto para agências de checagem, "
            "um veredito preliminar ('apoiada', 'contraditada' ou 'inconclusiva') e uma justificativa factual.\n"
            "Responda estritamente em formato JSON válido contendo a chave 'claims'."
        )

        user_content = (
            f"Título do Vídeo: {video_title}\n\n"
            f"Transcrição:\n{transcript[:2500]}\n\n"
            "Formato esperado de resposta JSON:\n"
            "{\n"
            '  "claims": [\n'
            '    {\n'
            '      "text": "Texto exato da alegação",\n'
            '      "search_query": "Termo limpo de busca",\n'
            '      "status": "apoiada|contraditada|inconclusiva",\n'
            '      "evidence_summary": "Justificativa factual neutra",\n'
            '      "confidence": 0.90\n'
            '    }\n'
            "  ]\n"
            "}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code != 200:
                    logger.warning(f"Ollama respondeu com status {res.status_code}: {res.text}")
                    return None

                response_json = res.json()
                content = response_json.get("message", {}).get("content", "")
                parsed = json.loads(content)
                claims = parsed.get("claims", [])
                if isinstance(claims, list):
                    return claims
                return None
        except Exception as exc:
            logger.debug(f"Ollama local indisponível ou timeout ({str(exc)}); acionando fallback.")
            return None

    async def generate_accessible_summary_with_qwen(
        self,
        claims: List[Dict],
        video_title: str,
    ) -> Optional[str]:
        """
        Gera uma síntese analítica em tom claro e empático (persona Dona Lurdes) via Qwen local.
        """
        system_prompt = (
            "Você é um assistente de checagem de fatos dedicado a explicar a veracidade de conteúdos "
            "em português do Brasil de maneira simples, acolhedora e direta para pessoas leigas (persona Dona Lurdes). "
            "Regras obrigatórias:\n"
            "1. NUNCA use jargões técnicos como 'algoritmo', 'inferência', 'bayesiano', 'overfitting' ou termos acadêmicos complexos.\n"
            "2. Oriente a investigação separada de cada alegação; não atribua nota, porcentagem ou veredito global ao vídeo.\n"
            "3. Mantenha o texto com 2 a 4 frases objetivas."
        )

        claims_summary = "\n".join(
            f"- [{c.get('status', 'inconclusiva').upper()}] {c.get('text', '')}: {c.get('evidence_summary', '')}"
            for c in claims
        )

        user_content = (
            f"Título do Vídeo: {video_title}\n"
            f"Alegações examinadas:\n{claims_summary}\n\n"
            "Escreva a síntese acessível em linguagem simples:"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text = data.get("message", {}).get("content", "").strip()
                    if text:
                        return text
                return None
        except Exception:
            return None

ollama_service = OllamaService()
