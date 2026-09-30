"""
Huko News Data Pipeline
원문 수집 -> LLM 가공 -> data/lessons.json
20개를 넘는 지난 글은 data/archive/YYYY-MM.json 으로 보관
"""

import os
import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from collect import collect_candidates
from llm import process_candidate
from sources import CATEGORIES, CATEGORY_IMAGE_FALLBACK, LEVEL_LABEL_MAP
from store import known_source_urls, load_lessons, save_featured


def _fallback_image(category: str) -> str:
    return CATEGORY_IMAGE_FALLBACK.get(
        category, CATEGORY_IMAGE_FALLBACK["Culture & Society"]
    )


def build_entry(candidate: dict, rewritten: dict, index: int) -> dict:
    lvl = int(rewritten.get("assessed_level", 6))
    lvl = min(9, max(1, lvl))
    cat = rewritten.get("category") or candidate.get("target_category")
    if cat not in CATEGORIES:
        cat = candidate.get("target_category") or "Culture & Society"
    source_url = candidate.get("source_url") or candidate.get("link") or ""
    source_name = (rewritten.get("source_name") or candidate.get("source_name") or "").strip()
    today = datetime.date.today()
    return {
        "id": f"news-{today.strftime('%Y%m%d')}-{index}",
        "category": cat,
        "date": today.strftime("%Y.%m.%d"),
        "level": LEVEL_LABEL_MAP.get(lvl, "Intermediate"),
        "levelNum": lvl,
        "isNew": True,
        "image": candidate.get("image") or _fallback_image(cat),
        "source": {"name": source_name, "url": source_url},
        "title": rewritten.get("title", {}),
        "desc": rewritten.get("desc", {}),
        "article": rewritten.get("article", {}),
        "vocab": rewritten.get("vocab", []),
    }


def run() -> None:
    has_key = any([
        os.environ.get("OPENAI_API_KEY"),
        os.environ.get("ANTHROPIC_API_KEY"),
        os.environ.get("GEMINI_API_KEY"),
        os.environ.get("GOOGLE_API_KEY"),
    ])
    if not has_key:
        raise SystemExit("LLM API 키가 없습니다. .env 또는 Actions secrets 를 확인하세요.")

    data = load_lessons(CATEGORIES)
    known = known_source_urls(data.get("featured", []))
    candidates = [
        c for c in collect_candidates()
        if (c.get("source_url") or "") not in known
    ]
    print(f"[2] LLM 가공 시작 (원문 확보 후보 {len(candidates)}개)...")
    new_entries = []
    for i, candidate in enumerate(candidates):
        title = (candidate.get("title") or "")[:28]
        print(f"  - 처리 ({i + 1}/{len(candidates)}): {title}...")
        try:
            rewritten = process_candidate(candidate)
        except Exception as e:
            print(f"    x 에러: {e}")
            continue
        if not rewritten:
            continue
        entry = build_entry(candidate, rewritten, len(new_entries) + 1)
        new_entries.append(entry)
        src = entry["source"]["name"] or "출처 미상"
        print(f"    ok Level {entry['levelNum']} | {entry['category']} | {src}")

    if not new_entries:
        print("추가할 기사가 없습니다.")
        return

    print(f"[3] lessons.json 업데이트 ({len(new_entries)}개 추가)...")
    save_featured(data, new_entries, CATEGORIES)
    print("완료")


if __name__ == "__main__":
    run()
