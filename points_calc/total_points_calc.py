import argparse
import csv
import glob
import json
import os
import re
import time

import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "players_total_points.csv")
JSON_PATH = os.path.join(BASE_DIR, "..", "contestant_data.json")

LOGIN_URL = "https://www.cricbattle.com/Account/LoginRegister"
TARGET_URL = (
    "https://fantasycricket.cricbattle.com/MyFantasy/Player-Scores-Breakdown"
    "?LeagueModel=SalaryCap&LeagueId=675295"
)
MATCH_DROPDOWN_ID = "ddlMatch"


def _norm_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name.lower()


def _parse_points(value: str) -> float:
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group(0)) if m else 0.0


def _format_points(value: float) -> str:
    if value.is_integer():
        return f"{int(value)} Pts"
    return f"{value} Pts"


def scrape_matches(mode: str, selected_matches: list[str]) -> None:
    try:
        from io import StringIO
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.common.exceptions import NoSuchElementException
    except ImportError as exc:
        raise SystemExit(
            "Missing selenium/webdriver_manager. Install dependencies before scraping."
        ) from exc

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(LOGIN_URL)
        print("\n" + "=" * 50)
        print("ACTION REQUIRED: Please log in manually in the browser.")
        input("Press ENTER here once you are logged in...")
        print("=" * 50 + "\n")

        print(f"Navigating to: {TARGET_URL}")
        driver.get(TARGET_URL)
        time.sleep(5)

        try:
            select_element = driver.find_element(By.ID, MATCH_DROPDOWN_ID)
            dropdown = Select(select_element)
            all_options = dropdown.options
            print(f"Found dropdown with {len(all_options)} options.")
        except NoSuchElementException:
            print(f"ERROR: Could not find dropdown with ID '{MATCH_DROPDOWN_ID}'.")
            return

        master_data = []
        for option in all_options:
            match_name = option.text.strip()
            if match_name == "" or "Select" in match_name:
                continue
            if mode == "selected" and match_name not in selected_matches:
                continue

            print(f"Processing: {match_name}...")
            dropdown.select_by_visible_text(match_name)
            time.sleep(4)

            try:
                page_html = driver.page_source
                tables = pd.read_html(StringIO(page_html))
                if not tables:
                    print("  -> No table found for this match.")
                    continue

                df = max(tables, key=len)
                df["Match_Name"] = match_name
                master_data.append(df)
                print(f"  -> Extracted {len(df)} rows.")

                safe_name = "".join(
                    ch if ch.isalnum() or ch in (" ", "-", "_") else "_" for ch in match_name
                ).strip()
                per_match_filename = os.path.join(BASE_DIR, f"match_scores_{safe_name}.csv")
                df.to_csv(per_match_filename, index=False)
                print(f"  -> Saved match file: {per_match_filename}")
            except Exception as exc:
                print(f"  -> Error reading table: {exc}")

        if master_data:
            print("\nConsolidating data...")
            final_df = pd.concat(master_data, ignore_index=True)
            filename = os.path.join(BASE_DIR, "all_matches_scores.csv")
            final_df.to_csv(filename, index=False)
            print(f"SUCCESS! Saved {len(final_df)} total rows to '{filename}'")
        else:
            print("No data was extracted. Check your match names or dropdown ID.")
    finally:
        driver.quit()


def build_players_total_points() -> None:
    match_files = glob.glob(os.path.join(BASE_DIR, "match_scores_*.csv"))
    if not match_files:
        raise SystemExit(f"No match CSVs found in {BASE_DIR}")

    dfs = []
    for path in match_files:
        df = pd.read_csv(path)
        if "0" not in df.columns or "1" not in df.columns:
            print(f"Skipping {os.path.basename(path)} (missing columns)")
            continue
        df = df[["0", "1"]].copy()
        # Remove country names in parentheses from player names
        df["0"] = df["0"].astype(str).str.replace(r"\s*\([^)]*\)\s*", " ", regex=True)
        df["0"] = df["0"].str.replace(r"\s+", " ", regex=True).str.strip()
        df["1"] = df["1"].apply(_parse_points)
        dfs.append(df)

    if not dfs:
        raise SystemExit("No valid match CSVs found with required columns.")

    combined = pd.concat(dfs, ignore_index=True)
    summary = combined.groupby("0", as_index=False)["1"].sum()
    summary["1"] = summary["1"].apply(_format_points)

    summary.to_csv(CSV_PATH, index=False)
    print(f"Saved: {CSV_PATH}")


def load_points_map(csv_path: str) -> dict:
    points_map = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            name = row[0].strip()
            points = row[1] if len(row) > 1 else "0"
            points_map[_norm_name(name)] = str(int(_parse_points(points)))
    return points_map


def update_json_points(json_path: str, points_map: dict) -> tuple[int, list[str]]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing = []
    updated = 0
    for _, obj in data.items():
        squad = obj.get("squad") or []
        for player in squad:
            name = player.get("name", "")
            key = _norm_name(name)
            if key in points_map:
                player["points"] = points_map[key]
                updated += 1
            else:
                missing.append(name)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    return updated, missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape, aggregate points, and update JSON.")
    parser.add_argument("--no-scrape", action="store_true", help="Skip web scraping step.")
    parser.add_argument("--no-calc", action="store_true", help="Skip points aggregation step.")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON update step.")
    parser.add_argument("--mode", choices=["all", "selected"], default="all")
    parser.add_argument("--selected", nargs="*", default=[], help="Match names for selected mode.")
    args = parser.parse_args()

    if not args.no_scrape:
        scrape_matches(args.mode, args.selected)

    if not args.no_calc:
        build_players_total_points()

    if not args.no_json:
        if not os.path.exists(CSV_PATH):
            raise SystemExit(f"CSV not found: {CSV_PATH}")
        if not os.path.exists(JSON_PATH):
            raise SystemExit(f"JSON not found: {JSON_PATH}")
        points_map = load_points_map(CSV_PATH)
        updated, missing = update_json_points(JSON_PATH, points_map)
        print(f"Updated {updated} player points in {JSON_PATH}")
        if missing:
            print(f"Missing {len(missing)} players from CSV (showing first 25):")
            for name in missing[:25]:
                print(f"- {name}")


if __name__ == "__main__":
    main()
