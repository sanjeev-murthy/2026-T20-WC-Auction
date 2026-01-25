// Extract all players from allPlayers array in index.html
const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');

// Extract allPlayers array using regex
const match = html.match(/const allPlayers = \[([\s\S]*?)\];/);
if (!match) {
    console.error('Could not find allPlayers array');
    process.exit(1);
}

// Parse the array string
const arrayStr = '[' + match[1] + ']';
const allPlayers = eval(arrayStr);

// Create CSV
let csv = 'Name,Role,Country,Suggestion (Buy/Not Worth It/Bits and Pieces),Price Target\n';
allPlayers.forEach(player => {
    csv += `"${player.name}","${player.role}","${player.country}",,\n`;
});

fs.writeFileSync('players_for_suggestions.csv', csv);
console.log(`✅ Created players_for_suggestions.csv with ${allPlayers.length} players`);
