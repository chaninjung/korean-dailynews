"""원문 HTML에서 본문, 대표 사진, 매체명을 읽는다."""

import re
import html
from typing import Dict

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def clean_html_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _meta(soup: BeautifulSoup, **attrs) -> str:
    tag = soup.find("meta", attrs=attrs)
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def extract_article(url: str) -> Dict[str, str]:
    empty = {"body": "", "image": "", "source_name": ""}
    if not url or not url.startswith("http"):
        return empty
    try:
        resp = requests.get(
            url, timeout=14,
            headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"},
        )
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "text/html")
        if "html" not in ctype and "xml" not in ctype:
            return empty
        soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        print(f"    · 원문 요청 실패: {e}")
        return empty

    image = _meta(soup, property="og:image") or _meta(soup, attrs={"name": "twitter:image"})
    if image.startswith("//"):
        image = "https:" + image
    source_name = _meta(soup, property="og:site_name")

    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    node = (
        soup.find("article")
        or soup.select_one("#articleBody, #articeBody, #newsEndContents, .article_body, .news_body")
        or soup.find("main")
    )
    paragraphs = []
    if node:
        paragraphs = [clean_html_text(p.get_text(" ", strip=True)) for p in node.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) >= 40]
    if len(paragraphs) < 3:
        paragraphs = [clean_html_text(p.get_text(" ", strip=True)) for p in soup.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) >= 40]
    seen = []
    for p in paragraphs:
        if p not in seen:
            seen.append(p)
    return {
        "body": "\n\n".join(seen[:18])[:6000],
        "image": image,
        "source_name": source_name,
    }
