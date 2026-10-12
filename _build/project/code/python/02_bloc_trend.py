# Step 2: chart of farm trade between blocs over time.
# Input:  outputs/data/bloc_trade.csv  (made by 01_bloc_trade.py)
# Output: outputs/figures/bloc_trend.png

import matplotlib

matplotlib.use("Agg")  # draw to a file, no window
import matplotlib.pyplot as plt
import pandas as pd

bloc_trade = pd.read_csv("outputs/data/bloc_trade.csv")

# One label per pair of blocs, for example "EU -> USMCA".
bloc_trade["pair"] = bloc_trade["bloc_from"] + " -> " + bloc_trade["bloc_to"]


def plot_trend(ax, data):
    """Draw one line per bloc pair on the axes `ax`."""
    for pair, rows in data.groupby("pair"):
        ax.plot(rows["year"], rows["trade_usd"], label=pair)
    ax.set_xticks(range(2000, 2020, 5))
    ax.set_xlabel("Year")
    ax.set_ylabel("Trade (USD)")
    ax.ticklabel_format(axis="y", style="plain")  # show full numbers
    ax.legend(fontsize=7)


fig, ax = plt.subplots(figsize=(10, 6))
plot_trend(ax, bloc_trade)
ax.set_title("Farm trade betwen blocs")

fig.tight_layout()
fig.savefig("outputs/figures/bloc_trend.png", dpi=150)
plt.close(fig)
print("Saved outputs/figures/bloc_trend.png")
