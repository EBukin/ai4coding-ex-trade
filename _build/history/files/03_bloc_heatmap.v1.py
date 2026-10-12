# Step 3: heatmap of who trades with whom in 2019.
# Rows are the exporting bloc, columns the importing bloc.
# Input:  outputs/data/bloc_trade.csv  (made by 01_bloc_trade.py)
# Output: outputs/figures/bloc_heatmap_2019.png

import matplotlib

matplotlib.use("Agg")  # draw to a file, no window
import matplotlib.pyplot as plt
import pandas as pd

year = 2019
bloc_trade = pd.read_csv("outputs/data/bloc_trade.csv")

# Keep one year and make a bloc-by-bloc table, in USD billions.
table = (
    bloc_trade[bloc_trade["year"] == year]
    .pivot(index="bloc_from", columns="bloc_to", values="trade_usd")
    .fillna(0)
    / 1e9
)

fig, ax = plt.subplots(figsize=(8, 6.5))
image = ax.imshow(table.values, cmap="Blues")

# Label rows and columns with the bloc names.
ax.set_xticks(range(len(table.columns)), labels=table.columns, rotation=30, ha="right")
ax.set_yticks(range(len(table.index)), labels=table.index)
ax.set_xlabel("Importing bloc")
ax.set_ylabel("Exporting bloc")

fig.colorbar(image, ax=ax, label="Farm trade (USD billions)")
ax.set_title(f"Farm trade between blocs, {year} (USD billions)")

fig.tight_layout()
fig.savefig(f"outputs/figures/bloc_heatmap_{year}.png", dpi=150)
plt.close(fig)
print(f"Saved outputs/figures/bloc_heatmap_{year}.png")
