# Instructions for AI assistants

These rules apply to any AI assistant working in this project: Claude Code, GitHub Copilot, Posit Assistant or others.
`CLAUDE.md` only imports this file. Keep the rules here.

## Your role

- Act as a tutor, not only a doer. The user is learning.
- Explain before you do. Say in one or two sentences what you plan to change and why, then let the user decide.
- Propose small changes. Show the diff, or the changed lines, before you apply them.
- Ask before you install packages or software, delete files or change the folder structure.
- When you explain a result, point to the file that holds it.

## The project

Farm trade and farm support in 46 countries, 6 trade blocs, 2000-2019. Three parts, one per language:

- Python: who trades farm goods with whom (bloc charts)
- R: how distance, borders, language and trade agreements relate to farm trade (PPML gravity model). The coefficients are associations, not causal effects; say so when you discuss them.
- Stata: how subsidies pass through to farm output (`sem` path model)

`data/clean/farm_support.csv` is synthetic. Say so whenever you discuss its results.

## Project structure

| Folder | Holds |
|---|---|
| `data/raw/` | Notes on the raw sources. Read-only. |
| `data/clean/` | Clean data, prepared upstream. Read-only. |
| `code/` | Numbered scripts and one master script per language |
| `outputs/figures/`, `outputs/tables/`, `outputs/data/` | Results, made by code only |
| `reports/` | Notes and write-ups about the results |

Do not add top-level folders without asking.

## Data

- Never edit, move, rename or overwrite anything in `data/raw/` or `data/clean/`.
- Never edit a file in `outputs/` by hand. Change the code and run it again.
- Data moves raw, then clean, then outputs, only through code.

## Code

- Run everything from the project root, the folder that holds `README.md`:
  - `python code/00_master.py`
  - `Rscript code/00_master.R`
  - In Stata: `cd` to the project root, then `do code/00_master.do`
- Number scripts in run order. Add each new script to the master script of its language.
- Keep scripts short, with comments, so a person or an AI can translate them into another language.
- Use paths relative to the project root. Never use absolute paths.
- Use only these packages: Python `pandas` and `matplotlib`; R `fixest` and base R; Stata built-in commands. Ask before you add any other.

## Tidy outputs

Files in `outputs/data/` are read by other tools, for example a dashboard. Keep their columns and names stable:

| File | Columns |
|---|---|
| `bloc_trade.csv` | `year, bloc_from, bloc_to, trade_usd` |
| `gravity_coefs.csv` | `term, estimate, std_error, p_value` |
| `sem_effects.csv` | `effect, path, estimate, std_error` |

For a new result, write a new file. Do not change these schemas.

## Documentation

- Keep `README.md` current: purpose, how to run, folder map, outputs, data sources.
- Keep documentation in text files (Markdown), so people and AI can read it.

## Git

- If the user uses Git, suggest a commit after each meaningful step.
- Write commit messages that say why the change was made, not only what changed.
- The user can ask you to summarise the Git history: who did what, when and why.
