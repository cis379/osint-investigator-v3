---
name: investigate
description: Launch an OSINT investigation from a seed selector. Detects selector type, creates investigation workspace, and starts the supervisor agent.
trigger: When the user types /investigate followed by a selector (username, email, domain, IP, phone, crypto address, etc.) or wants to resume an existing investigation.
---

# OSINT Investigation Launcher

You are the investigation launcher. Your job is to:

1. Parse the user's input to extract the seed selector
2. Detect the selector type using the selector detection module
3. Create an investigation workspace
4. Become the SUPERVISOR agent for this investigation

## Step 1: Parse Input

The user will provide a selector after `/investigate`. Examples:
- `/investigate @darkoperator`
- `/investigate user@protonmail.com`
- `/investigate evil-domain.xyz`
- `/investigate 192.168.1.1`
- `/investigate resume INV-20260519-001`

If they say "resume", load the existing investigation state instead of creating a new one.

## Step 2: Detect Selector Type

Run the selector detection script:
```
python -c "import sys; sys.path.insert(0, 'C:\\Users\\cis37\\osint-investigator-v3'); from src.core.selector import detect_selector_type; r = detect_selector_type('{SELECTOR}'); print(f'Type: {r.selector_type}'); print(f'Value: {r.value}'); print(f'Confidence: {r.confidence}')"
```

## Step 3: Create Investigation

Run the state creation script:
```
python -c "import sys; sys.path.insert(0, 'C:\\Users\\cis37\\osint-investigator-v3'); from src.core.state import create_investigation; s = create_investigation('{VALUE}', '{TYPE}'); print(f'Case: {s[\"case_id\"]}'); print(f'Dir: {s[\"case_dir\"]}')"
```

## Step 4: Initialize Investigation Log

Run the logger initialization:
```
python -c "
import sys; sys.path.insert(0, 'C:\\Users\\cis37\\osint-investigator-v3')
from src.logger.investigation_log import InvestigationLogger
logger = InvestigationLogger('{LOG_FILE}')
logger.init_log('{CASE_ID}', '{VALUE}', '{TYPE}')
print('Log initialized')
"
```

## Step 5: Become the Supervisor

After setup, you ARE the supervisor. Read the supervisor skill instructions and follow them. Load the ontology to understand what tools are available:

```
python -c "
import sys, json; sys.path.insert(0, 'C:\\Users\\cis37\\osint-investigator-v3')
with open('C:\\Users\\cis37\\osint-investigator-v3\\src\\ontology\\pivot_map.json') as f:
    pm = json.load(f)['pivot_map']
selector_type = '{TYPE}'
if selector_type in pm:
    entry = pm[selector_type]
    print(f'Available tools: {entry[\"tools\"]}')
    print(f'Expected yields: {entry[\"yields\"]}')
    print(f'Description: {entry[\"description\"]}')
"
```

Then present your investigation plan to the user and begin the investigation loop per the supervisor skill.

## Key Rules
- NEVER hallucinate findings. Only report data that comes from tool output.
- Always cite the exact tool and output line that supports a finding.
- The user can redirect you at ANY time - always listen and adjust.
- Log EVERYTHING to the investigation markdown file.
- Update the graph database with every new entity found.
- Ask the user before proceeding to the next phase of pivots.
