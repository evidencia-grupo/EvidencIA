from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.v1.endpoints import router as api_v1_router

# Rate limiter por endereço remoto (RNF-04)
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute"])

app = FastAPI(
    title="EvidencIA — Backend Proxy Seguro",
    description="API de intermediação e orquestração de checagem factual para extensão do YouTube.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuração de CORS restrito
origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Registra rotas da versão 1
app.include_router(api_v1_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "EvidencIA Backend Proxy",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
