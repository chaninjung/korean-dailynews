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


CONSENT_MARKERS = (
    "consent.google.com",
    "accounts.google.com",
    "before you continue",
)

CONSENT_TITLES = ("consent", "privacy", "sign in", "로그인")


def _is_consent_page(final_url: str, soup: BeautifulSoup) -> bool:
    """쿠키 동의/차단 페이지를 기사로 착각하지 않도록 걸러낸다."""
    host = (final_url or "").lower()
    if any(marker in host for marker in CONSENT_MARKERS[:2]):
        return True
    title = soup.title.get_text(strip=True).lower() if soup.title else ""
    return any(marker in title for marker in CONSENT_TITLES)


def _host_name(url: str) -> str:
    match = re.match(r"https?://([^/]+)", url or "")
    host = match.group(1) if match else ""
    return host[4:] if host.startswith("www.") else host


# ── 구글 뉴스 리다이렉트 링크 해석 ─────────────────────────────────
# 구글 뉴스 RSS의 /articles/ 링크는 동의 페이지와 JS 리다이렉트를 거칩니다.
# 동의 폼을 1회 자동 제출해 세션을 만들고, 기사 페이지의 시그니처(ts/sg)로
# batchexecute API를 호출해 실제 원문 URL을 얻은 뒤 본문을 읽습니다.
_GNEWS_SESSION = None


def _gnews_session() -> requests.Session:
    global _GNEWS_SESSION
    if _GNEWS_SESSION is None:
        session = requests.Session()
        session.headers.update({"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
        _GNEWS_SESSION = session
    return _GNEWS_SESSION


def _gnews_accept_consent(session: requests.Session, link: str) -> None:
    """구글 동의 폼을 자동 제출해 SOCS 쿠키를 받는다 (세션당 1회)."""
    try:
        resp = session.get(link, timeout=14, allow_redirects=True)
        if "consent.google.com" not in resp.url:
            return
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", action="https://consent.google.com/save")
        if not form:
            return
        data = {
            i["name"]: (i.get("value") or "")
            for i in form.find_all("input")
            if i.get("name")
        }
        session.post(
            "https://consent.google.com/save",
            data=data, timeout=14, allow_redirects=True,
        )
    except Exception:
        pass


def resolve_gnews_url(url: str) -> str:
    """구글 뉴스 리다이렉트 링크 -> 실제 원문 URL. 실패 시 빈 문자열."""
    if "news.google.com" not in url or "/articles/" not in url:
        return ""
    session = _gnews_session()
    try:
        page = session.get(url, timeout=14, allow_redirects=True)
        if "consent.google.com" in page.url:
            _gnews_accept_consent(session, url)
            page = session.get(url, timeout=14, allow_redirects=True)
        aid = re.search(r'data-n-a-id="([^"]+)"', page.text)
        ts = re.search(r'data-n-a-ts="([^"]+)"', page.text)
        sg = re.search(r'data-n-a-sg="([^"]+)"', page.text)
        if not (aid and ts and sg):
            return ""
        payload = [
            "garturlreq",
            [
                ["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1,
                 None, None, None, None, None, 0, 1],
                "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0,
            ],
            aid.group(1),
            int(ts.group(1)),
            sg.group(1),
        ]
        import json as _json
        f_req = [[["Fbv4je", _json.dumps(payload, separators=(",", ":")), None, "generic"]]]
        resp = session.post(
            "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je",
            headers={"content-type": "application/x-www-form-urlencoded;charset=UTF-8"},
            data={"f.req": _json.dumps(f_req, separators=(",", ":"))},
            timeout=14,
        )
        # 응답은 이중 이스케이프된 JSON 문자열: garturlres","<url>",1
        m = re.search(r'garturlres\\+",\\"+(.*?)\\+",\s*\d', resp.text, re.S)
        if not m:
            return ""
        real = m.group(1)
        # \uXXXX 형태의 유니코드 이스케이프 복원 (예: \u003d -> =)
        real = re.sub(
            r"\\+u([0-9a-fA-F]{4})",
            lambda x: chr(int(x.group(1), 16)),
            real,
        )
        real = real.replace("\\/", "/").replace("\\\\", "")
        return real if real.startswith("http") else ""
    except Exception:
        return ""


def extract_article(url: str) -> Dict[str, str]:
    empty = {"body": "", "image": "", "source_name": "", "url": ""}
    if not url or not url.startswith("http"):
        return empty

    final_url = url
    if "news.google.com" in url and "/articles/" in url:
        real = resolve_gnews_url(url)
        if not real:
            print("    · 구글 뉴스 리다이렉트 해석 실패.")
            return empty
        final_url = real

    try:
        resp = requests.get(
            final_url, timeout=14,
            headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko,en;q=0.8",
                "Referer": "https://news.google.com/",
            },
        )
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "text/html")
        if "html" not in ctype and "xml" not in ctype:
            return empty
        soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        print(f"    · 원문 요청 실패: {e}")
        return empty

    if _is_consent_page(resp.url, soup):
        print("    · 쿠키 동의/차단 페이지여서 본문을 읽을 수 없습니다.")
        return empty

    image = _meta(soup, property="og:image") or _meta(soup, attrs={"name": "twitter:image"})
    if image.startswith("//"):
        image = "https:" + image
    source_name = _meta(soup, property="og:site_name") or _host_name(resp.url)

    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    node = (
        soup.find("article")
        or soup.select_one(
            "#articleBody, #articeBody, #newsEndContents, .story-news-article,"
            " .article_body, .news_body, .article-body"
        )
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
        "url": resp.url,
    }
