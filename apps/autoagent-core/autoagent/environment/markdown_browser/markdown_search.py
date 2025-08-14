import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, cast
from urllib.parse import quote, quote_plus, unquote, urlparse, urlunparse

import requests

from .mdconvert import MarkdownConverter

logger = logging.getLogger(__name__)


class AbstractMarkdownSearch(ABC):
    """
    An abstract class for providing search capabilities to a Markdown browser.
    """

    @abstractmethod
    def search(self, query: str) -> str:
        pass


class BingMarkdownSearch(AbstractMarkdownSearch):
    """
    Provides Bing web search capabilities to Markdown browsers.
    """

    def __init__(self, bing_api_key: Optional[str] = None, interleave_results: bool = True):
        """
        Perform a Bing web search, and return the results formatted in Markdown.

        Args:
            bing_api_key: key for the Bing search API. If omitted, an attempt is made to read the key from the
                BING_API_KEY environment variable. If no key is found, BingMarkdownSearch will print a warning,
                and will fall back to visiting and scraping the live Bing results page. Scraping is objectively
                worse than using the API, and thus is not recommended.
            interleave_results: When using the Bing API, results are returned based on category (web, news, videos,
                etc.), along with instructions for how they should be interleaved on the page. When `interleave_results`
                is True, these interleaving instructions are followed, and a single results list is returned. When False,
                results are separated by category, and no interleaving is done.
        """
        self._mdconvert: MarkdownConverter = MarkdownConverter()
        self._interleave_results = interleave_results

        if bing_api_key is None or bing_api_key.strip() == "":
            self._bing_api_key = os.environ.get("BING_API_KEY")
        else:
            self._bing_api_key = bing_api_key

        if self._bing_api_key is None:
            if not self._interleave_results:
                raise ValueError(
                    "No Bing API key was provided. This is incompatible with setting `interleave_results` to False. "
                    "Please provide a key, or set `interleave_results` to True."
                )

    def search(self, query: str) -> str:
        """
        Search Bing and return the results formatted in Markdown. If a Bing API key is available, the API is used to
        perform the search. If no API key is available, the search is performed by submitting an HTTPS GET request
        directly to Bing. Searches performed with the API are higher quality and more reliable.

        Args:
            query: The search query to issue.

        Returns:
            A Markdown rendering of the search results.
        """
        if self._bing_api_key is None:
            return self._fallback_search(query)
        return self._api_search(query)

    def _api_search(self, query: str) -> str:
        """
        Search Bing using the API, and return the results formatted in Markdown.

        Args:
            query: The search query to issue.

        Returns:
            A Markdown rendering of the search results.
        """
        results = self._bing_api_call(query)

        snippets: Dict[str, List[str]] = {}

        def _processFacts(elm: List[Dict[str, Any]]) -> str:
            facts: List[str] = []
            for e in elm:
                k = e["label"]["text"]
                v = " ".join(item["text"] for item in e["items"])
                facts.append(f"{k}: {v}")
            return "\n".join(facts)

        # Web pages
        web_snippets: List[str] = []
        if "webPages" in results:
            for page in results["webPages"]["value"]:
                snippet = f"__POS__. {self._markdown_link(page['name'], page['url'])}\n{page['snippet']}"

                if "richFacts" in page:
                    snippet += "\n" + _processFacts(page["richFacts"])

                if "mentions" in page:
                    snippet += "\nMentions: " + ", ".join(e["name"] for e in page["mentions"])

                if page["id"] not in snippets:
                    snippets[page["id"]] = []
                snippets[page["id"]].append(snippet)
                web_snippets.append(snippet)

                if "deepLinks" in page:
                    for dl in page["deepLinks"]:
                        deep_snippet = (
                            f"__POS__. {self._markdown_link(dl['name'], dl['url'])}\n"
                            f"{dl['snippet'] if 'snippet' in dl else ''}"
                        )
                        snippets[page["id"]].append(deep_snippet)
                        web_snippets.append(deep_snippet)

        # News results
        news_snippets: List[str] = []
        if "news" in results:
            for page in results["news"]["value"]:
                snippet = (
                    f"__POS__. {self._markdown_link(page['name'], page['url'])}\n"
                    f"{page.get('description', '')}"
                ).strip()

                if "datePublished" in page:
                    snippet += "\nDate published: " + page["datePublished"].split("T")[0]

                if "richFacts" in page:
                    snippet += "\n" + _processFacts(page["richFacts"])

                if "mentions" in page:
                    snippet += "\nMentions: " + ", ".join(e["name"] for e in page["mentions"])

                news_snippets.append(snippet)

            if news_snippets:
                snippets[results["news"]["id"]] = news_snippets

        # Videos
        video_snippets: List[str] = []
        if "videos" in results:
            for page in results["videos"]["value"]:
                if not page["contentUrl"].startswith("https://www.youtube.com/watch?v="):
                    continue

                snippet = (
                    f"__POS__. {self._markdown_link(page['name'], page['contentUrl'])}\n"
                    f"{page.get('description', '')}"
                ).strip()

                if "datePublished" in page:
                    snippet += "\nDate published: " + page["datePublished"].split("T")[0]

                if "richFacts" in page:
                    snippet += "\n" + _processFacts(page["richFacts"])

                if "mentions" in page:
                    snippet += "\nMentions: " + ", ".join(e["name"] for e in page["mentions"])

                video_snippets.append(snippet)

            if video_snippets:
                snippets[results["videos"]["id"]] = video_snippets

        # Related searches
        related_searches = ""
        if "relatedSearches" in results:
            related_searches = "## Related Searches:\n"
            for s in results["relatedSearches"]["value"]:
                related_searches += "- " + s["text"] + "\n"
            snippets[results["relatedSearches"]["id"]] = [related_searches.strip()]

        idx = 0
        content = ""
        if self._interleave_results:
            # Interleaved
            for item in results["rankingResponse"]["mainline"]["items"]:
                _id = item["value"]["id"]
                if _id in snippets:
                    for s in snippets[_id]:
                        if "__POS__" in s:
                            idx += 1
                            content += s.replace("__POS__", str(idx)) + "\n\n"
                        else:
                            content += s + "\n\n"
        else:
            # Categorized
            if web_snippets:
                content += "## Web Results\n\n"
                for s in web_snippets:
                    if "__POS__" in s:
                        idx += 1
                        content += s.replace("__POS__", str(idx)) + "\n\n"
                    else:
                        content += s + "\n\n"
            if news_snippets:
                content += "## News Results\n\n"
                for s in news_snippets:
                    if "__POS__" in s:
                        idx += 1
                        content += s.replace("__POS__", str(idx)) + "\n\n"
                    else:
                        content += s + "\n\n"
            if video_snippets:
                content += "## Video Results\n\n"
                for s in video_snippets:
                    if "__POS__" in s:
                        idx += 1
                        content += s.replace("__POS__", str(idx)) + "\n\n"
                    else:
                        content += s + "\n\n"
            if related_searches:
                content += related_searches

        return f"## A Bing search for '{query}' found {idx} results:\n\n" + content.strip()

    def _bing_api_call(self, query: str) -> Dict[str, Any]:
        """
        Make a Bing API call, and return a Python representation of the JSON response.

        Args:
            query: The search query to issue.

        Returns:
            A Python representation of the Bing API's JSON response (as parsed by `json.loads()`).
        """
        if not self._bing_api_key:
            raise ValueError("Missing Bing API key.")

        request_kwargs: Dict[str, Any] = {}
        request_kwargs["headers"] = {"Ocp-Apim-Subscription-Key": self._bing_api_key}
        request_kwargs["params"] = {
            "q": query,
            "textDecorations": False,
            "textFormat": "raw",
        }
        request_kwargs["stream"] = False

        response = requests.get("https://api.bing.microsoft.com/v7.0/search", **request_kwargs)
        response.raise_for_status()
        results = response.json()
        return cast(Dict[str, Any], results)

    def _fallback_search(self, query: str) -> str:
        """
        When no Bing API key is provided, issue a simple HTTPS GET call to the Bing landing page
        and convert it to Markdown.

        Args:
            query: The search query to issue.

        Returns:
            The Bing search results page, converted to Markdown.
        """
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        )
        headers = {"User-Agent": user_agent}

        url = f"https://www.bing.com/search?q={quote_plus(query)}&FORM=QBLH"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return self._mdconvert.convert_response(response).text_content

    def _markdown_link(self, anchor: str, href: str) -> str:
        """
        Create a Markdown hyperlink, escaping the URLs as appropriate.

        Args:
            anchor: The anchor text of the hyperlink.
            href: The href destination of the hyperlink.

        Returns:
            A correctly formatted Markdown hyperlink.
        """
        try:
            parsed_url = urlparse(href)
            # URLs provided by Bing are sometimes only partially quoted, leaving in characters
            # that conflict with Markdown. Unquote the URL, then re-quote the path safely.
            href = urlunparse(parsed_url._replace(path=quote(unquote(parsed_url.path))))
            anchor = re.sub(r"[\[\]]", " ", anchor)
            return f"[{anchor}]({href})"
        except ValueError:
            return f"[{anchor}]({href})"
