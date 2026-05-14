"""
Unit tests for link handling in src/ui/pages/todos.py
"""

from PyQt6.QtCore import QUrl

from src.ui.pages.todos import ItemDetailsDialog


class TestLinkExtraction:
    def test_extracts_web_and_app_links(self):
        text = "Docs https://example.com and local file:///tmp/demo plus mailto:me@example.com"
        links = ItemDetailsDialog._extract_links(text)
        assert "https://example.com" in links
        assert "file:///tmp/demo" in links
        assert "mailto:me@example.com" in links


class TestLinkNormalization:
    def test_normalizes_www_links(self):
        url = ItemDetailsDialog._link_to_qurl("www.example.com")
        assert isinstance(url, QUrl)
        assert url.scheme() == "https"
        assert url.host() == "www.example.com"

    def test_normalizes_local_paths(self):
        url = ItemDetailsDialog._link_to_qurl("~/demo.txt")
        assert url.isLocalFile()
