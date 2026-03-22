#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: Optional[int]
    method: str
    content_type: str
    title: str
    excerpt: str
    text: str
    errors: List[str]


def _compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _clean_html_text(html: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "img"]):
        tag.decompose()
    title = _compact_whitespace(soup.title.get_text(" ", strip=True)) if soup.title else ""
    text = _compact_whitespace(soup.get_text(" ", strip=True))
    return title, text


def _requests_fetch(url: str, timeout: float) -> FetchResult:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
    content_type = response.headers.get("Content-Type", "")
    title = ""
    text = response.text if response.encoding or "text" in content_type.lower() or "html" in content_type.lower() else response.text
    if "html" in content_type.lower() or "text" in content_type.lower() or not content_type:
        title, cleaned_text = _clean_html_text(response.text)
    else:
        cleaned_text = _compact_whitespace(response.text)
    excerpt = _truncate(cleaned_text, 500)
    return FetchResult(
        url=url,
        final_url=str(response.url),
        status_code=response.status_code,
        method="requests",
        content_type=content_type,
        title=title,
        excerpt=excerpt,
        text=cleaned_text,
        errors=[],
    )


def _urllib_fetch(url: str, timeout: float) -> FetchResult:
    req = Request(url, headers=DEFAULT_HEADERS)
    with urlopen(req, timeout=timeout) as response:  # nosec - user-requested network helper
        raw = response.read()
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or "utf-8"
        text = raw.decode(charset, errors="replace")
        if "html" in content_type.lower() or "text" in content_type.lower() or not content_type:
            title, cleaned_text = _clean_html_text(text)
        else:
            title, cleaned_text = "", _compact_whitespace(text)
        excerpt = _truncate(cleaned_text, 500)
        return FetchResult(
            url=url,
            final_url=response.geturl(),
            status_code=getattr(response, "status", None),
            method="urllib",
            content_type=content_type,
            title=title,
            excerpt=excerpt,
            text=cleaned_text,
            errors=[],
        )


def _mobile_variants(url: str) -> List[str]:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return []
    variants: List[str] = []
    host = parsed.netloc
    if not host.startswith("m."):
        variants.append(parsed._replace(netloc=f"m.{host}").geturl())
    path = parsed.path.rstrip("/")
    if path and not path.endswith("/amp"):
        amp_variant = parsed._replace(path=path + "/amp").geturl()
        variants.append(amp_variant)
    return variants


def fetch_url(url: str, timeout: float, max_chars: int, try_mobile: bool) -> Dict[str, Any]:
    errors: List[str] = []
    attempts: List[Tuple[str, str]] = [(url, "primary")]
    if try_mobile:
        for variant in _mobile_variants(url):
            attempts.append((variant, "alt"))

    seen = set()
    for attempt_url, _kind in attempts:
        if attempt_url in seen:
            continue
        seen.add(attempt_url)
        try:
            result = _requests_fetch(attempt_url, timeout)
            result.text = _truncate(result.text, max_chars)
            result.excerpt = _truncate(result.excerpt, min(max_chars, 500))
            result.errors = errors
            return {
                "mode": "fetch",
                "url": url,
                "final_url": result.final_url,
                "status_code": result.status_code,
                "title": result.title,
                "excerpt": result.excerpt,
                "text": result.text,
                "method": result.method,
                "content_type": result.content_type,
                "errors": errors,
            }
        except Exception as exc:
            errors.append(f"requests:{attempt_url}:{type(exc).__name__}:{exc}")
        try:
            result = _urllib_fetch(attempt_url, timeout)
            result.text = _truncate(result.text, max_chars)
            result.excerpt = _truncate(result.excerpt, min(max_chars, 500))
            result.errors = errors
            return {
                "mode": "fetch",
                "url": url,
                "final_url": result.final_url,
                "status_code": result.status_code,
                "title": result.title,
                "excerpt": result.excerpt,
                "text": result.text,
                "method": result.method,
                "content_type": result.content_type,
                "errors": errors,
            }
        except Exception as exc:
            errors.append(f"urllib:{attempt_url}:{type(exc).__name__}:{exc}")

    return {
        "mode": "fetch",
        "url": url,
        "final_url": url,
        "status_code": None,
        "title": "",
        "excerpt": "",
        "text": "",
        "method": "none",
        "content_type": "",
        "errors": errors,
    }


