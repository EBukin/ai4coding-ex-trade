# farm-trade-support: build branch

This `dev` branch builds the example repository for exercise 1 of the
"AI for coding" course: a small project on farm trade and farm support with
R, Python and Stata code and a five-month Git history.

**The project and its history are made up for teaching.** The four analysts,
their commits and their dates are written in `_build/history/commits.py`
and replayed by a script. The trade data are real (FAOSTAT, CEPII); the
subsidy data are synthetic.

The learner project lives on `main`. The branches `r/gravity`,
`python/bloc-charts`, `stata/sem-passthrough`, `fix/trade-units` and
`fix/stata-root-check` are part of its history. `dev` shares no commits with
them.

## What is here

| Path | Holds |
|---|---|
| `_build/make_data.py` | Raw downloads to clean data (`project/data/clean/`) |
| `_build/raw/` | Filtered extracts of the raw downloads (the downloads themselves are not committed) |
| `_build/project/` | The final state of the learner project, outputs included |
| `_build/history/commits.py` | Commit-by-commit spec of the history |
| `_build/history/files/` | Earlier versions of files, used by the spec |
| `_build/build_history.py` | Replays the spec into `main` and the feature branches |
| `_build/research/` | Notes on data sources and tooling |
| `exercise/` | The exercise pages and the expected answers |

## Rebuild

From the repository root, with Python 3.11+ and Git:

```
python _build/make_data.py          # clean data from _build/raw/ (downloads if needed)
python _build/build_history.py      # replays the history into main and the branches
```

To rerun the analyses, run the three master scripts in `_build/project/`
(see its README) before building the history.
