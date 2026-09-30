"""카테고리마다 원문을 읽어 후보 풀을 만든다."""

import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

import requests

from extract import UA, clean_html_text, extract_article
from sources import (
    BLOCKED_DOMAINS,
    CATEGORIES,
    CATEGORY_RSS_FEEDS,
    CATEGORY_SEARCH_QUERIES,
)

RSS_ITEMS_PER_FEED = 25     # 피드당 후보 개수 (하루 30건을 뽑으려면 넉넉해야 함)
MAX_EXTRACT_ATTEMPTS = 24   # 카테고리당 원문 읽기 시도 횟수
POOL_BUFFER = 3             # 목표 건수보다 여유 있게 모아 거절/실패에 대비
# 연합뉴스 피드들은 상단에 같은 인기 기사를 함께 올리므로,
# 같은 기사가 여러 카테고리에 중복 저장되지 않도록 걸러냅니다.


def title_key(title: str) -> str:
    """대괄호/기호를 떼고 제목 비교용 키를 만든다."""
    text = re.sub(r"\[[^\]]*\]", " ", title or "")
    text = re.sub(r"[^0-9A-Za-z가-힣]+", "", text)
    return text.lower()[:40]


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


def collect_pools(plan: Dict[str, List[int]], known_urls: set) -> Dict[str, List[Dict[str, Any]]]:
    """카테고리마다 (목표 건수 + 여유)만큼 원문을 읽어 후보 풀을 만든다."""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    pools: Dict[str, List[Dict[str, Any]]] = {}
    used_links: set = set(known_urls)
    used_titles: set = set()
    print("[1] 뉴스 수집 및 원문 전문 읽기...")
    for category in CATEGORIES:
        target_count = len(plan.get(category, []))
        if target_count == 0:
            continue
        gathered = _fetch_category(category, client_id, client_secret)
        pool = _pool_with_body(category, gathered, target_count + POOL_BUFFER,
                               used_links, used_titles)
        pools[category] = pool
        print(f"  · [{category}] 원문 확보 {len(pool)}건 (목표 {target_count}건)")
    return pools


def _fetch_category(category: str, client_id, client_secret) -> List[Dict[str, Any]]:
    """네이버 검색 API 가 있으면 그것을, 없으면 언론사 RSS 를 모은다."""
    gathered: List[Dict[str, Any]] = []
    if client_id and client_secret:
        for q in CATEGORY_SEARCH_QUERIES.get(category, [category]):
            try:
                gathered.extend(fetch_naver_news(q, client_id, client_secret,
                                                 count=RSS_ITEMS_PER_FEED))
            except Exception as e:
                print(f"  - 네이버 API 실패 ({q}): {e}")
            if len(gathered) >= RSS_ITEMS_PER_FEED:
                break
    if not gathered:
        for rss in CATEGORY_RSS_FEEDS.get(category, []):
            try:
                gathered.extend(fetch_rss_news(rss, count=RSS_ITEMS_PER_FEED))
            except Exception as e:
                print(f"  - RSS 수집 실패 ({category}): {e}")
    return gathered


def _pool_with_body(
    category: str,
    gathered: List[Dict[str, Any]],
    want: int,
    used_links: set,
    used_titles: set,
) -> List[Dict[str, Any]]:
    """본문을 읽은 후보를 want 개까지 모은다. 원문 요청은 필요한 만큼만 한다."""
    pool: List[Dict[str, Any]] = []
    skipped = 0
    for item in gathered:
        if len(pool) >= want:
            break
        link = item.get("link") or ""
        if not link or link in used_links:
            continue
        if any(domain in link for domain in BLOCKED_DOMAINS):
            continue
        key = title_key(item.get("title") or "")
        if key and key in used_titles:
            continue
        if skipped >= MAX_EXTRACT_ATTEMPTS:
            print(f"  - [{category}] 원문 {MAX_EXTRACT_ATTEMPTS}건 시도 후 중단")
            break
        skipped += 1
        extracted = extract_article(link)
        body = extracted.get("body") or ""
        if len(body) < 280:
            continue
        item["target_category"] = category
        item["body"] = body
        item["image"] = extracted.get("image") or ""
        item["source_name"] = item.get("source_name") or extracted.get("source_name") or ""
        item["source_url"] = link
        pool.append(item)
        used_links.add(link)
        if key:
            used_titles.add(key)
    return pool