def _decode_duckduckgo_redirect(href: str) -> str:
    if href.startswith("//"):
        return "https:" + href
    parsed = urlparse(href)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        query = parse_qs(parsed.query)
        uddg = query.get("uddg")
        if uddg:
            return unquote(uddg[0])
    return href


def _parse_duckduckgo_results(html: str, base_url: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    results: List[Dict[str, str]] = []
    seen = set()

    for anchor in soup.select("a.result__a, a.result-link, a[href]"):
        href = anchor.get("href")
        title = _compact_whitespace(anchor.get_text(" ", strip=True))
        if not href or not title:
            continue
        url = _decode_duckduckgo_redirect(urljoin(base_url, href))
        if not url.startswith("http"):
            continue
        if url in seen:
            continue
        parent = anchor.find_parent(["div", "tr", "article"])
        snippet = ""
        if parent is not None:
            snippet_candidates = parent.select(".result__snippet, .result-snippet, td.result-snippet, .snippet")
            if snippet_candidates:
                snippet = _compact_whitespace(snippet_candidates[0].get_text(" ", strip=True))
            else:
                snippet = _compact_whitespace(parent.get_text(" ", strip=True))
                if snippet.startswith(title):
                    snippet = _compact_whitespace(snippet[len(title):])
        results.append({"title": title, "url": url, "snippet": _truncate(snippet, 300)})
        seen.add(url)
    return results


def search_web(query: str, site: Optional[str], max_results: int, timeout: float) -> Dict[str, Any]:
    search_query = query.strip()
    if site:
        search_query = f"{search_query} site:{site}"

    providers = [
        ("duckduckgo_html", f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"),
        ("duckduckgo_lite", f"https://lite.duckduckgo.com/lite/?q={quote_plus(search_query)}"),
    ]
    errors: List[str] = []
    for provider, url in providers:
        fetch = fetch_url(url, timeout=timeout, max_chars=50000, try_mobile=False)
        if fetch.get("status_code") and int(fetch["status_code"]) >= 400:
            errors.extend(fetch.get("errors", []))
            errors.append(f"{provider}:http_status:{fetch.get('status_code')}")
            continue
        html = fetch.get("text", "")
        if not html:
            errors.extend(fetch.get("errors", []))
            continue
        results = _parse_duckduckgo_results(html, url)
        if results:
            trimmed = []
            for idx, item in enumerate(results[:max_results], start=1):
                trimmed.append({"rank": idx, **item})
            return {
                "mode": "search",
                "query": query,
                "site": site,
                "provider": provider,
                "result_count": len(trimmed),
                "results": trimmed,
                "errors": errors,
            }
        errors.extend(fetch.get("errors", []))
        errors.append(f"{provider}:no_results")

    return {
        "mode": "search",
        "query": query,
        "site": site,
        "provider": "none",
        "result_count": 0,
        "results": [],
        "errors": errors,
    }


def _write_output(data: Dict[str, Any], output: Optional[str]) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HTTP search/fetch fallback helper for Biotech Alpha")
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser("search", help="Search the web via HTML search endpoints")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--site", default=None)
    search_parser.add_argument("--max-results", type=int, default=8)
    search_parser.add_argument("--timeout", type=float, default=20.0)
    search_parser.add_argument("--output", default=None)

    fetch_parser = sub.add_parser("fetch", help="Fetch a page via requests and urllib fallbacks")
    fetch_parser.add_argument("--url", required=True)
    fetch_parser.add_argument("--timeout", type=float, default=20.0)
    fetch_parser.add_argument("--max-chars", type=int, default=6000)
    fetch_parser.add_argument("--try-mobile", action="store_true")
    fetch_parser.add_argument("--output", default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "search":
        result = search_web(
            query=args.query,
            site=args.site,
            max_results=max(1, int(args.max_results)),
            timeout=float(args.timeout),
        )
        _write_output(result, args.output)
        return

    if args.command == "fetch":
        result = fetch_url(
            url=args.url,
            timeout=float(args.timeout),
            max_chars=max(200, int(args.max_chars)),
            try_mobile=bool(args.try_mobile),
        )
        _write_output(result, args.output)
        return

    parser.error("unknown command")


if __name__ == "__main__":
    main()
