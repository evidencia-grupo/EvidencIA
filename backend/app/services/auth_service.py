"""Serviço de autenticação e emissão de tokens efêmeros para a extensão (ADR-002, RNF-01)."""

import hashlib
import hmac
import time
from typing import Optional

from fastapi import Header, HTTPException, status

from app.config import settings


class AuthService:
    """Emite e valida credenciais efêmeras rotacionáveis para clientes da extensão."""

    def __init__(self):
        self.ttl_seconds = 86400  # 24 horas

    def _sign(self, payload: str) -> str:
        secret = settings.AUTH_SECRET.encode("utf-8")
        return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def create_token(self, installation_id: str) -> str:
        """Cria token efêmero no formato <installation_id>.<expires_at>.<signature>."""
        expires_at = int(time.time()) + self.ttl_seconds
        payload = f"{installation_id}.{expires_at}"
        signature = self._sign(payload)
        return f"{payload}.{signature}"

    def verify_token(self, token: str) -> Optional[dict]:
        """Valida token e verifica integridade e expiração."""
        try:
            parts = token.strip().split(".")
            if len(parts) != 3:
                return None
            installation_id, expires_at_str, signature = parts
            expires_at = int(expires_at_str)
            if time.time() > expires_at:
                return None  # Expirado
            payload = f"{installation_id}.{expires_at}"
            expected_signature = self._sign(payload)
            if not hmac.compare_digest(signature, expected_signature):
                return None  # Assinatura inválida
            return {"installation_id": installation_id, "expires_at": expires_at}
        except Exception:
            return None


auth_service = AuthService()


async def get_current_client(
    authorization: Optional[str] = Header(None, description="Token de autenticação Bearer"),
) -> Optional[dict]:
    """Dependência FastAPI para verificação de autorização da extensão."""
    if not settings.REQUIRE_AUTH:
        # Em modo permissivo (dev/test), aceita chamada anônima se nenhum header for enviado
        if not authorization:
            return {"installation_id": "anonymous-dev"}
        token = authorization.replace("Bearer ", "").strip()
        verified = auth_service.verify_token(token)
        return verified or {"installation_id": "anonymous-dev"}

    # Modo estrito com autenticação obrigatória
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial de autenticação ausente ou mal formatada.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.replace("Bearer ", "").strip()
    verified = auth_service.verify_token(token)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credencial de autenticação inválida ou expirada.",
        )
    return verified
