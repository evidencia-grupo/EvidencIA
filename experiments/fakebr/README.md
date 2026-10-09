# Entrega de IA - EvidencIA

Pacote acadêmico preparado em **09/10/2026**, para a pasta do grupo no canal
**2_First Challenge** do Teams. O experimento foi reproduzido e incorporado em `experiments/fakebr`. Contém modelo, notebook, avaliação, documentação e código de reprodução. A aplicação e seus testes ficam nas demais pastas do repositório.

## Arquivos principais

- `avaliacao_modelo.ipynb`: notebook executado, com treinamento, inferência,
  comparação de modelos, métricas, abstenção, gráficos e análise de limitações.
- `models/modelo_treinado.pkl`: TF-IDF, regressão logística, calibrador sigmoid,
  limiar, proteção mínima de vocabulário e metadados do experimento.
- `relatorio_tecnico.md`: relatório para leitura e entrega.
- `relatorio_tecnico.md`: versão editável do relatório.
- `results/`: métricas completas, predições do teste, diagnóstico local,
  identificadores das partições e integridade do pacote.
- `source/`: implementação independente e versão de referência do classificador.
- `requirements-lock.txt`: versões usadas nesta execução (Python 3.12).

O modelo entregue foi ajustado em 4.312 notícias, selecionado com 1.082 notícias
e calibrado com outras 717. As 1.088 notícias de teste não participaram do treino,
da seleção, da calibração nem da escolha do limiar. Não houve retreino no teste.

## Executar

Descompacte o ZIP por completo. Use **Python 3.12**; o ambiente medido foi 3.12.14.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m ipykernel install --user --name evidencia-ia --display-name "EvidencIA IA"
```

Abra `avaliacao_modelo.ipynb` no VS Code/Jupyter e selecione esse kernel.
Execute todas as células em ordem. O notebook já inclui as saídas da execução
validada. O código de treinamento também pode ser executado diretamente:

```bash
python source/experiment.py
```

O primeiro treinamento baixa a revisão fixada do corpus oficial Fake.br
(aproximadamente 32 MB), confere SHA-256 e usa apenas a versão com comprimento
normalizado. É necessária internet para obter os dados; **carregar e executar o
modelo salvo não exige o download do corpus**. Não incluímos artigos integrais
no ZIP, pois o snapshot inspecionado não contém licença explícita de redistribuição.
O código e o manifesto permitem recuperar os mesmos dados diretamente da fonte.

Inferência independente:

```python
from pathlib import Path
import pickle
from source.experiment import predict_bundle

with Path("models/modelo_treinado.pkl").open("rb") as file:
    model = pickle.load(file)  # somente o artefato confiável deste pacote
print(predict_bundle(model, ["Texto de uma notícia para análise linguística."]))
```

## O que os resultados significam

Os rótulos `fake` e `true` são os rótulos históricos **das notícias do corpus**.
O modelo aprende regularidades linguísticas desse conjunto; sua probabilidade
não é prova de verdade factual e não é score de veracidade de vídeo. O modelo
não foi treinado para decidir se uma evidência apoia ou contradiz uma fala.

Respostas inconclusivas da aplicação também dependem de fontes e configuração.
O relatório registra ausência de índice e chave de busca no ambiente local,
provedor `mock` e incompatibilidade entre o modelo Ollama configurado e instalado.
A configuração online não foi inspecionada. O diagnóstico é histórico (revisão 0ffe395). Use `backend/.venv/bin/python scripts/check_readiness.py --check-services` na raiz da aplicação para verificar o ambiente atual. O experimento mantém a política de evidências e permanece uma avaliação de notícias, com inferência offline.

O arquivo `models/modelo_treinado.plk` contém os mesmos bytes de `modelo_treinado.pkl`, conforme a extensão solicitada. A reprodução não lê credenciais nem envia notícias para APIs.

## Integração e validação

Os testes do pacote executam com `python -m unittest source.test_experiment -v` nesta pasta. O corpus bruto não é republicado. O notebook aceita execução na raiz do repositório ou nesta pasta. A submissão ao Teams não foi executada.
