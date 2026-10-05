"""Wrapper do encoder de embeddings para o pipeline EvidencIA.

Usa sentence-transformers com import tardio (dentro das funções)
para não bloquear a inicialização quando a biblioteca não está instalada.

Configuração via env:
    EMBEDDING_MODEL: nome do modelo (padrão: neuralmind/bert-base-portuguese-cased)

Refs: ADR-001, IS-06.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Modelo padrão: BERT em PT-BR (NILC / USP)
DEFAULT_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "neuralmind/bert-base-portuguese-cased",
)

# Segundo modelo para comparação (seção 13 do notebook EDA)
ALT_MODEL = os.getenv(
    "EMBEDDING_MODEL_ALT",
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
)


class EmbeddingEncoder:
    """Wrapper de sentence-transformers com import tardio.

    O modelo é carregado apenas na primeira chamada a ``encode()``,
    evitando dependência obrigatória de ``sentence_transformers`` em todos os módulos.

    Args:
        model_name: Nome do modelo Hugging Face. Usa ``DEFAULT_MODEL`` se omitido.
    """

    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or DEFAULT_MODEL
        self._model = None  # Import tardio

    def _load_model(self) -> None:
        """Carrega o modelo de embedding (import tardio)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers não está instalado. "
                    "Execute: pip install -r requirements-ml.txt"
                ) from exc
            logger.info("Carregando modelo de embedding: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info("Modelo carregado: %s", self.model_name)

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Gera embeddings para uma lista de textos.

        Args:
            texts: Lista de strings a codificar.
            batch_size: Tamanho do batch de inferência.

        Returns:
            Lista de vetores (listas de float).

        Raises:
            ImportError: Se sentence-transformers não estiver instalado.
        """
        self._load_model()
        assert self._model is not None  # type narrowing
        embeddings = self._model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Retorna a dimensão dos vetores gerados pelo modelo.

        Raises:
            ImportError: Se sentence-transformers não estiver instalado.
        """
        self._load_model()
        assert self._model is not None
        return self._model.get_sentence_embedding_dimension()


# Instâncias padrão (lazy — não carregam até o primeiro uso)
default_encoder = EmbeddingEncoder(DEFAULT_MODEL)
alt_encoder = EmbeddingEncoder(ALT_MODEL)
