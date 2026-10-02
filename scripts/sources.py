"""sources.py: 고품질 글로벌 스탠다드 RSS 및 설정 (BBC 코리아 전용)."""

import os

CATEGORIES = [
    "Global & Society",
    "Tech & Future",
    "Health & Mind",
    "Culture & Arts",
    "Travel & Lifestyle",
]

# ── 1. 글로벌 스탠다드 데스크 (BBC 코리아 + BBC 카테고리 피드) ───────────
# BBC 코리아 피드는 정치·범죄 기사가 대부분이라 5개 카테고리의 '후보 풀'이
# 부족합니다. 그래서 한국어 학습 소재감을 위한 BBC 코리아 피드에 더해,
# 카테고리별 주제에 맞는 BBC(영문) 피드를 병행 수집합니다.
# (LLM이 원문 언어와 무관하게 한국어 학습 아티클로 다시 씁니다.)
# 정치(Business & Politics) 카테고리는 폐지했습니다.
CATEGORY_RSS_FEEDS = {
    "Global & Society": [
        "https://feeds.bbci.co.uk/korean/rss.xml",
        "http://feeds.bbci.co.uk/news/world/rss.xml",
    ],
    "Tech & Future": [
        "https://feeds.bbci.co.uk/korean/rss.xml",
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    ],
    "Health & Mind": [
        "https://feeds.bbci.co.uk/korean/rss.xml",
        "http://feeds.bbci.co.uk/news/health/rss.xml",
    ],
    "Culture & Arts": [
        "https://feeds.bbci.co.uk/korean/rss.xml",
        "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    ],
    "Travel & Lifestyle": [
        "https://feeds.bbci.co.uk/korean/rss.xml",
        "https://www.theguardian.com/travel/rss",
        "https://www.theguardian.com/food/rss",
    ],
}

# 본문을 읽을 수 없는 도메인 (Google 쿠키 동의/리다이렉트 페이지 등)
BLOCKED_DOMAINS = (
    "consent.google.com",
    "accounts.google.com",
    "news.google.com",
)

CATEGORY_IMAGE_FALLBACK = {
    "Global & Society": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    "Tech & Future": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    "Health & Mind": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1200&q=80",
    "Culture & Arts": "https://images.unsplash.com/photo-1538485399081-7191377e8241?auto=format&fit=crop&w=1200&q=80",
    "Travel & Lifestyle": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80",
}

LEVEL_LABEL_MAP = {
    1: "Beginner", 2: "Beginner", 3: "Elementary",
    4: "Intermediate", 5: "Intermediate", 6: "Intermediate",
    7: "Advanced", 8: "Advanced", 9: "Proficient",
}

# ── 하루 목표 레벨 계획 ────────────────────────────────────────────────────────
# 한국 뉴스는 원어민 성인용으로 쓰여 있어서 '레벨 1~2 짜리 기사'는 존재하지 않습니다.
# 그래서 레벨을 '판정'하지 않고, 목표 레벨을 정해 그 수준으로 다시 씁니다.
# 원문의 사실은 그대로 두고 문장 길이·어휘·문단 수만 목표 레벨에 맞춥니다.
#
# 이 계획으로 하루 30건이 만들어지고 레벨 1~9가 모두 포함됩니다.
#   초급(L1~3) 9건 / 중급(L4~6) 14건 / 고급(L7~9) 7건
LEVEL_PLAN = {
    # 세계 이슈·과학 등 복잡한 주제는 쉬운 문장으로 풀어쓰기 어려우므로 중급 이상 위주
    "Global & Society": [4, 5, 6, 7, 8, 9],
    "Tech & Future": [4, 5, 6, 7, 8, 9],
    # 생활·예술·여행 주제는 쉬운 문장으로 바꾸기 쉬우므로 초급을 넉넉히
    "Health & Mind": [1, 2, 3, 4, 5, 6],
    "Culture & Arts": [1, 2, 3, 5, 6, 7],
    "Travel & Lifestyle": [1, 2, 3, 4, 5, 6],
}

# 카테고리마다 만들 기사 수. 기본 6 -> 하루 30건.
# 테스트할 때는 ARTICLES_PER_CATEGORY=1 처럼 줄여서 실행할 수 있습니다.
# (시크릿/변수 미설정 시 빈 문자열이 들어오므로 안전하게 처리합니다.)
def _env_int(name: str, default: int, low: int, high: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(low, min(high, value))


ARTICLES_PER_CATEGORY = _env_int("ARTICLES_PER_CATEGORY", 6, 1, 6)


def daily_level_plan() -> dict:
    """오늘 만들 (카테고리 -> 목표 레벨 목록)."""
    return {category: LEVEL_PLAN[category][:ARTICLES_PER_CATEGORY] for category in CATEGORIES}
