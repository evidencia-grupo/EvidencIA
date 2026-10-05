from typing import Any, List

# Lista de termos técnicos e jargões proibidos na síntese voltada para Dona Lurdes (HU02 / RF-03)
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
    acessível e empática para a persona Dona Lurdes (HU02 / RF-03).
    Garante ausência de termos herméticos e separação evidente do que é fato vs boato.
    """

    def generate_accessible_summary(
        self,
        claims: List[Any],
        classification: str,
        score: int = 50,
        video_title: str = "",
    ) -> str:
        """
        Gera uma explicação em linguagem cotidiana explicando por que o vídeo recebeu
        aquela classificação e orientando o usuário sem sobrecarga técnica.
        """
        supported_claims = [c for c in claims if c.status == "apoiada"]
        contradicted_claims = [c for c in claims if c.status == "contraditada"]
        inconclusive_claims = [c for c in claims if c.status == "inconclusiva"]

        parts: List[str] = []

        if classification == "falso":
            parts.append(
                "Atenção: este vídeo contém afirmações que não são verdadeiras e foram desmentidas por dados oficiais e checagens de fontes confiáveis."
            )
            if contradicted_claims:
                parts.append(
                    f"Entre as afirmações analisadas, {len(contradicted_claims)} contrariam diretamente as informações comprovadas por especialistas."
                )
            parts.append("Recomendamos não repassar este conteúdo a familiares ou amigos sem antes verificar.")

        elif classification == "verdadeiro":
            parts.append(
                "As informações apresentadas neste vídeo foram checadas e estão corretas, com apoio em dados e fontes seguras de informação."
            )
            if supported_claims:
                parts.append(
                    f"As {len(supported_claims)} afirmações principais do conteúdo coincidem com relatórios e dados consolidados."
                )
            parts.append("O conteúdo transmite orientações seguras e pode ser compartilhado com tranquilidade.")

        elif classification == "inconclusivo":
            parts.append(
                "Atenção com as afirmações deste vídeo: no momento, não há comprovação suficiente ou existem opiniões diferentes entre os especialistas sobre o assunto."
            )
            if inconclusive_claims:
                parts.append(
                    "Algumas afirmações carecem de provas concretas para podermos dizer se são totalmente certas ou erradas."
                )
            parts.append("Vale a pena ter cautela e aguardar confirmações oficiais antes de acreditar plenamente.")

        else:  # moderado
            parts.append(
                "Este vídeo mistura informações verdadeiras com outras que são exageradas ou não têm confirmação completa."
            )
            if supported_claims and contradicted_claims:
                parts.append(
                    f"Parte do que é falado tem base em fatos reais ({len(supported_claims)} afirmação apoiada), mas há partes que foram contestadas ({len(contradicted_claims)} afirmação contradita)."
                )
            elif supported_claims and inconclusive_claims:
                parts.append(
                    f"Embora apresente fatos confirmados ({len(supported_claims)} afirmação apoiada), algumas conclusões ainda não possuem provas definitivas."
                )
            parts.append(
                "Recomendamos ler as explicações de cada ponto abaixo com atenção antes de tomar qualquer decisão ou repassar o vídeo."
            )

        summary = " ".join(parts)

        # Validação de segurança defensiva: assegura ausência de jargões técnicos
        for jargon in FORBIDDEN_JARGONS:
            if jargon in summary.lower():
                # Sanitização defensiva caso ocorra em implementações futuras
                summary = summary.replace(jargon, "análise")

        return summary


synthesis_service = SynthesisService()
