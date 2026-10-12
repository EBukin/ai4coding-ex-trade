# farm-trade-support: build branch

This `dev` branch builds the example repository for the "AI for coding"
course: a small project on farm trade and farm support with
R, Python and Stata code, two dashboards and a seven-month Git history.

**The project and its history are made up for teaching.** The four analysts,
their commits and their dates are written in `_build/history/commits.py`
and replayed by a script. The trade data are real (FAOSTAT, CEPII); the
subsidy data are synthetic.

The learner project lives on `main`. The branches `r/gravity`,
`python/bloc-charts`, `stata/sem-passthrough`, `fix/trade-units`,
`fix/stata-root-check` and `shiny/dashboards` are part of its history. `dev` shares no commits with
them.

## What is here

- `_build/project/`: the final state of the learner project, outputs included.
- `_build/project/code/00_data_prep/prepare_data.py`: raw downloads to clean data. It is part of the learner project; see its README.
- `_build/project/data/raw/`: the two filtered extracts of the raw downloads. They are committed on `dev` only (force-added, because the project ignores `data/raw/`). The downloads themselves are not committed.
- `_build/history/commits.py`: commit-by-commit spec of the history.
- `_build/history/files/`: earlier versions of files, used by the spec.
  - `files/m13/`: `README.md`, `AGENTS.md` and `code/README.md` as they were at M13. The commits up to M13 are derived from these, so later edits in `_build/project/` leave them as they are.
  - `files/shiny/`: the dashboards as they were built, before they were adapted.
- History on GitHub is not rewritten: add new commits at the end of the spec, and check that the old commit hashes stay the same.
- `_build/build_history.py`: replays the spec into `main` and the feature branches.
- `_build/plans/`: plans for changes to the build.
- `_build/research/`: notes on data sources and tooling.

## Rebuild

With Python 3.11+ (with `pandas`) and Git:

```
cd _build/project
python code/00_data_prep/prepare_data.py   # clean data from data/raw/ (downloads if needed)
cd ../..
python _build/build_history.py             # replays the history into main and the branches
```

To rerun the analyses, run the three master scripts in `_build/project/`
(see its README) before building the history.
