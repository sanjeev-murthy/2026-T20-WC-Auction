import csv
import json
import os
import re

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "players_total_points.csv")
JSON_PATH = os.path.join(BASE_DIR, "..", "contestant_data.json")


def _norm_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name)  # drop country in parentheses
    name = re.sub(r"\s+", " ", name)
    return name.lower()


def _parse_points(value: str) -> str:
    # Handles formats like "143 Pts", "-9 Pts", "0"
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return m.group(0) if m else "0"


def load_points_map(csv_path: str) -> dict:
    points_map = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            name = row[0].strip()
            points = row[1] if len(row) > 1 else "0"
            points_map[_norm_name(name)] = _parse_points(points)
    return points_map


def update_json_points(json_path: str, points_map: dict) -> tuple[int, list[str]]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing = []
    updated = 0
    for owner, obj in data.items():
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
