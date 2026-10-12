# Project name

## To do

- [ ] Write the purpose and the why in two sentences.
- [ ] Record where the raw data comes from: source, date, link.
- [ ] Set up the environment for your language.
- [ ] Make the first commit, with a message that says why.

Delete this section when every item is done.

## Purpose and why

What this project produces, and why it is needed. Two sentences.

## Who

| Role | Name | Contact |
|---|---|---|
| Lead | | |
| Contributors | | |

One-off or long-term: state which, and who maintains the project.

## How to run

1. Open this folder in Positron or VS Code.
2. Run the master script for your language in `code/`: `00_master.do`, `00_master.R` or `00_master.py`.
3. The master script rebuilds `data/clean/` and `outputs/` from `data/raw/`.

Delete `data/clean/` and `outputs/` contents, run the master script again, and you get the same results.

**Environment.** Stata: the master do-file installs the packages it needs. R: use `renv`. Python: use a project environment.

## Folder map

| Folder | Holds | Rule |
|---|---|---|
| `data/raw/` | Data as downloaded or received | Read-only. Never edit or overwrite. |
| `data/clean/` | Data after cleaning, ready for analysis | Made by code only |
| `code/` | Numbered scripts and one master script | The master script runs them all, in order |
| `outputs/figures/` | Charts | Made by code only |
| `outputs/tables/` | Tables | Made by code only |
| `outputs/data/` | Data behind figures, tables and indicators | Made by code only |
| `reports/` | Write-ups, notes, slides | Flexible |

The data moves in three stages, like an ETL pipeline: extract (`data/raw/`), transform (`data/clean/`), load (`outputs/`).

## Data sources

| File | Source | Date downloaded | Link | Licence |
|---|---|---|---|---|
| | | | | |

If the raw data lives outside this folder, for example on SharePoint, write the full path here and treat it as read-only.

## Log

Record who did what, when and why. Newest first.

| Date | Who | What | Why |
|---|---|---|---|
| | | Project created from the ai4coding template | |

## Licence and publishing (optional)

Fill this in before you share the project outside your team.

- **Code.** World Bank repositories use the MIT License plus the World Bank IGO Rider: <https://github.com/worldbank>.
- **Data.** World Bank datasets default to CC BY 4.0. Third-party data keeps its own licence: check it before you publish.
- **Reports.** World Bank publications carry the standard disclaimer: "The findings, interpretations, and conclusions expressed in this work do not necessarily reflect the views of The World Bank, its Board of Executive Directors, or the governments they represent."
- **Before you make code public,** contact the Open Source Program Office (OSPO), <github@worldbank.org>. Releases are cleared by the Legal Vice Presidency (LEG) and OSPO.
- **OSPO guidance:** <https://worldbank.github.io/ospo>. It opens only if your GitHub account is a member of the World Bank GitHub organization.
