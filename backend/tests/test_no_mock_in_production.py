"""Testes de segurança e governança contra uso indevido de Mocks em Produção.

Garantias testadas:
(a) Factory com APP_ENV='production' ou 'prod' + LLM_PROVIDER='mock' lança MockInProductionError.
(b) APP_ENV='development' com LLM_PROVIDER='mock' é permitido para testes locais.
(c) Valor inválido de LLM_PROVIDER lança ValueError descritivo.
(d) Varredura estática: nenhum módulo em backend/app/ (exceto providers/mock.py e factory.py)
    pode importar diretamente providers.mock.

Refs: ADR-001, IS-11.
"""

import ast
import os
import pytest

from app.services.providers.factory import get_provider
from app.services.providers.types import MockInProductionError
from app.services.providers.mock import MockProvider


def test_factory_raises_mock_in_production():
    """Tentar instanciar o mock provider em produção deve falhar imediatamente."""
    for prod_env in ["production", "Production", "PROD", "prod"]:
        with pytest.raises(MockInProductionError) as exc_info:
            get_provider(provider_name="mock", app_env=prod_env)
        assert "não é permitido em ambiente de produção" in str(exc_info.value)


def test_factory_allows_mock_in_development():
    """Mock provider é permitido em ambiente de desenvolvimento ou testes locais."""
    for dev_env in ["development", "dev", "test", "local"]:
        provider = get_provider(provider_name="mock", app_env=dev_env)
        assert isinstance(provider, MockProvider)
        assert provider.is_mock is True


def test_factory_invalid_provider_raises_value_error():
    """Provedor com nome não reconhecido deve levantar ValueError."""
    with pytest.raises(ValueError) as exc_info:
        get_provider(provider_name="desconhecido", app_env="development")
    assert "Provedor LLM inválido" in str(exc_info.value)
    assert "ollama" in str(exc_info.value)


def test_no_direct_imports_of_mock_in_app():
    """Varre a árvore de código backend/app/ para garantir que nenhum módulo importe providers.mock diretamente.

    Regra de ouro: apenas factory.py pode importar mock.py para instanciação controlada.
    """
    app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))

    # Arquivos permitidos a referenciar o mock
    allowed_files = {
        os.path.normpath(os.path.join(app_root, "services", "providers", "mock.py")),
        os.path.normpath(os.path.join(app_root, "services", "providers", "factory.py")),
        os.path.normpath(os.path.join(app_root, "services", "providers", "__init__.py")),
    }

    violations = []

    for root, _, files in os.walk(app_root):
        for file in files:
            if not file.endswith(".py"):
                continue

            full_path = os.path.normpath(os.path.join(root, file))
            if full_path in allowed_files:
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read(), filename=full_path)
                except SyntaxError:
                    continue

            for node in ast.walk(tree):
                # Caso 1: import app.services.providers.mock
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if "providers.mock" in alias.name:
                            violations.append((full_path, alias.name))
                # Caso 2: from app.services.providers import mock (ou from ...providers.mock import ...)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if "providers.mock" in module:
                        violations.append((full_path, module))
                    elif "providers" in module:
                        for alias in node.names:
                            if alias.name == "mock" or alias.name == "MockProvider":
                                violations.append((full_path, f"{module}.{alias.name}"))

    assert not violations, f"Importação direta indevida de Mock detectada em código de aplicação: {violations}"
