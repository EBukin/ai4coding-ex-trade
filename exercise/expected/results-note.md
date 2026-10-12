# Farm trade and farm support: what the results show

Draft note, written with an AI assistant from the files in `outputs/`.

**Who trades with whom (Python).** Farm trade among the 27 countries grew from USD 227 billion in 2000 to USD 730 billion in 2019 (sum of `outputs/data/bloc_trade.csv`). Trade inside the EU is the largest flow by far: USD 219 billion in 2019. Next come trade inside USMCA (USD 100 billion) and USMCA exports to East Asia (USD 47 billion). Mercosur exports to East Asia grew the fastest, from USD 2.7 billion to USD 43.9 billion (all from `outputs/tables/bloc_trade.csv`). Around 2010 East Asia overtook the EU as Mercosur's main market (`outputs/data/bloc_trade.csv`).

**Gravity model (R).** In the PPML gravity model, a 10% longer distance goes with about 5% less trade (elasticity -0.57). Neighbours trade about 110% more (contig 0.75). Pairs with a trade agreement trade about 85% more (rta 0.62). These are associations, not causal effects. A common language shows no clear link (p = 0.38). All four numbers are in `outputs/data/gravity_coefs.csv`.

**Subsidy pass-through (Stata).** The data are synthetic. The estimates match the true values: direct 0.105, indirect 0.238 through fertiliser, total 0.342 (true 0.10, 0.24, 0.34). The estimates are in `outputs/data/sem_effects.csv`.
