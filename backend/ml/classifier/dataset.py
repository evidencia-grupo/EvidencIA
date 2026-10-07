"""Carregador e compilador de datasets para treinamento de classificadores em PT-BR."""

import csv
import json
import os
from dataclasses import dataclass
from typing import List, Optional

FIXTURE_FAKEBR_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "tests", "fixtures", "fakebr_sample.csv"
)
SAMPLE_FACTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "sample_facts.json"
)


@dataclass
class TrainingSample:
    text: str
    label: str  # "fake" ou "true"
    category: str
    source: str

    @property
    def binary_label(self) -> int:
        return 1 if self.label == "true" else 0


# Amostras adicionais alinhadas aos padrões do Fake.br e FactChecks.br
CURATED_CORPUS = [
    # Saúde - Falsas
    ("Chá milagroso de folhas de graviola elimina tumores cancerígenos sem quimioterapia ou cirurgia.", "fake", "saúde", "Fake.br"),
    ("Gargarejo com água morna e vinagre destrói o vírus antes de atingir os pulmões.", "fake", "saúde", "FactChecks.br"),
    ("Uso contínuo de máscaras de proteção provoca hipóxia e envenenamento por gás carbônico.", "fake", "saúde", "FactChecks.br"),
    ("Comer alho cru pela manhã com água fervente previne completamente qualquer infecção por gripe.", "fake", "saúde", "Fake.br"),
    ("Vacinas da infância contêm mercúrio em doses tóxicas que causam transtorno do espectro autista.", "fake", "saúde", "FactChecks.br"),
    ("Gotas de óleo de orégano diluído curam sinusite bacteriana em menos de duas horas.", "fake", "saúde", "Fake.br"),
    ("Transfusão de sangue de pessoas vacinadas transmite anticorpos alterados geneticamente.", "fake", "saúde", "FactChecks.br"),
    ("Beber água gelada após as refeições solidifica gorduras e causa infarto fulminante.", "fake", "saúde", "Fake.br"),
    ("Aplicar pasta de dente em queimaduras de segundo grau regenera a pele instantaneamente.", "fake", "saúde", "Fake.br"),
    ("Inalar vapor de eucalipto com álcool cura bronquite e asma crônica.", "fake", "saúde", "Fake.br"),

    # Saúde - Verdadeiras
    ("A vacina tríplice viral protege eficazmente contra sarampo, caxumba e rubéola.", "true", "saúde", "FactChecks.br"),
    ("O controle da hipertensão arterial reduz significativamente o risco de acidente vascular cerebral.", "true", "saúde", "FactChecks.br"),
    ("Antibióticos atuam exclusivamente contra bactérias e não têm efeito contra infecções causadas por vírus.", "true", "saúde", "FactChecks.br"),
    ("Lavar as mãos com água e sabão por 20 segundos reduz a transmissão de patógenos respiratórios.", "true", "saúde", "FactChecks.br"),
    ("O tabagismo ativo é a principal causa evitável de câncer de pulmão e doenças cardiovasculares.", "true", "saúde", "FactChecks.br"),
    ("A prática regular de exercícios físicos melhora a sensibilidade à insulina em pacientes com diabetes.", "true", "saúde", "FactChecks.br"),
    ("O aleitamento materno exclusivo é recomendado pela OMS até os seis meses de vida da criança.", "true", "saúde", "FactChecks.br"),
    ("A mamografia de rastreamento periódica auxilia no diagnóstico precoce do câncer de mama.", "true", "saúde", "FactChecks.br"),
    ("A dengue é transmitida pela picada da fêmea do mosquito Aedes aegypti infectada pelo vírus.", "true", "saúde", "FactChecks.br"),
    ("O Sistema Único de Saúde garante atendimento médico integral e distribuição gratuita de insulina.", "true", "saúde", "FactChecks.br"),

    # Economia - Falsas
    ("Governo federal confiscará todas as contas poupança a partir do próximo mês.", "fake", "economia", "Fake.br"),
    ("Nota de duzentos reais deixará de circular e perderá o valor de compra imediatamente.", "fake", "economia", "FactChecks.br"),
    ("Receita Federal cobra taxa compulsória de dez por cento sobre qualquer chave Pix cadastrada.", "fake", "economia", "FactChecks.br"),
    ("Bancos anunciam encerramento de agências e bloqueio automático de cartões de débito.", "fake", "economia", "Fake.br"),
    ("Moeda digital oficial do Brasil substituirá o dinheiro físico e cancelará cédulas em circulação.", "fake", "economia", "FactChecks.br"),

    # Economia - Verdadeiras
    ("O Índice Nacional de Preços ao Consumidor Amplo (IPCA) é a medida oficial da inflação no Brasil.", "true", "economia", "FactChecks.br"),
    ("O Comitê de Política Monetária (Copom) do Banco Central define a taxa básica de juros Selic.", "true", "economia", "FactChecks.br"),
    ("O Fundo Garantidor de Créditos assegura depósitos bancários até o limite de 250 mil reais por CPF.", "true", "economia", "FactChecks.br"),
    ("O Produto Interno Bruto mede a soma de todos os bens e serviços finais produzidos no país.", "true", "economia", "FactChecks.br"),
    ("O salário mínimo nacional é reajustado anualmente com base em índices de inflação e legislação vigente.", "true", "economia", "FactChecks.br"),

    # Ciência e Meio Ambiente - Falsas
    ("A Terra é plana e as imagens de satélite são projeções geradas por computação gráfica da NASA.", "fake", "ciência", "Fake.br"),
    ("Eclipse solar recente foi causado por dispositivo artificial construído para bloquear radiação.", "fake", "ciência", "Fake.br"),
    ("Antenas de telecomunicação 5G emitem radiação ionizante capaz de destruir pássaros em voo.", "fake", "ciência", "Fake.br"),
    ("Mudanças climáticas são um boato criado para impedir o desenvolvimento industrial de países pobres.", "fake", "ciência", "FactChecks.br"),
    ("Vacas alimentadas com capim transgênico produzem leite fosforescente tóxico para consumo.", "fake", "ciência", "Fake.br"),

    # Ciência e Meio Ambiente - Verdadeiras
    ("A teoria da gravitação universal e a relatividade geral explicam a dinâmica dos corpos celestes.", "true", "ciência", "FactChecks.br"),
    ("O efeito estufa é um fenômeno natural essencial para manter a temperatura habitável do planeta.", "true", "ciência", "FactChecks.br"),
    ("A fotossíntese realizada por plantas e fitoplâncton consome dióxido de carbono e libera oxigênio.", "true", "ciência", "FactChecks.br"),
    ("Fósseis catalogados por paleontólogos evidenciam a evolução biológica e a extinção de espécies antigas.", "true", "ciência", "FactChecks.br"),
    ("A camada de ozônio na estratosfera filtra os raios ultravioleta mais prejudiciais emitidos pelo Sol.", "true", "ciência", "FactChecks.br"),

    # Política e Sociedade - Falsas
    ("Urnas eletrônicas contêm voto impresso secreto em chip escondido que altera os resultados.", "fake", "política", "FactChecks.br"),
    ("Constituição Federal de 1988 foi revogada por decisão monocrática de tribunal internacional.", "fake", "política", "Fake.br"),
    ("Censo do IBGE pede senhas bancárias e números de cartões de crédito dos moradores entrevistados.", "fake", "sociedade", "FactChecks.br"),
    ("Todas as eleições municipais foram canceladas definitivamente por portaria ministerial.", "fake", "política", "Fake.br"),
    ("Passaporte brasileiro deixará de ser aceito em viagens internacionais para a América do Sul.", "fake", "sociedade", "Fake.br"),

    # Política e Sociedade - Verdadeiras
    ("O voto no Brasil é obrigatório para cidadãos alfabetizados entre 18 e 70 anos de idade.", "true", "política", "FactChecks.br"),
    ("A Constituição de 1988 consagrou os direitos fundamentais e a tripartição dos poderes da República.", "true", "política", "FactChecks.br"),
    ("O Supremo Tribunal Federal é o guardião da Constituição e atua como corte de última instância.", "true", "política", "FactChecks.br"),
    ("O Código de Trânsito Brasileiro estabelece normas e penalidades para condutores em vias terrestres.", "true", "sociedade", "FactChecks.br"),
    ("A Lei de Acesso à Informação garante aos cidadãos o direito de obter dados de órgãos públicos.", "true", "política", "FactChecks.br"),

    # Pares Balanceados por Entidade (Economia, Sociedade, Saúde, Política, Ciência)
    # Banco Central / Pix
    ("Banco Central anunciou cobrança de taxa de quinze por cento sobre transferências via Pix entre pessoas físicas.", "fake", "economia", "FactChecks.br"),
    ("O Banco Central do Brasil lançou o sistema Pix para liquidação instantânea de pagamentos em 2020.", "true", "economia", "FactChecks.br"),
    ("Banco Central encerra operações de dinheiro físico e confisca cédulas em circulação a partir do próximo mês.", "fake", "economia", "FactChecks.br"),
    ("O Banco Central do Brasil define diretrizes para funcionamento e segurança de instituições financeiras no país.", "true", "economia", "FactChecks.br"),
    ("Receita Federal e Banco Central bloquearão contas com movimentações via Pix acima de duzentos reais sem declaração prévia.", "fake", "economia", "FactChecks.br"),
    ("O Banco Central não cobra taxa de transferências por Pix realizadas entre pessoas físicas para operações de rotina.", "true", "economia", "FactChecks.br"),

    # Bolsa Família / CadÚnico
    ("Beneficiários do Bolsa Família que receberem Pix de qualquer valor terão o benefício cancelado no mesmo dia.", "fake", "sociedade", "FactChecks.br"),
    ("O programa Bolsa Família prevê condicionalidades de saúde e educação como frequência escolar e acompanhamento nutricional.", "true", "sociedade", "FactChecks.br"),
    ("Governo federal liberou saque extraordinário de cinco mil reais no Bolsa Família mediante cadastro em link externo.", "fake", "sociedade", "FactChecks.br"),
    ("O Bolsa Família transfere renda mensalmente para famílias em situação de vulnerabilidade inscritas no Cadastro Único.", "true", "sociedade", "FactChecks.br"),
    ("Bolsa Família foi cancelado em todo o país após corte orçamentário aprovado pelo Congresso.", "fake", "sociedade", "FactChecks.br"),
    ("O Cadastro Único é gerido pelo governo federal em parceria com as prefeituras para identificar famílias de baixa renda.", "true", "sociedade", "FactChecks.br"),

    # Imunização e Vacinas
    ("Vacina contra poliomielite causa paralisia infantil nas crianças imunizadas e foi proibida em países desenvolvidos.", "fake", "saúde", "FactChecks.br"),
    ("A vacina contra a poliomielite erradicou a transmissão do poliovírus selvagem no território brasileiro desde 1989.", "true", "saúde", "FactChecks.br"),
    ("Vacina da febre amarela foi contaminada em laboratório e transmite a doença para adultos saudáveis.", "fake", "saúde", "FactChecks.br"),
    ("A vacinação contra a febre amarela é indicada e segura para residentes e viajantes que se deslocam para áreas de recomendação.", "true", "saúde", "FactChecks.br"),
    ("Vacina contra a dengue Qdenga teve registro cassado pela Anvisa por falta de comprovação de eficácia.", "fake", "saúde", "FactChecks.br"),
    ("A vacina contra dengue Qdenga foi aprovada pela Anvisa e incorporada ao Programa Nacional de Imunizações para faixas prioritárias.", "true", "saúde", "FactChecks.br"),
    ("Vacina da gripe comum altera o código genético humano e enfraquece a imunidade natural contra outras infecções.", "fake", "saúde", "FactChecks.br"),
    ("A vacina contra a gripe é atualizada anualmente com base nas cepas do vírus influenza em circulação.", "true", "saúde", "FactChecks.br"),
    ("Estudos científicos globais com milhões de crianças comprovaram a inexistência de relação entre vacinas e o desenvolvimento de autismo.", "true", "saúde", "FactChecks.br"),

    # Eleições e Urnas
    ("Tribunal Superior Eleitoral proibiu uso de caneta esferográfica azul na cabine de votação sob pena de anulação.", "fake", "política", "FactChecks.br"),
    ("O Tribunal Superior Eleitoral coordena a realização das eleições e a fiscalização de contas de campanhas partidárias.", "true", "política", "FactChecks.br"),
    ("As urnas eletrônicas brasileiras funcionam sem conexão à internet e imprimem o boletim de urna ao final da votação.", "true", "política", "FactChecks.br"),
    ("Se mais de cinquenta por cento dos votos forem nulos a eleição inteira é anulada e novo pleito é convocado.", "fake", "política", "FactChecks.br"),
    ("Os votos nulos e brancos não são considerados no cálculo dos votos válidos e não anulam a eleição.", "true", "política", "FactChecks.br"),

    # Tratamentos Médicos e Fisiologia
    ("Chá de casca de banana com canela cura diabetes e elimina a necessidade de aplicação de insulina em três dias.", "fake", "saúde", "FactChecks.br"),
    ("A diabetes mellitus é uma condição crônica controlada com acompanhamento médico, alimentação equilibrada, atividade física e medicamentos.", "true", "saúde", "FactChecks.br"),
    ("Água morna com limão em jejum alcaliniza o sangue e impede a proliferação de vírus e células de câncer.", "fake", "saúde", "FactChecks.br"),
    ("O organismo humano possui mecanismos fisiológicos e renais próprios que mantêm o pH sanguíneo estável entre 7,35 e 7,45.", "true", "saúde", "FactChecks.br"),
    ("Máscaras cirúrgicas e de proteção respiratória são seguras e amplamente utilizadas por profissionais de saúde há décadas sem causar hipóxia.", "true", "saúde", "FactChecks.br"),
    ("Infecções respiratórias virais afetam as células do trato respiratório e não são eliminadas por gargarejos com vinagre ou sal.", "true", "saúde", "FactChecks.br"),
    ("Ivermectina e hidroxicloroquina são comprovadamente eficazes para prevenir qualquer forma de dengue ou virose.", "fake", "saúde", "FactChecks.br"),
    ("A dengue é tratada principalmente com hidratação rigorosa e analgésicos adequados, sob orientação médica para evitar complicações.", "true", "saúde", "FactChecks.br"),
    ("Inalar vapor de álcool com eucalipto cura pneumonia e substitui internação hospitalar.", "fake", "saúde", "FactChecks.br"),
    ("A pneumonia bacteriana exige tratamento com antibióticos específicos prescritos por profissional de saúde.", "true", "saúde", "FactChecks.br"),

    # Meio Ambiente e Ciência
    ("Imagens de satélite da NASA e do INPE sobre o desmatamento na Amazônia são geradas artificialmente para prejudicar o agronegócio.", "fake", "ciência", "FactChecks.br"),
    ("O sistema Prodes do INPE utiliza imagens de satélites com sensoriamento remoto óptico para mapear o desmatamento na Amazônia Legal.", "true", "ciência", "FactChecks.br"),
    ("A radiação emitida por antenas de telefonia celular e 5G é não-ionizante e não possui energia suficiente para danificar o DNA celular.", "true", "ciência", "FactChecks.br"),
    ("Cientistas internacionais comprovaram que a Terra é plana e que fotos espaciais são ilustrações computadorizadas.", "fake", "ciência", "FactChecks.br"),
    ("Fotografias espaciais e a observação de constelações e eclipses comprovam a esfericidade do planeta Terra.", "true", "ciência", "FactChecks.br"),
    ("Tempestades e inundações recentes foram causadas artificialmente por transmissões da estação eletromagnética HAARP.", "fake", "ciência", "FactChecks.br"),
    ("Eventos climáticos extremos decorrem da dinâmica atmosférica, fatores oceânicos como El Niño e alterações no clima global.", "true", "ciência", "FactChecks.br"),

    # Instituições e Leis
    ("Militares assumiram o controle das cortes superiores após decreto extraordinário secreto do Ministério da Defesa.", "fake", "política", "FactChecks.br"),
    ("As Forças Armadas são instituições nacionais permanentes que atuam sob a autoridade suprema do Presidente da República e da Constituição.", "true", "política", "FactChecks.br"),
    ("Todos os cidadãos que utilizarem redes sociais sem cadastro governamental terão suas contas bancárias bloqueadas por lei emergencial.", "fake", "sociedade", "FactChecks.br"),
    ("A Lei Geral de Proteção de Dados (LGPD) garante aos cidadãos o controle e a privacidade de seus dados pessoais.", "true", "sociedade", "FactChecks.br"),
    ("Vacinas da infância causam autismo e transtornos de desenvolvimento devido a conservantes com mercúrio.", "fake", "saúde", "FactChecks.br"),
    ("Uso contínuo de máscaras faciais de proteção provoca hipóxia, asfixia celular e envenenamento por dióxido de carbono.", "fake", "saúde", "FactChecks.br"),
    ("Gargarejo com vinagre e sal destrói o vírus no trato respiratório superior antes que ele atinja os pulmões.", "fake", "saúde", "FactChecks.br"),
    ("Tribunal internacional em Haia revogou a Constituição Federal do Brasil e destituiu os três poderes.", "fake", "política", "FactChecks.br"),
    ("Antenas de tecnologia 5G emitem radiação perigosa que mata aves em pleno voo e transmite vírus biológicos.", "fake", "ciência", "FactChecks.br"),
    ("A Constituição de 1988 é a norma jurídica fundamental do Brasil e define a organização dos poderes Executivo, Legislativo e Judiciário.", "true", "política", "FactChecks.br"),
    ("Urnas eletrônicas realizam apuração em servidor secreto e foram programadas para desviar votos de candidatos.", "fake", "política", "FactChecks.br"),
]


