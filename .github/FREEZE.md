# FREEZE — Descongelamento Formal de Caminhos Críticos

> **Status:** 🟢 DESCONGELADO  
> **Data de Descongelamento:** 2026-10-03  
> **Motivo:** Transição para Sprint 2 e homologação da Arquitetura Evidence-First ([ADR-006](../../documentation/docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md)).  
> **Issues Relacionadas:** #33 ([HU13] Evidence-First Schema) e #34 ([HU02] Descongelamento Formal e Remoção do Score Global).

---

## Histórico

Na Sprint 1 Foundation, os caminhos contendo medidores de veracidade (`score: 0–100`), componentes visuais de velocímetro (`Gauge.tsx`) e campos agregadores foram congelados para evitar acoplamento enquanto o pipeline de dados e evidências era estruturado.

Com a homologação formal dos contratos de dados Evidence-First, o congelamento foi formalmente encerrado.
O componente `Gauge` e os atributos `score` e `reliabilityScore` foram eliminados de ponta a ponta do projeto.
