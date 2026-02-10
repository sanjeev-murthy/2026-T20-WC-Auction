import os
import glob
import pandas as pd

FOLDER = r"C:\Users\madha\Documents\Auctions_Code"  # change if needed
PLAYER_COL = "0"   # change if your column name is different
POINTS_COL = "1"   # change if your column name is different

all_files = glob.glob(os.path.join(FOLDER, "*.csv"))

dfs = []
for path in all_files:
    df = pd.read_csv(path)
    if PLAYER_COL in df.columns and POINTS_COL in df.columns:
        dfs.append(df[[PLAYER_COL, POINTS_COL]])
    else:
        print(f"Skipping {os.path.basename(path)} (missing columns)")

if not dfs:
    raise SystemExit("No valid CSVs found with required columns.")

combined = pd.concat(dfs, ignore_index=True)

# sum points per player
summary = combined.groupby(PLAYER_COL, as_index=False)[POINTS_COL].sum()

out_path = os.path.join(FOLDER, "players_total_points.csv")
summary.to_csv(out_path, index=False)
print(f"Saved: {out_path}")
