"""Base abstrata para adapters de datasets do pipeline EvidencIA.

Define o contrato que todos os adapters devem implementar e o registro
central de adapters por nome.

Refs: ADR-001, IS-04.
"""

from __future__ import annotations

import abc
from typing import Iterator, Union

from ml.schemas.evidence import EvidenceRecord, NewsRecord

# Tipo canônico de saída dos adapters
CanonicalRecord = Union[EvidenceRecord, NewsRecord]


class DatasetAdapter(abc.ABC):
    """Interface base para adapters de ingestão de datasets.

    Cada adapter é responsável por:
    1. Ler o dataset bruto do ``input_dir`` (bronze).
    2. Converter cada linha no schema canônico (``EvidenceRecord`` ou ``NewsRecord``).
    3. Nunca fazer download de rede (isso é responsabilidade do operador).

    Todos os adapters devem ser registrados em ``ADAPTER_REGISTRY``.
    """

    #: Nome do dataset (deve coincidir com a chave em sources.yaml)
    name: str

    @abc.abstractmethod
    def parse(self, input_dir: str) -> Iterator[CanonicalRecord]:
        """Lê o dataset bruto e retorna um iterador de registros canônicos.

        Args:
            input_dir: Caminho local para o diretório com os arquivos brutos (bronze).

        Yields:
            Instâncias de ``EvidenceRecord`` ou ``NewsRecord``.

        Raises:
            FileNotFoundError: Se o ``input_dir`` não existir ou estiver vazio.
            ValueError: Se os dados não estiverem no formato esperado.
        """
        ...

    def to_canonical(self, raw: dict) -> CanonicalRecord:
        """Converte um dicionário bruto em um registro canônico.

        Implementação opcional; adapters simples podem não precisar.

        Args:
            raw: Dicionário com os dados brutos de uma linha do dataset.

        Returns:
            Instância de ``EvidenceRecord`` ou ``NewsRecord``.
        """
        raise NotImplementedError(f"{self.__class__.__name__} não implementou to_canonical()")


# ---------------------------------------------------------------------------
# Registro de adapters
# ---------------------------------------------------------------------------

#: Registro global de adapters por nome do dataset.
#: Populado por cada módulo de adapter ao importar.
ADAPTER_REGISTRY: dict[str, type[DatasetAdapter]] = {}


def register_adapter(adapter_cls: type[DatasetAdapter]) -> type[DatasetAdapter]:
    """Decorador / função para registrar um adapter no registry global.

    Args:
        adapter_cls: Classe que herda de ``DatasetAdapter``.

    Returns:
        A própria classe (para uso como decorador).

    Example::

        @register_adapter
        class FakeBrAdapter(DatasetAdapter):
            name = "fakebr"
            ...
    """
    if not hasattr(adapter_cls, "name") or not adapter_cls.name:
        raise ValueError(f"Adapter {adapter_cls.__name__} deve definir o atributo 'name'")
    ADAPTER_REGISTRY[adapter_cls.name] = adapter_cls
    return adapter_cls


def get_adapter(source_name: str) -> DatasetAdapter:
    """Instancia e retorna o adapter correspondente ao nome do dataset.

    Args:
        source_name: Nome do dataset (ex.: 'fakebr', 'factchecksbr').

    Returns:
        Instância do adapter registrado.

    Raises:
        ValueError: Se ``source_name`` não estiver no registry.
    """
    # Importação local para garantir que os módulos de adapter sejam carregados
    from ml.datasets.adapters import fakebr, factchecksbr, claimreview  # noqa: F401

    if source_name not in ADAPTER_REGISTRY:
        valid = sorted(ADAPTER_REGISTRY.keys())
        raise ValueError(
            f"Adapter '{source_name}' não encontrado. "
            f"Adapters disponíveis: {valid}"
        )
    return ADAPTER_REGISTRY[source_name]()
