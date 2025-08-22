import tempfile

import pytest

pytest.importorskip("browsergym")
pytest.importorskip("inquirer")

from autoagent.environment.markdown_browser.requests_markdown_browser import (
    RequestsMarkdownBrowser,
)
from autoagent.environment.markdown_browser.mdconvert import MarkdownConverter


def test_find_next_viewport_strips_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        browser = RequestsMarkdownBrowser(local_root=tmpdir, workplace_name="wp")
        content = "Check [Example](http://example.com) and image ![alt](img.png)."
        browser._page_content = content
        browser.viewport_pages = [(0, len(content))]
        assert browser._find_next_viewport("example.com", 0) is None
        assert browser._find_next_viewport("example", 0) == 0
        assert browser._find_next_viewport("alt", 0) is None


def test_append_ext_deduplicates():
    converter = MarkdownConverter()
    exts = []
    converter._append_ext(exts, ".txt")
    converter._append_ext(exts, ".txt")
    assert exts == [".txt"]