def load_training_dataset(include_sample_facts: bool = True) -> List[TrainingSample]:
    """Carrega o corpus completo consolidado a partir das fontes brasileiras disponíveis."""
    samples: List[TrainingSample] = []

    # 1. Carrega amostras do Fake.br fixture
    if os.path.exists(FIXTURE_FAKEBR_PATH):
        with open(FIXTURE_FAKEBR_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lbl = row.get("label", "").lower().strip()
                if lbl in ["fake", "1"]:
                    clean_lbl = "fake"
                elif lbl in ["true", "0", "real"]:
                    clean_lbl = "true"
                else:
                    continue

                samples.append(TrainingSample(
                    text=row.get("text", "").strip(),
                    label=clean_lbl,
                    category=row.get("category", "geral"),
                    source="Fake.br (NILC/USP)",
                ))

    # 2. Carrega checagens de sample_facts.json
    if include_sample_facts and os.path.exists(SAMPLE_FACTS_PATH):
        with open(SAMPLE_FACTS_PATH, "r", encoding="utf-8") as f:
            facts = json.load(f)
            for item in facts:
                status = item.get("status", "").lower()
                if status == "contraditada":
                    label = "fake"
                elif status == "apoiada":
                    label = "true"
                else:
                    continue  # Pula inconclusivas no treino supervisionado binário

                samples.append(TrainingSample(
                    text=item.get("claim", "").strip(),
                    label=label,
                    category=item.get("category", "saúde"),
                    source=f"FactChecks.br ({item.get('publisher', 'Agência')})",
                ))

    # 3. Adiciona o corpus curado adicional
    for text, label, category, source in CURATED_CORPUS:
        samples.append(TrainingSample(
            text=text,
            label=label,
            category=category,
            source=source,
        ))

    return samples
