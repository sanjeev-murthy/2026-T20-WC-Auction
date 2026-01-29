import json
import csv
from pathlib import Path

# Countries with complete expert analysis
COMPLETE_COUNTRIES = {
    "India",
    "Afghanistan", 
    "Namibia",
    "Netherlands",
    "Ireland",
    "New Zealand",
    "South Africa",
    "West Indies"
}

def get_price_range(price_str):
    """Convert price string like $22.00 to numeric value"""
    if not price_str or price_str == "":
        return 0.5
    try:
        return float(price_str.replace("$", "").strip())
    except:
        return 0.5

# Read CSV
csv_data = {}
with open('players_for_suggestions.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        country = row['Country'].strip()
        
        # Only process complete countries
        if country not in COMPLETE_COUNTRIES:
            continue
        
        player_name = row['PLAYER'].strip()
        role = row['ROLE '].strip()  # Note: 'ROLE ' has trailing space
        rating = row['Rating'].strip()
        price_target = get_price_range(row['Price Target'])
        analysis = row["Aakash's Expert Analysis"].strip()
        lot = row['Lot'].strip()
        
        if country not in csv_data:
            csv_data[country] = {}
        
        # Store by player name for easy lookup
        csv_data[country][player_name] = {
            "role": role,
            "rating": rating,
            "priceTarget": str(price_target),
            "analysis": analysis,
            "lot": f"Lot {lot}",
            "basePrice": "0.50" if price_target < 1 else "1.00"
        }

# Read existing JSON
with open('players_data_central.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# Separate players into two groups: complete countries and others
complete_country_players = {}
other_country_players = []

for player in json_data:
    country = player['country']
    if country in COMPLETE_COUNTRIES:
        if country not in complete_country_players:
            complete_country_players[country] = {}
        complete_country_players[country][player['name']] = player
    else:
        other_country_players.append(player)

# For each complete country, merge old and new data
updated_data = list(other_country_players)  # Start with non-complete countries

for country in COMPLETE_COUNTRIES:
    if country in csv_data:
        # Get old players for this country (for reference fields)
        old_players = complete_country_players.get(country, {})
        
        # For each player in CSV, create updated record
        for csv_player_name, csv_player_data in csv_data[country].items():
            # Check if player exists in old data
            if csv_player_name in old_players:
                # Merge: keep old fields, update with CSV data
                updated_player = old_players[csv_player_name].copy()
                updated_player.update(csv_player_data)
            else:
                # New player: create from scratch with required fields
                updated_player = {
                    "name": csv_player_name,
                    "country": country,
                    "squad": "GROUP A",  # Default squad
                    "role": csv_player_data["role"],
                    "rating": csv_player_data["rating"],
                    "priceTarget": csv_player_data["priceTarget"],
                    "analysis": csv_player_data["analysis"],
                    "espncricinfo": "https://www.espncricinfo.com/",  # Placeholder
                    "basePrice": csv_player_data["basePrice"],
                    "lot": csv_player_data["lot"],
                    "flagCode": ""  # Will be filled if available
                }
            
            updated_data.append(updated_player)

# Write back to JSON
with open('players_data_central.json', 'w', encoding='utf-8') as f:
    json.dump(updated_data, f, indent=2, ensure_ascii=False)

print(f"Updated players_data_central.json")
print(f"Updated countries: {', '.join(sorted(COMPLETE_COUNTRIES))}")
print(f"Total players in file: {len(updated_data)}")

# Summary of changes
print("\nSummary:")
for country in sorted(COMPLETE_COUNTRIES):
    old_count = len(complete_country_players.get(country, {}))
    new_count = len(csv_data.get(country, {}))
    print(f"  {country}: {old_count} → {new_count} players")
