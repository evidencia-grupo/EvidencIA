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
> **Conceito de Governança:** O modelo adota calibração com limiar mínimo de confiança $\tau$. Quando a confiança probabilística é inferior ao limiar estipulado, o modelo **absteve-se de emitir veredito unilateral** e encaminha a alegação para o modo *Evidence-First* (verificação manual por checagens oficiais rastreáveis).

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
| **0.90** | 0 / 27 | 0.0% | 100.0% | **100.0%** | 0.0% |

## 5. Recomendação Operacional para Produção
- **Limiar Recomendado ($\tau = 0.65$ ou $0.70$):** Oferece o equilíbrio ideal entre alta cobertura e margem mínima de erro.
- **Garantia Evidence-First:** Nenhuma decisão automatizada substitui a apresentação de fontes auditadas; alegações com score abaixo do limiar mantêm o estado de neutralidade investigativa.