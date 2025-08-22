from __future__ import annotations

from browsergym.core.action.functions import goto, page

import base64
import html
import io


def _get_page_markdown() -> None:
    """
    Convert the current page to Markdown and render a paged HTML view.
    Intended for BrowserGym usage after you've already navigated somewhere.
    """
    # Grab DOM
    dom_html = page.evaluate("document.documentElement.outerHTML;")
    if page.url == "about:blank":
        raise Exception(
            "You cannot convert the blank page. Visit a valid page before converting."
        )

    # Convert to Markdown
    from autoagent.environment.markdown_browser.mdconvert import MarkdownConverter

    md = MarkdownConverter()
    res = md.convert_stream(io.StringIO(dom_html), file_extension=".html", url=page.url)

    # Chunk the markdown for viewport-sized scrolling
    content = res.text_content or ""
    chunk_size = 5000
    chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
    note = (
        f"The converted markdown text is divided into {len(chunks)} chunks; "
        "use `page_down()` and `page_up()` to navigate."
        if len(chunks) > 1
        else ""
    )

    # Build simple HTML (escape markdown since we’re embedding as text)
    regions = []
    for i, chunk in enumerate(chunks, start=1):
        regions.append(
            f"""
            <div role="region"
                 aria-label="[INFO] content chunk {i}/{len(chunks)} {html.escape(note)}"
                 tabindex="0"
                 data-chunk-id="{i-1}"
                 style="min-height: 100vh; padding: 20px 0; border-bottom: 1px solid #eee;">
                <pre style="white-space: pre-wrap; word-wrap: break-word; margin: 0;">{html.escape(chunk)}</pre>
            </div>
            """
        )

    html_content = f"""
    <html>
      <head>
        <title>{html.escape(res.title or "")}</title>
        <meta charset="utf-8"/>
        <style>
          html, body {{ height: 100%; margin: 0; }}
          body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
          .viewport-container {{ height: 100vh; overflow-y: auto; scroll-behavior: smooth; padding: 16px 24px; }}
          .hint {{ margin-top: 16px; font-size: 0.9em; color: #555; }}
        </style>
      </head>
      <body>
        <div class="viewport-container">
          {''.join(regions)}
          <div class="hint">
            If you haven’t got the answer and want to go back, call:
            <code>visit_url(url={html.escape(repr(page.url))})</code>
          </div>
        </div>
      </body>
    </html>
    """

    # Navigate to data: URL (fix double prefix bug)
    data_url = "data:text/html;base64," + base64.b64encode(
        html_content.encode("utf-8")
    ).decode("utf-8")
    goto(data_url)

    # Fire pageshow event once (fix mis-nested triple quotes)
    page.evaluate(
        """
        const event = new Event('pageshow', { bubbles: true, cancelable: false });
        window.dispatchEvent(event);
        """
    )
