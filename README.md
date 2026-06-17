# ⚽ FIFA World Cup 2026 · Player Physical Metrics

App interativo para análise dos dados físicos (EPTS) das seleções da Copa do Mundo 2026.

## Funcionalidades

- Upload de um ou mais CSVs no formato FIFA (separador `;`, decimais com vírgula)
- Contexto automático da partida (estádio, placar) e referência dos estádios
- Posições oficiais GK/DF/MF/FW das 32 seleções (filtro em todas as análises)
- **Benchmark de equipe** com totais absolutos, zonas Z4+Z5 (≥20 km/h) e Z5 (≥25 km/h),
  coeficiente de variação e mapas de quadrantes com bandeiras
- Perfil físico por resultado (vitória/empate/derrota) com teste de significância
- Análises por posição, z-score, eficiência de sprint, clustering, correlação e benchmark
- Relatório em PDF com resumo estatístico

## Referência científica

Bradley, P. S. (2024). *"Setting the Benchmark" Part 2: Contextualising the Physical
Demands of Teams in the FIFA World Cup Qatar 2022.* **Biology of Sport, 41(1), 271–278.**
https://doi.org/10.5114/biolsport.2024.131091

As análises de benchmark de equipe seguem a metodologia deste estudo.

## Como usar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```
