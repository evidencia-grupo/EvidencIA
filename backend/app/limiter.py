"""Rate limiter centralizado para a API do EvidencIA (RNF-04)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute"],
)
