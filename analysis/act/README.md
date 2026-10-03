# Ferramenta de Analise Estatistica e Metricas — Fase CBL Act

## Visao Geral

Este diretorio contem a ferramenta de calculo e sumarizacao deterministica das metricas comportamentais (M1 a M9) definidas no protocolo experimental da fase Act do projeto **EvidencIA**.

O script foi desenvolvido estritamente com a **biblioteca padrao do Python** (`stdlib only`), garantindo portabilidade absoluta, zero dependencia de bibliotecas pesadas (sem pandas, sem numpy, sem scipy) e execucao reproduzivel em qualquer estacao de trabalho.

---

## Requisitos de Execucao

- Python 3.10 ou superior.
- Nenhuma dependencia externa e necessaria para o script principal `compute_metrics.py`.
- Para executar os testes automatizados da suite de analise: `pytest >= 7.0`.

---

## Estrutura do Diretorio

```text
analysis/act/
├── README.md                          # Este documento explicativo
├── compute_metrics.py                 # Script CLI deterministico (stdlib only)
├── .gitignore                         # Bloqueio de dados reais de participantes e outputs
├── fixtures/
│   ├── synthetic_ground_truth.json    # Verdade-terreno sintetica ("synthetic": true)
│   └── synthetic_sessions.jsonl       # Sessoes sinteticas anotadas ("synthetic": true)
├── out/
│   ├── .gitkeep                       # Preserva diretorio de output no Git
│   └── summary.json                   # Output oficial gerado deterministamente
└── tests/
    └── test_compute_metrics.py        # 14 testes com valores calculados a mao
```

---

## Instrucoes de Uso da CLI

Para processar sessoes exportadas e calcular o sumario estatistico completo:

```bash
python analysis/act/compute_metrics.py \
  --sessions <caminho_arquivo_ou_pasta_jsonl> \
  --ground-truth <caminho_ground_truth.json> \
  --out analysis/act/out/summary.json \
  --seed 42 \
  --n-bootstraps 10000
```

### Argumentos da Linha de Comando:
- `--sessions`: Caminho para um arquivo `.jsonl` de sessao ou diretorio contendo multiplos arquivos `.jsonl`.
- `--ground-truth`: Caminho para o arquivo JSON contendo o mapeamento de verdade-terreno dos itens (`item_id` -> `claims` -> `verdict`).
- `--out`: Caminho de destino para gravacao do relatorio sumarizado `summary.json` (padrao: `analysis/act/out/summary.json`).
- `--seed`: Semente pseudoaleatoria inteira para inicializar o gerador de bootstrap (padrao: `42`).
- `--n-bootstraps`: Quantidade de reamostragens bootstrap nao parametricas para estimativa dos intervalos de confianca a 95% (padrao: `10000`).

---

## Saida e Hash de Integridade (SHA-256)

Ao concluir a execucao, o script:
1. Valida cada linha pelo contrato de schema e sanitizacao (descartando e contabilizando rejeicoes).
2. Computa M1 a M9 por participante e por condicao (A vs. B).
3. Estima intervalos de confianca a 95% via bootstrap percentilico.
4. Gera o arquivo `summary.json` com chaves ordenadas (`sort_keys=True`).
5. Emite no console a impressao padronizada do hash de integridade:
   ```text
   summary_sha256: sha256:<hex_digest_de_64_caracteres>
   ```

---

## Execucao dos Testes Automatizados

Para rodar a suite de testes com valores calculados a mao:

```bash
python -m pytest analysis/act/tests -q
```
