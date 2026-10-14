"""Rate limiter centralizado para a API do EvidencIA (RNF-04)."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import settings


def client_key(request: Request) -> str:
    """Identifica o cliente para o rate limit.

    Atrás de N proxies confiáveis (TRUSTED_PROXY_HOPS), usa a N-ésima entrada a partir da direita
    de X-Forwarded-For: é a anexada pelo proxy mais externo que controlamos. Entradas à esquerda
    vêm do próprio cliente e podem ser forjadas. Sem proxy configurado, o cabeçalho é ignorado.
    """
    hops = settings.TRUSTED_PROXY_HOPS
    if hops > 0:
        chain = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
        if len(chain) >= hops:
            return chain[-hops]
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_key,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    default_limits=[f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute"],
)
