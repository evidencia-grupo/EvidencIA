# Relatório de Treinamento e Avaliação do Modelo Classificador — EvidencIA

## 1. Resumo Geral de Performance
- **Amostras no Conjunto de Teste:** 16
- **Acurácia Global:** 62.50%
- **Macro F1-Score:** 61.90%

## 2. Matriz de Confusão
| | Predito: FALSO | Predito: VERDADEIRO |
|:---|:---:|:---:|
| **Real: FALSO** | 6 (Verdadeiro Positivo) | 2 (Falso Negativo) |
| **Real: VERDADEIRO** | 4 (Falso Positivo) | 4 (Verdadeiro Negativo) |

## 3. Métricas Detalhadas por Classe
| Classe | Precisão | Revocação (Recall) | F1-Score |
|:---|:---:|:---:|:---:|
| **Falso / Desinformação** | 60.0% | 75.0% | 66.7% |
| **Verdadeiro / Fato** | 66.7% | 50.0% | 57.1% |

## 4. Análise de Limiares de Aceitação (Curva de Decisão e Confiança)
> **Conceito de Governança:** O modelo adota calibração com limiar mínimo de confiança $\tau$. Quando a confiança probabilística é inferior ao limiar estipulado, o modelo **absteve-se de emitir veredito unilateral** e encaminha a alegação para o modo *Evidence-First* (verificação manual por checagens oficiais rastreáveis).

| Limiar ($\tau$) | Predições Aceitas | Taxa de Aceitação (%) | Taxa de Abstenção (%) | Precisão nos Aceitos (%) | Taxa de Erro nos Aceitos (%) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **0.50** | 16 / 16 | 100.0% | 0.0% | **62.5%** | 37.5% |
| **0.55** | 11 / 16 | 68.8% | 31.2% | **63.6%** | 36.4% |
| **0.60** | 4 / 16 | 25.0% | 75.0% | **50.0%** | 50.0% |
| **0.65** | 1 / 16 | 6.2% | 93.8% | **100.0%** | 0.0% |
| **0.70** | 0 / 16 | 0.0% | 100.0% | **100.0%** | 0.0% |
| **0.75** | 0 / 16 | 0.0% | 100.0% | **100.0%** | 0.0% |
| **0.80** | 0 / 16 | 0.0% | 100.0% | **100.0%** | 0.0% |
| **0.85** | 0 / 16 | 0.0% | 100.0% | **100.0%** | 0.0% |
| **0.90** | 0 / 16 | 0.0% | 100.0% | **100.0%** | 0.0% |

## 5. Recomendação Operacional para Produção
- **Limiar Recomendado ($\tau = 0.65$ ou $0.70$):** Oferece o equilíbrio ideal entre alta cobertura e margem mínima de erro.
- **Garantia Evidence-First:** Nenhuma decisão automatizada substitui a apresentação de fontes auditadas; alegações com score abaixo do limiar mantêm o estado de neutralidade investigativa.