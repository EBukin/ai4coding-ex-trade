# Master script for the Python part of the project.
# Run it from the project root folder:
#     python code/python/00_master.py
# It runs the numbered Python scripts below, in order.

import runpy
from pathlib import Path

# The Python scripts, in the order they run.
scripts = [
    "code/python/01_bloc_trade.py",    # bloc-to-bloc trade by year
    "code/python/02_bloc_trend.py",    # chart: trade between blocs over time
    "code/python/03_bloc_heatmap.py",  # chart: who trades with whom in 2019
]

# Make sure the output folders exist.
for folder in ["outputs/data", "outputs/tables", "outputs/figures"]:
    Path(folder).mkdir(parents=True, exist_ok=True)

for script in scripts:
    print("Running", script)
    runpy.run_path(script, run_name="__main__")

print("Done. Results are in outputs/.")
