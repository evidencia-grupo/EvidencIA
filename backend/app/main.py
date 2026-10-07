from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.api.v1.endpoints import router as api_v1_router
from app.services.fact_checker import fact_checker_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Exceção de configuração aborta o startup do Uvicorn com código não zero.
    fact_checker_service.initialize_provider()
    try:
        yield
    finally:
        fact_checker_service.provider = None

# Rate limiter por endereço remoto (RNF-04)
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute"])

app = FastAPI(
    lifespan=lifespan,
    title="EvidencIA — Backend Proxy Seguro",
    description="API de intermediação e orquestração de checagem factual para extensão do YouTube.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuração de CORS restrito
raw_origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
exact_origins = [o for o in raw_origins if not o.startswith("chrome-extension://")]
allow_extension = any(o.startswith("chrome-extension://") for o in raw_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=exact_origins if "*" not in raw_origins else ["*"],
    allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9]+$" if allow_extension else None,
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
