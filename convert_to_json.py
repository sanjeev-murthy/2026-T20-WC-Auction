import json
import re

# Read the JS file
with open('allPlayers-updated.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove 'const allPlayers = ' from beginning and '];' from end
content = content.replace('const allPlayers = ', '')
if content.strip().endswith('];'):
    content = content.strip()[:-2] + ']'

# Remove comments
content = re.sub(r'//\s*\w+.*\n', '\n', content)

# Replace unquoted keys with quoted keys - match pattern like "name:" or "role:" etc
content = re.sub(r'(\w+):', r'"\1":', content)

try:
    # Parse the JSON
    data = json.loads(content)
    
    # Write formatted JSON
    with open('allPlayers-updated.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully converted! Created JSON with {len(data)} players")
    
except json.JSONDecodeError as e:
    print(f"❌ JSON Parse Error: {e}")
    print(f"At line {e.lineno}, col {e.colno}")
except Exception as e:
    print(f"❌ Error: {e}")
