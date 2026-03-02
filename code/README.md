# Code

- Number scripts in the order they run: `01_load`, `02_clean`, `03_analysis`, and so on.
- One master script per language runs all the others, in order: `00_master.do`, `00_master.R` or `00_master.py`.
- Delete the master scripts for languages you do not use.
- Use paths relative to the project folder.
