"""
Unit tests for src/ui/search_filters.py
"""
import pytest

from src.database.models import ItemStatus
from src.ui.search_filters import SearchQuery, parse_search_text


class TestParseSearchText:
    # ------------------------------------------------------------------
    # Basic term extraction
    # ------------------------------------------------------------------
    def test_empty_string_gives_empty_query(self):
        q = parse_search_text("")
        assert q.terms == []
        assert q.tags == []
        assert q.statuses == []

    def test_whitespace_only_gives_empty_query(self):
        q = parse_search_text("   ")
        assert q.terms == []

    def test_plain_words_become_terms(self):
        q = parse_search_text("hello world")
        assert q.terms == ["hello", "world"]
        assert q.tags == []
        assert q.statuses == []

    def test_single_term(self):
        q = parse_search_text("meeting")
        assert q.terms == ["meeting"]

    # ------------------------------------------------------------------
    # Tag extraction
    # ------------------------------------------------------------------
    def test_hash_token_becomes_tag(self):
        q = parse_search_text("#urgent")
        assert q.tags == ["#urgent"]
        assert q.terms == []

    def test_multiple_tags(self):
        q = parse_search_text("#urgent #cs101 #frontend")
        assert q.tags == ["#urgent", "#cs101", "#frontend"]

    def test_tags_and_terms_mixed(self):
        q = parse_search_text("assignment #cs101 due")
        assert q.terms == ["assignment", "due"]
        assert q.tags == ["#cs101"]

    def test_bare_hash_treated_as_tag(self):
        """A lone '#' token is treated as a tag (empty string after #)."""
        q = parse_search_text("#")
        assert "#" in q.tags

    # ------------------------------------------------------------------
    # Status extraction
    # ------------------------------------------------------------------
    def test_backlog_status(self):
        q = parse_search_text("backlog")
        assert ItemStatus.BACKLOG in q.statuses
        assert q.terms == []

    def test_todo_status(self):
        q = parse_search_text("todo")
        assert ItemStatus.TODO in q.statuses

    def test_doing_status(self):
        q = parse_search_text("doing")
        assert ItemStatus.DOING in q.statuses

    def test_done_status(self):
        q = parse_search_text("done")
        assert ItemStatus.DONE in q.statuses

    def test_complete_alias_maps_to_done(self):
        q = parse_search_text("complete")
        assert ItemStatus.DONE in q.statuses

    def test_status_case_insensitive(self):
        q = parse_search_text("DOING")
        assert ItemStatus.DOING in q.statuses

    def test_hyphenated_todo_status(self):
        q = parse_search_text("to-do")
        assert ItemStatus.TODO in q.statuses

    def test_multiple_statuses(self):
        q = parse_search_text("done todo")
        assert ItemStatus.DONE in q.statuses
        assert ItemStatus.TODO in q.statuses

    # ------------------------------------------------------------------
    # Combined input
    # ------------------------------------------------------------------
    def test_combined_query(self):
        q = parse_search_text("assignment #cs101 doing urgent")
        assert "assignment" in q.terms
        assert "urgent" in q.terms
        assert "#cs101" in q.tags
        assert ItemStatus.DOING in q.statuses

    def test_return_type_is_search_query(self):
        q = parse_search_text("test")
        assert isinstance(q, SearchQuery)

    def test_preserves_original_case_in_terms(self):
        q = parse_search_text("Assignment CS101")
        assert "Assignment" in q.terms
        assert "CS101" in q.terms
