import json
import os
from datetime import datetime, timezone
from pathlib import Path

INVESTIGATIONS_DIR = Path(__file__).parent.parent.parent / "investigations"


def generate_case_id() -> str:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    existing = list(INVESTIGATIONS_DIR.glob(f"INV-{date_str}-*"))
    seq = len(existing) + 1
    return f"INV-{date_str}-{seq:03d}"


def create_investigation(seed_value: str, seed_type: str) -> dict:
    case_id = generate_case_id()
    case_dir = INVESTIGATIONS_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "case_id": case_id,
        "seed": {"value": seed_value, "type": seed_type},
        "status": "in_progress",
        "current_depth": 0,
        "steps_completed": 0,
        "pending_pivots": [],
        "completed_queries": [],
        "graph_file": str(case_dir / "graph.json"),
        "log_file": str(case_dir / "investigation.md"),
        "report_file": str(case_dir / "report.md"),
        "graph_html": str(case_dir / "graph.html"),
        "case_dir": str(case_dir),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    save_state(state)
    return state


def save_state(state: dict):
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state_file = Path(state["case_dir"]) / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_state(case_id: str) -> dict:
    state_file = INVESTIGATIONS_DIR / case_id / "state.json"
    if not state_file.exists():
        raise FileNotFoundError(f"No investigation found: {case_id}")
    with open(state_file, "r", encoding="utf-8") as f:
        return json.load(f)


def list_investigations() -> list[dict]:
    results = []
    if not INVESTIGATIONS_DIR.exists():
        return results
    for case_dir in sorted(INVESTIGATIONS_DIR.iterdir(), reverse=True):
        state_file = case_dir / "state.json"
        if state_file.exists():
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            results.append({
                "case_id": state["case_id"],
                "seed": state["seed"],
                "status": state["status"],
                "steps": state["steps_completed"],
                "created": state["created_at"],
                "updated": state["updated_at"],
            })
    return results


def pause_investigation(case_id: str):
    state = load_state(case_id)
    state["status"] = "paused"
    save_state(state)
    return state


def resume_investigation(case_id: str):
    state = load_state(case_id)
    if state["status"] != "paused":
        raise ValueError(f"Investigation {case_id} is not paused (status: {state['status']})")
    state["status"] = "in_progress"
    save_state(state)
    return state


def complete_investigation(case_id: str):
    state = load_state(case_id)
    state["status"] = "completed"
    save_state(state)
    return state


def archive_investigation(case_id: str):
    state = load_state(case_id)
    state["status"] = "archived"
    save_state(state)
    return state


def add_pivot(state: dict, selector_value: str, selector_type: str, source_tool: str, depth: int):
    pivot = {
        "value": selector_value,
        "type": selector_type,
        "source_tool": source_tool,
        "depth": depth,
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    if pivot not in state["pending_pivots"]:
        state["pending_pivots"].append(pivot)
    save_state(state)


def mark_query_complete(state: dict, selector_value: str, tool_name: str):
    entry = {"selector": selector_value, "tool": tool_name}
    if entry not in state["completed_queries"]:
        state["completed_queries"].append(entry)
    state["steps_completed"] += 1
    save_state(state)
