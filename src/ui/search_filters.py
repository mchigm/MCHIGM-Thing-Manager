"""
Utilities for parsing the omni-search bar input into structured filters.
"""
from dataclasses import dataclass

from src.database.models import ItemStatus


@dataclass
class SearchQuery:
    terms: list[str]
    tags: list[str]
    statuses: list[ItemStatus]


_STATUS_MAP = {
    "backlog": ItemStatus.BACKLOG,
    "todo": ItemStatus.TODO,
    "doing": ItemStatus.DOING,
    "done": ItemStatus.DONE,
    "complete": ItemStatus.DONE,
}


def parse_search_text(text: str) -> SearchQuery:
    """Parse raw omni-search input into terms, #tags, and statuses."""
    terms: list[str] = []
    tags: list[str] = []
    statuses: list[ItemStatus] = []

    for raw in text.split():
        token = raw.strip()
        if not token:
            continue
        if token.startswith("#"):
            tags.append(token)
            continue
        norm = token.lower().replace("-", "").replace("_", "")
        status = _STATUS_MAP.get(norm)
        if status:
            statuses.append(status)
            continue
        terms.append(token)

    return SearchQuery(terms=terms, tags=tags, statuses=statuses)
