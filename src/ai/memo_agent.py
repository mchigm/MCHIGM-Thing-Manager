"""
LLM integration for the MEMO page.

Uses litellm for a pluggable model interface. When no API key/model is
configured, falls back to a deterministic stub so the MEMO workflow still
creates an Item.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple

try:
    import litellm
except Exception:  # pragma: no cover - optional dependency at runtime
    litellm = None  # type: ignore

from src.database.models import ItemStatus, ItemType

# System prompt instructing the model to emit strict JSON for item creation.
_SYSTEM_PROMPT = """
You are an AI task planner for a time management app.
Return JSON only, no prose. Structure:
{
  "items": [
    {
      "title": "short title",
      "description": "optional details",
      "type": "Task|Event|Note|Goal",
      "status": "Backlog|To-Do|Doing|Done",
      "scenario": "Workspace name",
      "tags": ["#tag1", "#tag2"],
      "start_time": "ISO 8601 or null",
      "end_time": "ISO 8601 or null",
      "deadline": "ISO 8601 or null",
      "depends_on": ["title of prerequisite item"]
    }
  ]
}
If times are missing in the user's text, keep them null. Infer sensible tags
and scenario names like School, Work, or Personal.
"""


@dataclass
class GeneratedItem:
    title: str
    description: str = ""
    type: ItemType = ItemType.TASK
    status: ItemStatus = ItemStatus.TODO
    scenario: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    depends_on: List[str] = field(default_factory=list)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _map_item_type(value: Optional[str]) -> ItemType:
    if not value:
        return ItemType.TASK
    norm = value.strip().lower()
    for item_type in ItemType:
        if norm in {item_type.value.lower(), item_type.name.lower()}:
            return item_type
    return ItemType.TASK


def _map_item_status(value: Optional[str]) -> ItemStatus:
    if not value:
        return ItemStatus.TODO
    norm = value.strip().replace("-", "").lower()
    for status in ItemStatus:
        if norm in {status.value.replace("-", "").lower(), status.name.lower()}:
            return status
    return ItemStatus.TODO


def _extract_json_block(text: str) -> Optional[str]:
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start != -1 and end != -1 and end > start:
            fenced = text[start + 3 : end]
            if fenced.strip().lower().startswith("json"):
                fenced = fenced.split("\n", 1)[1] if "\n" in fenced else ""
            return fenced.strip() or None
    return text.strip() or None


def _items_from_payload(payload: dict) -> List[GeneratedItem]:
    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return []
    items: List[GeneratedItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict) or not raw.get("title"):
            continue
        items.append(
            GeneratedItem(
                title=str(raw.get("title")),
                description=str(raw.get("description") or ""),
                type=_map_item_type(raw.get("type")),
                status=_map_item_status(raw.get("status")),
                scenario=str(raw.get("scenario")) if raw.get("scenario") else None,
                tags=[t for t in raw.get("tags", []) if isinstance(t, str)],
                start_time=_parse_datetime(raw.get("start_time")),
                end_time=_parse_datetime(raw.get("end_time")),
                deadline=_parse_datetime(raw.get("deadline")),
                depends_on=[t for t in raw.get("depends_on", []) if isinstance(t, str)],
            )
        )
    return items


def _fallback_items(text: str) -> Tuple[str, List[GeneratedItem]]:
    item = GeneratedItem(
        title=text[:80],
        description="Captured via MEMO (AI offline).",
        type=ItemType.NOTE,
        status=ItemStatus.BACKLOG,
        scenario=None,
        tags=[],
    )
    return ("AI unavailable; saved as a Note in Backlog.", [item])


def call_memo_agent(user_text: str, model: str, api_key: str) -> Tuple[str, List[GeneratedItem]]:
    """
    Invoke the LLM (if configured) and return the AI reply plus parsed items.

    Falls back to a deterministic stub when litellm or credentials are missing.
    """
    if not litellm or not api_key or not model:
        return _fallback_items(user_text)

    try:
        response = litellm.completion(
            model=model,
            api_key=api_key,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
        )
        content = response.choices[0]["message"]["content"]  # type: ignore[index]
        json_block = _extract_json_block(content)
        if not json_block:
            return content, []
        payload = json.loads(json_block)
        items = _items_from_payload(payload)
        return content, items
    except Exception as exc:
        return f"AI error: {exc}", []
