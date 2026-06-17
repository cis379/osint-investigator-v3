import json
from pathlib import Path

base = Path(r"C:\Users\cis37\osint-investigator-v3\ontology_viz")

# Load data
with open(base / "ontology_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Load HTML
with open(base / "ontology.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace fetch block with inline data
fetch_start = "fetch('ontology_data.json')"
fetch_end = "});"

# Find and replace the entire fetch block
idx_start = html.index(fetch_start)
# Find the matching end - it's the second ");" after catch
search_from = html.index(".catch(", idx_start)
idx_end = html.index("});", search_from) + 3

old_block = html[idx_start:idx_end]
data_json = json.dumps(data, ensure_ascii=False)
new_block = f"graphData = {data_json};\ninitGraph();"

html = html[:idx_start] + new_block + html[idx_end:]

with open(base / "ontology.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Inlined {len(data_json):,} chars of JSON data into ontology.html")
print(f"Final HTML size: {len(html):,} chars")
