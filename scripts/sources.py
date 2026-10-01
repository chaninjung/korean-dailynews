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

# ── 수집 소스 (Engoo 방식: 안전한 섹션만) ──────────────────────────────────
# 연합뉴스 전체 피드가 아니라 학습에 안전한 섹션 RSS만 사용합니다.
#  - 허용: culture(문화), health(건강/보건), industry(산업/기술), international(세계),
#          entertainment(연예가 아닌 문화공연/전시 위주로 LLM이 선별), sports(경기 결과 위주)
#  - 제외: politics(정치), economy(부동산/주식/시세 기사 다수), society(사건사고 다수),
#          local(지역 단신/조례 다수)
# Travel & Experiences 는 world.kbs.co.kr / korea.net 이 RSS 를 제공하지 않아
# culture 피드에서 여행·관광 소재를 LLM 이 선별하는 방식으로 충당합니다.
CATEGORY_RSS_FEEDS = {
    "Business & Politics": [
        "https://www.yna.co.kr/rss/international.xml",
        "https://www.yna.co.kr/rss/industry.xml",
    ],
    "Science & Technology": [
        "https://www.yna.co.kr/rss/industry.xml",
        "https://www.yna.co.kr/rss/international.xml",
    ],
    "Health & Lifestyle": [
        "https://www.yna.co.kr/rss/health.xml",
        "https://www.yna.co.kr/rss/culture.xml",
    ],
    "Culture & Society": [
        "https://www.yna.co.kr/rss/culture.xml",
        "https://www.yna.co.kr/rss/entertainment.xml",
    ],
    "Travel & Experiences": [
        "https://www.yna.co.kr/rss/culture.xml",
        "https://www.yna.co.kr/rss/international.xml",
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
