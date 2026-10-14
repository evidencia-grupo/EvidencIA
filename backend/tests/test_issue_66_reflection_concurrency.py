import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.types import Claim, ProviderUnavailableError
from app.schemas import AnalyzeRequest
from app.services.fact_checker import FactCheckerService
from app.providers.reflection_catalog import REFLECTION_QUESTIONS

VALID_QUESTIONS = REFLECTION_QUESTIONS[3:6]


def make_request() -> AnalyzeRequest:
    claims = [
        "A população aumentou em 2021.",
        "O PIB diminuiu em 2021.",
        "A inflação aumentou em 2021.",
        "O desemprego diminuiu em 2021.",
    ]

    return AnalyzeRequest(
        videoId="issue-66",
        videoTitle="Indicadores econômicos de 2021",
        channelName="Canal de teste",
        transcript=" ".join(claims) * 2,
        uploadDate="2021-12-31",
    )


def make_provider() -> MagicMock:
    provider = MagicMock()
    provider.is_mock = False

    provider.extract_claims = AsyncMock(
        return_value=[
            Claim(text="A população aumentou em 2021."),
            Claim(text="O PIB diminuiu em 2021."),
            Claim(text="A inflação aumentou em 2021."),
            Claim(text="O desemprego diminuiu em 2021."),
        ]
    )

    return provider


@pytest.mark.asyncio
async def test_reflections_run_concurrently_with_limit_of_three():
    provider = make_provider()

    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def reflect(claims, evidence):
        nonlocal active, peak

        async with lock:
            active += 1
            peak = max(peak, active)

        try:
            await asyncio.sleep(0.05)
            return VALID_QUESTIONS.copy()
        finally:
            async with lock:
                active -= 1

    provider.generate_reflection = AsyncMock(side_effect=reflect)

    with (
        patch(
            "app.services.fact_checker.get_provider",
            return_value=provider,
        ),
        patch(
            "app.services.fact_checker.brazilian_fact_matcher.find_match",
            return_value=None,
        ),
        patch(
            "app.services.fact_checker.fact_check_client.search_claims",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await FactCheckerService().analyze(make_request())

    assert len(result.claims) == 4
    assert provider.generate_reflection.await_count == 4

    # Issue #66: deve existir concorrência, mas limitada a três reflexões.
    assert peak == 3

    assert all(
        claim.reflectionQuestions == VALID_QUESTIONS
        for claim in result.claims
    )


@pytest.mark.asyncio
async def test_one_reflection_failure_does_not_abort_other_claims():
    provider = make_provider()

    attempted = []

    async def reflect(claims, evidence):
        claim_text = claims[0].text
        attempted.append(claim_text)

        if "inflação" in claim_text.lower():
            raise ProviderUnavailableError(
                "falha isolada da terceira alegação"
            )

        await asyncio.sleep(0)
        return VALID_QUESTIONS.copy()

    provider.generate_reflection = AsyncMock(side_effect=reflect)

    with (
        patch(
            "app.services.fact_checker.get_provider",
            return_value=provider,
        ),
        patch(
            "app.services.fact_checker.brazilian_fact_matcher.find_match",
            return_value=None,
        ),
        patch(
            "app.services.fact_checker.fact_check_client.search_claims",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await FactCheckerService().analyze(make_request())

    assert len(result.claims) == 4

    # Todas as quatro alegações devem ter sido tentadas.
    assert provider.generate_reflection.await_count == 4
    assert len(attempted) == 4

    # Somente a alegação que falhou recebe fallback.
    assert result.claims[2].reflectionQuestions == (
        FactCheckerService.FALLBACK_REFLECTION_QUESTIONS
    )

    assert result.claims[0].reflectionQuestions == VALID_QUESTIONS
    assert result.claims[1].reflectionQuestions == VALID_QUESTIONS
    assert result.claims[3].reflectionQuestions == VALID_QUESTIONS
