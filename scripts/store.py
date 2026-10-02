"""lessons.json 갱신과 data/archive 보관."""

import os
import re
import json
import datetime
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS_PATH = os.path.join(BASE_DIR, "data", "lessons.json")
ARCHIVE_DIR = os.path.join(BASE_DIR, "data", "archive")
# 하루 30건이 만들어지므로, 하루치가 사이트에 다 보이도록 여유를 둡니다.
FEATURED_CAP = 36
# 한 라인(카테고리)에 보여줄 최대 기사 수: 라인당 6건 = 총 30건.
# 초과분은 아카이브로 넘겨 화면의 균형을 항상 유지합니다.
PER_CATEGORY_CAP = 6


def load_lessons(categories: List[str]) -> Dict[str, Any]:
    data: Dict[str, Any] = {"featured": [], "categories": categories}
    if os.path.exists(LESSONS_PATH):
        with open(LESSONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    data["categories"] = categories
    data.setdefault("featured", [])
    return data


def known_source_urls(featured: List[Dict[str, Any]]) -> set:
    urls = set()
    for item in featured:
        src = item.get("source") or {}
        if src.get("url"):
            urls.add(src["url"])
    if not os.path.isdir(ARCHIVE_DIR):
        return urls
    for name in os.listdir(ARCHIVE_DIR):
        if not name.endswith(".json"):
            continue
        path = os.path.join(ARCHIVE_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                archived = json.load(f)
        except Exception:
            continue
        if not isinstance(archived, list):
            continue
        for item in archived:
            src = item.get("source") or {}
            if src.get("url"):
                urls.add(src["url"])
    return urls


def archive_overflow(items: List[Dict[str, Any]]) -> None:
    if not items:
        return
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        date = item.get("date") or datetime.date.today().strftime("%Y.%m.%d")
        month = str(date).replace(".", "-")[:7]
        if not re.match(r"^\d{4}-\d{2}$", month):
            month = datetime.date.today().strftime("%Y-%m")
        buckets.setdefault(month, []).append(item)
    for month, chunk in buckets.items():
        path = os.path.join(ARCHIVE_DIR, f"{month}.json")
        existing: List[Dict[str, Any]] = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    existing = loaded
        known = {item.get("id") for item in existing}
        added = 0
        for item in chunk:
            if item.get("id") not in known:
                existing.append(item)
                added += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  · 아카이브 {month}.json 에 {added}건 보관")


def save_featured(data: Dict[str, Any], new_entries: List[Dict[str, Any]], categories: List[str]) -> None:
    for item in data.get("featured", []):
        item["isNew"] = False
    merged = new_entries + data.get("featured", [])
    # 카테고리별로 최신 6건만 남기고 초과분은 아카이브 (라인당 6건 = 총 30건)
    kept: List[Dict[str, Any]] = []
    overflow: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    for item in merged:
        cat = item.get("category")
        if counts.get(cat, 0) < PER_CATEGORY_CAP:
            kept.append(item)
            counts[cat] = counts.get(cat, 0) + 1
        else:
            overflow.append(item)
    if len(kept) > FEATURED_CAP:
        overflow.extend(kept[FEATURED_CAP:])
        kept = kept[:FEATURED_CAP]
    data["featured"] = kept
    archive_overflow(overflow)
    data["categories"] = categories
    with open(LESSONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
