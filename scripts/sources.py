"""카테고리별 검색어, RSS, 사진 대체 주소, 하루 목표 레벨 계획."""

import os

CATEGORIES = [
    "Business & Politics",
    "Science & Technology",
    "Health & Lifestyle",
    "Culture & Society",
    "Travel & Experiences",
]

CATEGORY_SEARCH_QUERIES = {
    "Business & Politics": ["한국 경제 정책", "글로벌 무역"],
    "Science & Technology": ["인공지능 IT 신기술", "우주 과학 기술"],
    "Health & Lifestyle": ["건강 생활습관", "공중보건 의료"],
    "Culture & Society": ["한국 전통 문화", "한국어 교육 한글"],
    "Travel & Experiences": ["한국 여행 관광", "한국 지역 축제"],
}

# Google News RSS(https://news.google.com/rss/search?...)는 2024년 개편 이후
# <link> 가 news.google.com/rss/articles/... 리다이렉트 주소가 되어 원문을 읽을 수 없고,
# 해외 IP 에서는 쿠키 동의 페이지로 넘어가 본문 대신 동의 문구만 수집됩니다.
# 그래서 <link> 가 기사 원문 주소인 언론사 자체 RSS 를 사용합니다. (연합뉴스 카테고리 피드)
CATEGORY_RSS_FEEDS = {
    "Business & Politics": [
        "https://www.yna.co.kr/rss/economy.xml",
        "https://www.yna.co.kr/rss/politics.xml",
    ],
    "Science & Technology": [
        "https://www.yna.co.kr/rss/industry.xml",
    ],
    "Health & Lifestyle": [
        "https://www.yna.co.kr/rss/health.xml",
    ],
    "Culture & Society": [
        "https://www.yna.co.kr/rss/culture.xml",
        "https://www.yna.co.kr/rss/society.xml",
    ],
    "Travel & Experiences": [
        "https://www.yna.co.kr/rss/local.xml",
        "https://www.yna.co.kr/rss/culture.xml",
    ],
}

# 본문을 읽을 수 없는 도메인 (Google 쿠키 동의/리다이렉트 페이지 등)
BLOCKED_DOMAINS = (
    "consent.google.com",
    "accounts.google.com",
    "news.google.com",
)

CATEGORY_IMAGE_FALLBACK = {
    "Business & Politics": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=1200&q=80",
    "Science & Technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
    "Health & Lifestyle": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1200&q=80",
    "Culture & Society": "https://images.unsplash.com/photo-1538485399081-7191377e8241?auto=format&fit=crop&w=1200&q=80",
    "Travel & Experiences": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80",
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
    # 복잡한 주제는 쉬운 문장으로 풀어쓰기 어려우므로 중급 이상 위주
    "Business & Politics": [4, 5, 6, 7, 8, 9],
    "Science & Technology": [4, 5, 6, 7, 8, 9],
    # 생활 주제는 쉬운 문장으로 바꾸기 쉬우므로 초급을 넉넉히
    "Health & Lifestyle": [1, 2, 3, 4, 5, 6],
    "Culture & Society": [1, 2, 3, 5, 6, 7],
    "Travel & Experiences": [1, 2, 3, 4, 5, 6],
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
