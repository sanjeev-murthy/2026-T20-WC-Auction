import os
import glob
import pandas as pd

FOLDER = r"C:\Users\madha\Documents\2026-T20-WC-Auction\points_calc"  # change if needed
PLAYER_COL = "0"   # change if your column name is different
POINTS_COL = "1"   # change if your column name is different

all_files = glob.glob(os.path.join(FOLDER, "*.csv"))

dfs = []
for path in all_files:
    df = pd.read_csv(path)
    if PLAYER_COL in df.columns and POINTS_COL in df.columns:
        temp = df[[PLAYER_COL, POINTS_COL]]
        dfs.append(temp)
    else:
        print(f"Skipping {os.path.basename(path)} (missing columns)")

if not dfs:
    raise SystemExit("No valid CSVs found with required columns.")

combined = pd.concat(dfs, ignore_index=True)

combined[POINTS_COL] = combined[POINTS_COL].str.split(' ').str[0]
combined[POINTS_COL] = pd.to_numeric(combined[POINTS_COL], errors='coerce').fillna(0).astype(int)
combined[PLAYER_COL] = combined[PLAYER_COL].str.split('(').str[0]

# sum points per player
summary = combined.groupby(PLAYER_COL, as_index=False)[POINTS_COL].sum()

out_path = os.path.join(FOLDER, "temp.csv")
combined.to_csv(out_path, index=False)

out_path = os.path.join(FOLDER, "players_total_points.csv")
summary.to_csv(out_path, index=False)
print(f"Saved: {out_path}")
