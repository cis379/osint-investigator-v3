from datetime import datetime, timezone
from pathlib import Path


class InvestigationLogger:
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.step_count = 0

    def init_log(self, case_id: str, seed_value: str, seed_type: str):
        content = f"""# Investigation Log: {case_id}
## Seed: `{seed_value}` (type: {seed_type})
## Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
## Status: IN PROGRESS

---

"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(content)

    def log_step(self, title: str, content: str):
        self.step_count += 1
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        entry = f"""### Step {self.step_count}: {title}
**Timestamp:** {timestamp}

{content}

---

"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def log_tool_execution(self, tool_name: str, query: str, query_type: str, result_dict: dict):
        entities = result_dict.get("entities_found", [])
        success = result_dict.get("success", False)
        error = result_dict.get("error", "")

        entity_lines = []
        for e in entities:
            conf = e.get("confidence", "unknown").upper()
            entity_lines.append(f"  - [{conf}] {e.get('entity_type', '?')}: `{e.get('value', '')}` (source: \"{e.get('source_citation', '')}\")")

        entity_section = "\n".join(entity_lines) if entity_lines else "  - No entities found"

        raw = result_dict.get("raw_output", "")
        if len(raw) > 2000:
            raw = raw[:2000] + "\n... (truncated)"

        content = f"""- **Tool:** {tool_name}
- **Query:** `{query}` (type: {query_type})
- **Status:** {"SUCCESS" if success else "FAILED"}{"" if not error else f" - {error}"}
- **Entities Found ({len(entities)}):**
{entity_section}

<details>
<summary>Raw Output</summary>

```
{raw}
```
</details>
"""
        self.log_step(f"Tool Execution - {tool_name}", content)

    def log_analysis(self, analysis: str):
        self.log_step("Supervisor Analysis", analysis)

    def log_user_decision(self, decision: str):
        self.log_step("User Decision", f"**Decision:** {decision}")

    def log_pivot(self, from_selector: str, to_selectors: list[dict]):
        lines = [f"**Pivoting from:** `{from_selector}`\n\n**New selectors identified:**"]
        for s in to_selectors:
            lines.append(f"  - `{s.get('value', '')}` ({s.get('type', '')})")
        self.log_step("Pivot Planning", "\n".join(lines))

    def log_completion(self, summary: str):
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        content = f"""
---

## Investigation Complete
**Completed:** {timestamp}
**Total Steps:** {self.step_count}

### Summary
{summary}
"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(content)

    def get_full_log(self) -> str:
        if self.log_file.exists():
            return self.log_file.read_text(encoding="utf-8")
        return ""
