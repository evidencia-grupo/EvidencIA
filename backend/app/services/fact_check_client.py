import logging
import re
from typing import Dict, List, Literal, Optional
import httpx
from pydantic import BaseModel
from app.config import settings

ClaimVerificationStatus = Literal["apoiada", "contraditada", "inconclusiva"]


class FactCheckingSource(BaseModel):
    id: str
    title: str
    url: str
    domain: str
    reliabilityScore: Optional[float] = None
    publishedAt: Optional[str] = None

logger = logging.getLogger(__name__)

# Mapeamento semântico de vereditos do ClaimReview em PT-BR para ClaimVerificationStatus
RATING_MAP: Dict[str, ClaimVerificationStatus] = {
    # Vereditos de Contradição / Falso
    "falso": "contraditada",
    "mentira": "contraditada",
    "enganoso": "contraditada",
    "inverídico": "contraditada",
    "fake": "contraditada",
    "desmentido": "contraditada",
    "incorreto": "contraditada",
    "errado": "contraditada",
    # Vereditos de Apoio / Fato
    "verdadeiro": "apoiada",
    "fato": "apoiada",
    "correto": "apoiada",
    "autêntico": "apoiada",
    "comprovado": "apoiada",
    # Vereditos Inconclusivos / Contexto / Divergência
    "distorcido": "inconclusiva",
    "fora de contexto": "inconclusiva",
    "sem contexto": "inconclusiva",
    "exagerado": "inconclusiva",
    "impreciso": "inconclusiva",
    "inconclusivo": "inconclusiva",
    "discutível": "inconclusiva",
    "sem comprovação": "inconclusiva",
    "subestimado": "inconclusiva",
}


def normalize_rating_to_status(rating_text: str) -> ClaimVerificationStatus:
    """
    Converte o veredito textual emitido pela agência checadora (ClaimReview)
    para um dos três status permitidos pelo contrato de dados: apoiada, contraditada ou inconclusiva.
    """
    clean_text = rating_text.lower().strip()
    for keyword, status in RATING_MAP.items():
        if keyword in clean_text:
            return status
    return "inconclusiva"


def extract_domain_from_url(url: str) -> str:
    """Extrai o domínio limpo a partir de uma URL HTTP/HTTPS."""
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    return match.group(1) if match else "agenciachecagem.org"


class FactCheckClient:
    """
    Cliente assíncrono para a Google Fact Check Tools API (ClaimReview RAG).
    Realiza busca semântica em base de alegações jornalísticas indexadas (Lupa, Aos Fatos, Boatos.org, etc.)
    sem acoplar treinamento de modelos a chamadas externas (conforme decisão de arquitetura).
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_FACT_CHECK_API_KEY
        self.base_url = base_url or settings.FACT_CHECK_API_URL

    async def search_claims(
        self,
        query: str,
        language_code: str = "pt-BR",
        max_results: int = 3,
    ) -> List[Dict]:
        """
        Consulta a Google Fact Check Tools API buscando checagens prévias para o termo.
        Retorna lista de dicionários brutos formatados com fontes e vereditos.
        """
        if not self.api_key:
            logger.debug("Google Fact Check API Key não configurada; operando em modo offline/mock.")
            return []

        params = {
            "query": query,
            "languageCode": language_code,
            "key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(self.base_url, params=params)
                if response.status_code != 200:
                    logger.warning(
                        f"Google Fact Check API respondeu com status {response.status_code}: {response.text}"
                    )
                    return []

                data = response.json()
                return self.parse_claims_response(data, max_results=max_results)
        except Exception as exc:
            logger.warning(f"Falha ao consultar Google Fact Check API ({str(exc)}); degradando com segurança.")
            return []

    def parse_claims_response(self, data: Dict, max_results: int = 3) -> List[Dict]:
        """
        Interpreta o JSON retornado pela Google Fact Check API e normaliza
        para o formato de alegações e fontes auditadas do EvidencIA.
        """
        results: List[Dict] = []
        raw_claims = data.get("claims", [])

        for idx, item in enumerate(raw_claims[:max_results]):
            claim_text = item.get("text", "")
            claim_reviews = item.get("claimReview", [])
            if not claim_reviews:
                continue

            first_review = claim_reviews[0]
            publisher = first_review.get("publisher", {})
            pub_name = publisher.get("name", "Agência de Checagem")
            pub_site = publisher.get("site", "")
            review_url = first_review.get("url", "")
            review_title = first_review.get("title", f"Checagem por {pub_name}")
            textual_rating = first_review.get("textualRating", "Inconclusivo")
            review_date = first_review.get("reviewDate")

            domain = pub_site or extract_domain_from_url(review_url)
            status = normalize_rating_to_status(textual_rating)

            source = FactCheckingSource(
                id=f"src-gfc-{idx + 1}",
                title=f"{pub_name}: {review_title}",
                url=review_url,
                domain=domain,
                reliabilityScore=0.96,  # Agências IFCN possuem elevado índice de confiabilidade
                publishedAt=review_date,
            )

            results.append({
                "claim_text": claim_text,
                "status": status,
                "rating_text": textual_rating,
                "evidence_summary": f"Veredito '{textual_rating}' emitido por {pub_name}: {review_title}",
                "source": source,
                "confidence": 0.95,
            })

        return results


fact_check_client = FactCheckClient()
