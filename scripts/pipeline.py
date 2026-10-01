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

from collect import collect_pools
from llm import process_candidate, LLM_CALL_SLEEP
from sources import CATEGORIES, CATEGORY_IMAGE_FALLBACK, LEVEL_LABEL_MAP, daily_level_plan
from store import known_source_urls, load_lessons, save_featured
import time


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
        # 원문 이미지 절대 금지, Fallback 이미지만 무조건 사용
        "image": _fallback_image(cat),
        "source": {"name": source_name, "url": source_url},
        "title": rewritten.get("title", {}),
        "desc": rewritten.get("desc", {}),
        "article": rewritten.get("article", {}),
        "vocab": rewritten.get("vocab", []),
        "questions": rewritten.get("questions", []),
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
    plan = daily_level_plan()
    total_target = sum(len(v) for v in plan.values())
    print(f"[0] 오늘 목표: 총 {total_target}건")
    pools = collect_pools(plan, known)
    print(f"[2] LLM 가공 시작 (목표 {total_target}건)...")
    new_entries = []
    for category in CATEGORIES:
        targets = plan.get(category, [])
        pool = list(pools.get(category, []))
        print(f"  - [{category}] 목표 {len(targets)}건, 후보풀 {len(pool)}건")
        for target_level in targets:
            rewritten = None
            used_candidate = None
            while pool:
                candidate = pool.pop(0)
                title = (candidate.get("title") or "")[:28]
                print(f"    · L{target_level} 시도: {title}...")
                try:
                    rewritten = process_candidate(candidate, target_level)
                except Exception as e:
                    print(f"      x 에러: {e}")
                    rewritten = None
                if rewritten:
                    used_candidate = candidate
                    break
                if LLM_CALL_SLEEP:
                    time.sleep(LLM_CALL_SLEEP)
            if not rewritten or not used_candidate:
                print(f"    ! [{category}] L{target_level} 후보 소진으로 건너뜀")
                continue
            entry = build_entry(used_candidate, rewritten, len(new_entries) + 1)
            new_entries.append(entry)
            src = entry["source"]["name"] or "출처 미상"
            print(f"      ok Level {entry['levelNum']} | {entry['category']} | {src}")
            if LLM_CALL_SLEEP:
                time.sleep(LLM_CALL_SLEEP)

    if not new_entries:
        print("추가할 기사가 없습니다.")
        return

    print(f"[3] lessons.json 업데이트 ({len(new_entries)}개 추가)...")
    save_featured(data, new_entries, CATEGORIES)
    print("완료")


if __name__ == "__main__":
    run()
