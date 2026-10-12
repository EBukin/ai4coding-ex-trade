# Instructions for AI assistants

These rules apply to any AI assistant working in this project: Claude Code, GitHub Copilot, Posit Assistant or others.
`CLAUDE.md` only imports this file. Keep the rules here.

## Your role

- Act as a tutor, not only a doer. Explain each step in one or two sentences, then let the user decide.
- Keep changes small. Prefer the simplest solution that works.
- Ask before you delete files, install software or change the folder structure.

## Project structure

| Folder | Holds |
|---|---|
| `data/raw/` | Data as received. Read-only. |
| `data/clean/` | Cleaned data, made by code only |
| `code/` | Numbered scripts and one master script per language |
| `outputs/figures/`, `outputs/tables/`, `outputs/data/` | Results, made by code only |
| `reports/` | Write-ups |

Do not add top-level folders without asking.

## Data

- Never edit, move, rename or overwrite anything in `data/raw/`, or in an external raw-data path listed in `README.md`.
- Data moves raw → clean → outputs, only through code. Never edit a file in `data/clean/` or `outputs/` by hand.
- Record every new raw file in `README.md` (Data sources): source, date, link, licence.
- Aim for clean data in long format: one row per observation, with variable names and labels in separate tables.

## Code

- Number scripts in run order: `01_load.do`, `02_clean.do`, `03_analysis.do`, and so on.
- The master script (`code/00_master.do`, `00_master.R` or `00_master.py`) runs every script in order. Add each new script to it.
- Use paths relative to the project folder. Never use absolute paths to files inside the project.
- Running the master script from scratch must rebuild `data/clean/` and `outputs/`.
- Environments: Stata installs its packages in the master do-file; R uses `renv`; Python uses a project environment.

## Documentation

- Keep `README.md` current: purpose, how to run, folder map, data sources.
- After each meaningful change, add a row to the Log in `README.md`: date, who, what, why.
- Keep documentation in text files (Markdown), so people and AI can read it.

## Git

- If the project uses Git, commit after each meaningful step.
- Write commit messages that say why the change was made, not only what changed.
- Never commit data that must stay private. Check `.gitignore` first.
