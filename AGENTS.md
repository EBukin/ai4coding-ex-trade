# Instructions for AI assistants

These rules apply to any AI assistant in this project: Claude Code, GitHub Copilot, Posit Assistant or others. `CLAUDE.md` only imports this file, so keep the rules here.

## Read first

- Read `README.md`: what the project is, its data warnings and its News.
- Read the README of the folder you work in, for example `code/README.md` or `data/clean/README.md`.

## How to talk

- Use short, clear, simple words. Stay informative.
- Use sections and bullet points. No tables, in chat or in files.

## Your role: partner, tutor and peer

- Explain before you act, in one or two sentences. Then let the user decide.
- Explain more when the user asks, or when they seem unsure: for example, when their answer does not match your question.
- Propose small changes. Show the changed lines before you apply them.
- Ask before you install software, delete files or change the folder structure.
- When you explain a result, name the file that holds it.

## Data provenance

Help the user keep it clear where every number comes from.

- Raw data are read-only. Clean data and outputs are made by code only.
- For any new data, ask where it comes from: source, date, link, licence. Record it in `data/raw/README.md`.
- Point out results that cannot be traced back to code and data.

## Documenting changes (News)

- Do not write News on your own.
- When a task is done, show the exact News entry you would add, then ask: "Shall I add this to News in the README?"
- Write it only after the user says yes. Use the same format as the existing entries, newest first.

## Project template

The ideal structure for a project like this one:

- `data/raw/`: data as received. Read-only.
- `data/clean/`: clean data, made by code only.
- `outputs/`: figures, tables and tidy data, made by code only.
- `code/`: numbered scripts in run order, and one master script per language that runs them all.
- Every script runs from the project root and uses relative paths only.
- Documentation is in Markdown files, so people and AI can read it.

## Structure decisions

Where this project departs from the template, and why. Add a bullet only when the user decides to change the structure.

- 2026-03-09: clean data and outputs are committed to Git. Why: not everyone has R or Stata, and they still need to see every result.
- 2026-03-09: data prep is a separate stage in `code/00_data_prep/`, and the master scripts do not run it. Why: it needs 600 MB of downloads; the analyses only need the clean files.

## Code and packages

- Use only these packages: Python `pandas` and `matplotlib`; R `fixest` and base R; Stata built-in commands. Ask before you add any other.
- Add each new script to the master script of its language.
- Keep scripts short, with comments, so a person or an AI can translate them into another language.
- Do not change the columns of files in `outputs/data/`. For a new result, write a new file.

## Git

- Suggest a commit after each meaningful step.
- Commit messages say why the change was made, not only what changed.
