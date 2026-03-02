"""
Unit tests for src/ai/memo_agent.py
"""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.ai.memo_agent import (
    GeneratedItem,
    _extract_json_block,
    _fallback_items,
    _items_from_payload,
    _map_item_status,
    _map_item_type,
    _parse_datetime,
    call_memo_agent,
)
from src.database.models import ItemStatus, ItemType


# ---------------------------------------------------------------------------
# _parse_datetime
# ---------------------------------------------------------------------------
class TestParseDatetime:
    def test_none_returns_none(self):
        assert _parse_datetime(None) is None

    def test_empty_string_returns_none(self):
        assert _parse_datetime("") is None

    def test_valid_iso_string(self):
        dt = _parse_datetime("2024-06-15T09:00:00")
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 6
        assert dt.day == 15

    def test_naive_datetime_gets_utc(self):
        dt = _parse_datetime("2024-01-01T00:00:00")
        assert dt.tzinfo is not None
        assert dt.tzinfo == timezone.utc

    def test_tz_aware_datetime_preserved(self):
        dt = _parse_datetime("2024-01-01T12:00:00+05:30")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_invalid_string_returns_none(self):
        assert _parse_datetime("not-a-date") is None

    def test_malformed_iso_returns_none(self):
        assert _parse_datetime("2024-13-45") is None


# ---------------------------------------------------------------------------
# _map_item_type
# ---------------------------------------------------------------------------
class TestMapItemType:
    def test_none_returns_task(self):
        assert _map_item_type(None) == ItemType.TASK

    def test_empty_string_returns_task(self):
        assert _map_item_type("") == ItemType.TASK

    def test_task(self):
        assert _map_item_type("Task") == ItemType.TASK

    def test_event(self):
        assert _map_item_type("Event") == ItemType.EVENT

    def test_note(self):
        assert _map_item_type("Note") == ItemType.NOTE

    def test_goal(self):
        assert _map_item_type("Goal") == ItemType.GOAL

    def test_case_insensitive(self):
        assert _map_item_type("TASK") == ItemType.TASK
        assert _map_item_type("event") == ItemType.EVENT
        assert _map_item_type("NOTE") == ItemType.NOTE

    def test_unknown_returns_task(self):
        assert _map_item_type("Reminder") == ItemType.TASK


# ---------------------------------------------------------------------------
# _map_item_status
# ---------------------------------------------------------------------------
class TestMapItemStatus:
    def test_none_returns_todo(self):
        assert _map_item_status(None) == ItemStatus.TODO

    def test_empty_string_returns_todo(self):
        assert _map_item_status("") == ItemStatus.TODO

    def test_backlog(self):
        assert _map_item_status("Backlog") == ItemStatus.BACKLOG

    def test_todo_with_hyphen(self):
        assert _map_item_status("To-Do") == ItemStatus.TODO

    def test_doing(self):
        assert _map_item_status("Doing") == ItemStatus.DOING

    def test_done(self):
        assert _map_item_status("Done") == ItemStatus.DONE

    def test_case_insensitive(self):
        assert _map_item_status("DONE") == ItemStatus.DONE
        assert _map_item_status("backlog") == ItemStatus.BACKLOG

    def test_unknown_returns_todo(self):
        assert _map_item_status("Pending") == ItemStatus.TODO


# ---------------------------------------------------------------------------
# _extract_json_block
# ---------------------------------------------------------------------------
class TestExtractJsonBlock:
    def test_plain_json_returned_as_is(self):
        raw = '{"items": []}'
        assert _extract_json_block(raw) == '{"items": []}'

    def test_fenced_json_block_stripped(self):
        raw = '```json\n{"items": []}\n```'
        result = _extract_json_block(raw)
        assert result == '{"items": []}'

    def test_fenced_block_without_lang_marker(self):
        raw = '```\n{"items": []}\n```'
        result = _extract_json_block(raw)
        assert result is not None
        assert '{"items": []}' in result

    def test_empty_string_returns_none(self):
        result = _extract_json_block("")
        assert result is None

    def test_whitespace_only_returns_none(self):
        result = _extract_json_block("   ")
        assert result is None


