# Relatório de Treinamento e Avaliação do Modelo Classificador — EvidencIA

## 1. Resumo Geral de Performance
- **Amostras no Conjunto de Teste:** 27
- **Acurácia Global:** 66.67%
- **Macro F1-Score:** 65.92%

## 2. Matriz de Confusão
| | Predito: FALSO | Predito: VERDADEIRO |
|:---|:---:|:---:|
| **Real: FALSO** | 11 (Verdadeiro Positivo) | 3 (Falso Negativo) |
| **Real: VERDADEIRO** | 6 (Falso Positivo) | 7 (Verdadeiro Negativo) |

## 3. Métricas Detalhadas por Classe
| Classe | Precisão | Revocação (Recall) | F1-Score |
|:---|:---:|:---:|:---:|
| **Falso / Desinformação** | 64.7% | 78.6% | 71.0% |
| **Verdadeiro / Fato** | 70.0% | 53.8% | 60.9% |

## 4. Análise de Limiares de Aceitação (Curva de Decisão e Confiança)
> **Conceito de Governança:** O modelo adota abstenção por limiar de score; probabilidades não foram calibradas empiricamente. O limiar mínimo é $\tau$. Quando a confiança probabilística é inferior ao limiar estipulado, o modelo **absteve-se de emitir veredito unilateral** e encaminha a alegação para o modo *Evidence-First* (verificação manual por checagens oficiais rastreáveis).

| Limiar ($\tau$) | Predições Aceitas | Taxa de Aceitação (%) | Taxa de Abstenção (%) | Precisão nos Aceitos (%) | Taxa de Erro nos Aceitos (%) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **0.50** | 27 / 27 | 100.0% | 0.0% | **66.7%** | 33.3% |
| **0.55** | 22 / 27 | 81.5% | 18.5% | **72.7%** | 27.3% |
| **0.60** | 18 / 27 | 66.7% | 33.3% | **83.3%** | 16.7% |
| **0.65** | 10 / 27 | 37.0% | 63.0% | **90.0%** | 10.0% |
| **0.70** | 6 / 27 | 22.2% | 77.8% | **83.3%** | 16.7% |
| **0.75** | 3 / 27 | 11.1% | 88.9% | **100.0%** | 0.0% |
| **0.80** | 1 / 27 | 3.7% | 96.3% | **100.0%** | 0.0% |
| **0.85** | 1 / 27 | 3.7% | 96.3% | **100.0%** | 0.0% |
| **0.90** | 0 / 27 | 0.0% | 100.0% | **N/A** | N/A |

## 5. Recomendação Operacional para Produção
- **Limiar:** Deve ser escolhido em validação separada, de acordo com o custo do erro; não otimizar no conjunto de teste.
- **Limitação:** Rótulos são padrões do corpus local; as métricas não demonstram veracidade factual de alegações externas. Nenhuma taxa é definida quando zero predições são aceitas.

Protocolo: 112 treino / 27 teste, seed 42; corpus local de padrões linguísticos. Modelo entregue e avaliado é o mesmo; não houve retreinamento no teste.


## 6. Exportação solicitada em pickle (.plk)

`model.plk` contém o mesmo modelo de `model.json`, sem novo treinamento. A equivalência de inferência após carregar foi verificada nas 139 amostras do corpus. A extensão convencional para esse formato é `.pkl`; `.plk` atende ao nome solicitado.

Na pasta `backend`, com as classes Python do projeto disponíveis:

```python
import pickle
with open("ml/classifier/model.plk", "rb") as arquivo:
    modelo = pickle.load(arquivo)
resultado = modelo.predict("Texto da alegação em português.")
```

O runtime e o notebook continuam usando JSON. A exportação pickle requer as classes `ml.classifier` do projeto.
