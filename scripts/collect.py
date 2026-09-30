"""카테고리마다 후보를 모으고, 본문을 읽은 1건만 고른다."""

import os
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

import requests

from extract import UA, clean_html_text, extract_article
from sources import CATEGORIES, CATEGORY_SEARCH_QUERIES, CATEGORY_RSS_FALLBACK


def fetch_naver_news(query: str, client_id: str, client_secret: str, count: int = 3) -> List[Dict[str, Any]]:
    url = (
        "https://openapi.naver.com/v1/search/news.json"
        f"?query={urllib.parse.quote(query)}&display={count}&sort=date"
    )
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    resp = requests.get(url, headers=headers, timeout=12)
    resp.raise_for_status()
    items = []
    for item in resp.json().get("items", []):
        items.append({
            "title": clean_html_text(item.get("title", "")),
            "description": clean_html_text(item.get("description", "")),
            "link": item.get("originallink") or item.get("link", ""),
            "pubDate": item.get("pubDate", ""),
        })
    return items


def fetch_rss_news(rss_url: str, count: int = 3) -> List[Dict[str, Any]]:
    resp = requests.get(rss_url, timeout=12, headers={"User-Agent": UA})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item")[:count]:
        source_el = item.find("source")
        source_name = clean_html_text(source_el.text or "") if source_el is not None else ""
        items.append({
            "title": clean_html_text(item.findtext("title", "")),
            "description": clean_html_text(item.findtext("description", "")),
            "link": item.findtext("link", ""),
            "pubDate": item.findtext("pubDate", ""),
            "source_name": source_name,
        })
    return items


def collect_candidates() -> List[Dict[str, Any]]:
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    candidates = []
    print("[1] 뉴스 수집 및 원문 전문 읽기...")
    for category in CATEGORIES:
        gathered: List[Dict[str, Any]] = []
        if client_id and client_secret:
            for q in CATEGORY_SEARCH_QUERIES.get(category, [category]):
                try:
                    gathered.extend(fetch_naver_news(q, client_id, client_secret, count=3))
                except Exception as e:
                    print(f"  - 네이버 API 실패 ({q}): {e}")
                if len(gathered) >= 3:
                    break
        if not gathered:
            rss = CATEGORY_RSS_FALLBACK.get(category)
            if rss:
                try:
                    gathered = fetch_rss_news(rss, count=3)
                except Exception as e:
                    print(f"  - RSS 수집 실패 ({category}): {e}")
        chosen = _first_with_body(category, gathered)
        if chosen:
            candidates.append(chosen)
        else:
            print(f"  - [{category}] 원문을 읽은 후보가 없습니다.")
    return candidates


def _first_with_body(category: str, gathered: List[Dict[str, Any]]):
    for item in gathered:
        link = item.get("link") or ""
        print(f"  - [{category}] 원문 확인: {(item.get('title') or '')[:32]}")
        extracted = extract_article(link)
        body = extracted.get("body") or ""
        if len(body) < 280:
            print(f"    · 본문 부족 ({len(body)}자), 다음 후보")
            continue
        item["target_category"] = category
        item["body"] = body
        item["image"] = extracted.get("image") or ""
        item["source_name"] = item.get("source_name") or extracted.get("source_name") or ""
        item["source_url"] = link
        photo = "있음" if item["image"] else "없음"
        print(f"    · 본문 {len(body)}자 | 사진 {photo} | {item['source_name'] or '매체 미상'}")
        return item
    return None
