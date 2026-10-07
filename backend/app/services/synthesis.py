from typing import Any, List

# Lista de termos técnicos e jargões proibidos na síntese acessível (RF-03)
FORBIDDEN_JARGONS = [
    "algoritmo",
    "bayesiano",
    "inferência",
    "parâmetro",
    "regressão",
    "overfitting",
    "vetorial",
    "tokenização",
    "embeddings",
    "estocástico",
    "p-valor",
    "heurística",
    "convolucional",
    "machine learning",
    "redes neurais",
]


class SynthesisService:
    """
    Serviço gerador de sínteses analíticas estruturadas em linguagem clara,
    acessível e empática para a persona Dona Lurdes (RF-03).
    Garante ausência de termos herméticos e separação evidente do que é fato vs boato.
    """

    def generate_accessible_summary(self, claims: List[Any], video_title: str = "") -> str:
        """Orienta a investigação individual sem nota ou veredito sobre o vídeo."""
        if not claims:
            return "Não foram identificadas alegações checáveis neste vídeo. Opiniões e preferências pessoais não recebem nota ou veredito."
        return (
            f"Foram identificadas {len(claims)} alegações para investigar separadamente. "
            "Abra cada alegação para examinar suas fontes, datas e perguntas antes de formar sua interpretação."
        )


synthesis_service = SynthesisService()
