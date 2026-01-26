with open('allPlayers-updated.js', 'w', encoding='utf-8') as f:
    f.write("""let allPlayers = [];

// Load player data from JSON file
fetch('allPlayers-updated.json')
  .then(response => {
    if (!response.ok) {
      throw new Error(`Failed to load allPlayers-updated.json: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    allPlayers = data;
    console.log(`✅ Loaded ${data.length} players from allPlayers-updated.json`);
  })
  .catch(error => {
    console.error('❌ Error loading player data:', error);
  });
""")

print("✅ Updated allPlayers-updated.js to load from JSON")