# ---------------------------------------------------------------------------
# _items_from_payload
# ---------------------------------------------------------------------------
class TestItemsFromPayload:
    def test_empty_items_list(self):
        assert _items_from_payload({"items": []}) == []

    def test_missing_items_key(self):
        assert _items_from_payload({}) == []

    def test_items_not_a_list(self):
        assert _items_from_payload({"items": "not a list"}) == []

    def test_item_without_title_skipped(self):
        result = _items_from_payload({"items": [{"type": "Task"}]})
        assert result == []

    def test_minimal_valid_item(self):
        payload = {"items": [{"title": "Write report"}]}
        result = _items_from_payload(payload)
        assert len(result) == 1
        assert result[0].title == "Write report"
        assert result[0].type == ItemType.TASK
        assert result[0].status == ItemStatus.TODO

    def test_full_item_parsed(self):
        payload = {
            "items": [
                {
                    "title": "CS 101 assignment",
                    "description": "Research paper",
                    "type": "Note",
                    "status": "Backlog",
                    "scenario": "School",
                    "tags": ["#cs101", "#urgent"],
                    "start_time": None,
                    "end_time": None,
                    "deadline": "2024-12-01T23:59:00",
                    "depends_on": [],
                }
            ]
        }
        result = _items_from_payload(payload)
        assert len(result) == 1
        item = result[0]
        assert item.title == "CS 101 assignment"
        assert item.description == "Research paper"
        assert item.type == ItemType.NOTE
        assert item.status == ItemStatus.BACKLOG
        assert item.scenario == "School"
        assert "#cs101" in item.tags
        assert isinstance(item.deadline, datetime)

    def test_depends_on_non_string_entries_skipped(self):
        payload = {"items": [{"title": "Task", "depends_on": ["Parent", 123, None]}]}
        result = _items_from_payload(payload)
        assert result[0].depends_on == ["Parent"]

    def test_multiple_items(self):
        payload = {
            "items": [
                {"title": "Task 1"},
                {"title": "Task 2", "type": "Goal", "status": "Done"},
            ]
        }
        result = _items_from_payload(payload)
        assert len(result) == 2
        assert result[1].type == ItemType.GOAL
        assert result[1].status == ItemStatus.DONE


# ---------------------------------------------------------------------------
# _fallback_items
# ---------------------------------------------------------------------------
class TestFallbackItems:
    def test_returns_tuple(self):
        msg, items = _fallback_items("Test memo")
        assert isinstance(msg, str)
        assert isinstance(items, list)

    def test_single_item_created(self):
        _, items = _fallback_items("Some quick note")
        assert len(items) == 1

    def test_item_is_backlog_note(self):
        _, items = _fallback_items("Quick thought")
        item = items[0]
        assert item.type == ItemType.NOTE
        assert item.status == ItemStatus.BACKLOG

    def test_long_text_truncated_to_80_chars(self):
        long_text = "a" * 200
        _, items = _fallback_items(long_text)
        assert len(items[0].title) <= 80

    def test_message_mentions_offline(self):
        msg, _ = _fallback_items("text")
        assert "unavailable" in msg.lower() or "offline" in msg.lower()


# ---------------------------------------------------------------------------
# call_memo_agent — fallback paths (no litellm / no credentials)
# ---------------------------------------------------------------------------
class TestCallMemoAgentFallback:
    def test_no_api_key_triggers_fallback(self):
        msg, items = call_memo_agent("Buy milk", model="gpt-4o", api_key="")
        assert len(items) == 1
        assert items[0].status == ItemStatus.BACKLOG

    def test_no_model_triggers_fallback(self):
        msg, items = call_memo_agent("Buy milk", model="", api_key="sk-test")
        assert len(items) == 1

    def test_both_empty_triggers_fallback(self):
        msg, items = call_memo_agent("Buy milk", model="", api_key="")
        assert items[0].type == ItemType.NOTE

    def test_litellm_none_triggers_fallback(self):
        """When litellm module itself is None, fallback must be used."""
        import src.ai.memo_agent as agent_mod
        original = agent_mod.litellm
        try:
            agent_mod.litellm = None  # type: ignore[assignment]
            msg, items = call_memo_agent("Note", model="gpt-4", api_key="sk-key")
            assert len(items) == 1
        finally:
            agent_mod.litellm = original

    def test_litellm_error_returns_error_message(self):
        """When litellm raises, return error string and empty item list."""
        mock_litellm = MagicMock()
        mock_litellm.completion.side_effect = RuntimeError("API timeout")
        import src.ai.memo_agent as agent_mod
        original = agent_mod.litellm
        try:
            agent_mod.litellm = mock_litellm
            msg, items = call_memo_agent("Note", model="gpt-4", api_key="sk-key")
            assert "error" in msg.lower()
            assert items == []
        finally:
            agent_mod.litellm = original

    def test_litellm_returns_valid_json(self):
        """When litellm returns valid JSON, items are parsed and returned."""
        valid_response = json.dumps({
            "items": [
                {"title": "Finish report", "type": "Task", "status": "To-Do", "tags": ["#urgent"]}
            ]
        })
        mock_choice = MagicMock()
        mock_choice.__getitem__.side_effect = lambda key: {"message": {"content": valid_response}}[key]
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_litellm = MagicMock()
        mock_litellm.completion.return_value = mock_response
        import src.ai.memo_agent as agent_mod
        original = agent_mod.litellm
        try:
            agent_mod.litellm = mock_litellm
            msg, items = call_memo_agent("Finish my report", model="gpt-4", api_key="sk-key")
            assert len(items) == 1
            assert items[0].title == "Finish report"
            assert "#urgent" in items[0].tags
        finally:
            agent_mod.litellm = original
