# %%
from IPython.display import display

from consts import ROOT
from loader import load_distances_mst, load_locations_mst, load_orders

# %%
DATA_PATH = ROOT / "data" / "raw" / "medium_dataset.xlsx"
df_locations = load_locations_mst(DATA_PATH)
df_distances = load_distances_mst(DATA_PATH)
df_orders = load_orders(DATA_PATH)

# %%
display(df_locations)
display(df_distances)
display(df_orders)

# %%
