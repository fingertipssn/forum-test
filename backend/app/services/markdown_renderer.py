import html as _html_module
import re
import mistune
from bs4 import BeautifulSoup


def _make_renderer():
    # escape=True prevents users from injecting raw HTML through markdown posts.
    return mistune.create_markdown(
        plugins=["strikethrough", "table", "url"],
        escape=True,
    )


_renderer = _make_renderer()


def render(raw: str) -> str:
    if not raw:
        return ""
    html = _renderer(raw)
    html = _process_mentions(html)
    html = _process_quotes(html)
    return html


def _process_mentions(html: str) -> str:
    pattern = re.compile(r"@([a-zA-Z0-9_]+)")
    return pattern.sub(
        lambda m: f'<a class="mention" href="/u/{m.group(1)}">@{m.group(1)}</a>',
        html,
    )


def _process_quotes(html: str) -> str:
    pattern = re.compile(
        r'\[quote(?:="([^"]*)")?\](.*?)\[/quote\]',
        re.DOTALL | re.IGNORECASE,
    )

    def replace_quote(match):
        # Escape citation (user-controlled) before embedding in HTML.
        citation = _html_module.escape(match.group(1) or "", quote=True)
        content = match.group(2).strip()
        inner_html = _renderer(content)
        title_html = f'<div class="title">{citation}</div>' if citation else ""
        return (
            f'<aside class="quote"><blockquote>'
            f"{title_html}"
            f"{inner_html}</blockquote></aside>"
        )

    return pattern.sub(replace_quote, html)


def extract_excerpt(cooked: str, max_length: int = 300) -> str:
    soup = BeautifulSoup(cooked, "html.parser")
    text = soup.get_text(separator=" ").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_length:
        text = text[:max_length].rsplit(" ", 1)[0] + "…"
    return text


def count_words(raw: str) -> int:
    return len(raw.split())
