import argparse
import csv
import json
import os
import re
import time

import pandas as pd

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "players_total_points.csv")
JSON_PATH = os.path.join(BASE_DIR, "..", "contestant_data.json")

LOGIN_URL = "https://www.cricbattle.com/Account/LoginRegister"
RANKING_URL = (
    "https://fantasycricket.cricbattle.com/MyFantasy/League-Players-Ranking"
    "?LeagueModel=SalaryCap&LeagueId=675295&TournamentId=13357"
)


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


def scrape_player_rankings() -> None:
    try:
        from io import StringIO
        from selenium import webdriver
        from selenium.webdriver.common.by import By
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

        print(f"Navigating to: {RANKING_URL}")
        driver.get(RANKING_URL)
        time.sleep(5)

        page_html = driver.page_source
        tables = pd.read_html(StringIO(page_html))
        if not tables:
            raise SystemExit("No table found on rankings page.")

        df = max(tables, key=len)
        print(f"Found {len(df)} players in rankings.")
        print(f"Columns: {df.columns.tolist()}")

        cols = df.columns.tolist()
        name_col = cols[1] if len(cols) > 1 else cols[0]

        points_col = None
        for col in cols:
            if "total" in str(col).lower():
                points_col = col
                break
        if points_col is None:
            points_col = cols[-1]

        print(f"Using name column: {name_col}, points column: {points_col}")

        df[name_col] = df[name_col].astype(str).str.replace(r"\s*\([^)]*\)\s*", " ", regex=True)
        df[name_col] = df[name_col].str.replace(r"\s+", " ", regex=True).str.strip()
        df[points_col] = df[points_col].apply(_parse_points)

        result_df = df[[name_col, points_col]].copy()
        result_df.columns = ["Player", "Points"]
        result_df["Points"] = result_df["Points"].apply(_format_points)

        result_df.to_csv(CSV_PATH, index=False)
        print(f"Saved: {CSV_PATH}")
    finally:
        driver.quit()


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
    parser = argparse.ArgumentParser(description="Scrape player rankings and update JSON.")
    parser.add_argument("--no-scrape", action="store_true", help="Skip web scraping step.")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON update step.")
    args = parser.parse_args()

    if not args.no_scrape:
        scrape_player_rankings()

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
