"""collect.py: RSS 피드를 읽어 원문 후보 풀을 만든다. (Naver API 제거)"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

import requests

from extract import UA, clean_html_text, extract_article
from sources import (
    BLOCKED_DOMAINS,
    CATEGORIES,
    CATEGORY_RSS_FEEDS,
)

RSS_ITEMS_PER_FEED = 25     # 피드당 후보 개수 (하루 30건을 뽑으려면 넉넉해야 함)
MAX_EXTRACT_ATTEMPTS = 24   # 카테고리당 원문 읽기 시도 횟수
POOL_BUFFER = 10            # 목표 건수보다 여유 있게 모아 거절/실패에 대비
                            # (엄격한 배제 기준으로 거절이 늘어 후보 소진을 방지)
# 연합뉴스 피드들은 상단에 같은 인기 기사를 함께 올리므로,
# 같은 기사가 여러 카테고리에 중복 저장되지 않도록 걸러냅니다.


def title_key(title: str) -> str:
    """대괄호/기호를 떼고 제목 비교용 키를 만든다."""
    text = re.sub(r"\[[^\]]*\]", " ", title or "")
    text = re.sub(r"[^0-9A-Za-z가-힣]+", "", text)
    return text.lower()[:40]


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
    pools: Dict[str, List[Dict[str, Any]]] = {}
    used_links: set = set(known_urls)
    used_titles: set = set()

    print("[1] 뉴스 수집 및 원문 전문 읽기 (고품질 RSS 전용)...")
    for category in CATEGORIES:
        target_count = len(plan.get(category, []))
        if target_count == 0:
            continue

        gathered = _fetch_category(category)
        pool = _pool_with_body(category, gathered, target_count + POOL_BUFFER,
                               used_links, used_titles)
        pools[category] = pool
        print(f"  · [{category}] 원문 확보 {len(pool)}건 (목표 {target_count}건)")

    return pools


def _fetch_category(category: str) -> List[Dict[str, Any]]:
    """카테고리의 여러 RSS 피드를 '한 개씩 번갈아' 모은다.

    피드를 그대로 이어붙이면 첫 번째 피드(BBC 코리아: 정치·범죄 위주)가
    목표 인원을 먼저 채워 버려, 뒤의 주제 피드가 한 번도 읽히지 않습니다.
    그래서 라운드로빈으로 섞어 모든 피드가 고르게 후보가 되게 합니다.
    """
    per_feed: List[List[Dict[str, Any]]] = []
    for rss in CATEGORY_RSS_FEEDS.get(category, []):
        try:
            items = fetch_rss_news(rss, count=RSS_ITEMS_PER_FEED)
            if items:
                per_feed.append(items)
        except Exception as e:
            print(f"  - RSS 수집 실패 ({category} - {rss}): {e}")

    gathered: List[Dict[str, Any]] = []
    max_len = max((len(items) for items in per_feed), default=0)
    for i in range(max_len):
        for items in per_feed:
            if i < len(items):
                gathered.append(items[i])
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
        # 구글 뉴스 리다이렉트였다면 해석된 실제 원문 URL을 출처로 남긴다
        item["source_url"] = extracted.get("url") or link
        pool.append(item)
        used_links.add(link)
        if key:
            used_titles.add(key)
    return pool
