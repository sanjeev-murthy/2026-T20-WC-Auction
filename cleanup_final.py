#!/usr/bin/env python3

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the FIRST occurrence of "// OFFICIAL ICC T20 WORLD CUP 2026 SCHEDULE"
# and build from scratch from line 820 onward

parts = content.split('</div>\n\n<script>')
if len(parts) >= 2:
    # Keep everything before the broken section
    before = parts[0] + '</div>'
    
    # Find where the REAL tournamentSchedule is defined
    after_parts = parts[1].split('const tournamentSchedule = [')
    
    # Get everything after the real tournamentSchedule declaration
    if len(after_parts) >= 2:
        schedule_part = 'const tournamentSchedule = [' + after_parts[-1]
    else:
        schedule_part = ''
    
    # Build the clean version
    clean_content = before + '''

<script>
// Load allPlayers from JSON
let allPlayers = [];
fetch('allPlayers.json')
    .then(r => {
        if (!r.ok) throw new Error('Failed to load allPlayers.json');
        return r.json();
    })
    .then(data => {
        allPlayers = data;
        console.log('Loaded ' + data.length + ' players from JSON');
    })
    .catch(err => {
        console.error('Could not load allPlayers.json:', err);
    });

// OFFICIAL ICC T20 WORLD CUP 2026 SCHEDULE
''' + schedule_part
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(clean_content)
    
    print("✅ Successfully rebuilt HTML!")
else:
    print("❌ Could not find section markers")
