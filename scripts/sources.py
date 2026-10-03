"""sources.py: 구글 뉴스 커스텀 RSS 및 안전한 버티컬 매체 조합"""

import os
import urllib.parse

CATEGORIES = [
    "Business & Politics",
    "Science & Technology",
    "Health & Lifestyle",
    "Culture & Society",
    "Travel & Experiences",
]

# ── 1. 구글 뉴스 커스텀 RSS 생성기 ───────────────────────────────
# 구글 뉴스의 불리언 연산(+, -, OR, "")을 활용해 완벽하게 필터링된 RSS URL을 만듭니다.
def make_gnews_rss(query: str) -> str:
    # 예: "한국" (K팝 OR 문화) -정치 -사건 -논란
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"

# ── 2. 카테고리별 맞춤형 소스 (한국 맥락 + 안전함) ────────────────
CATEGORY_RSS_FEEDS = {
    # 비즈니스는 정치(여야, 국회)를 빼고 한국 스타트업, 수출, 트렌드에 집중
    "Business & Politics": [
        make_gnews_rss('"한국" (스타트업 OR 경제 트렌드 OR 비즈니스) -정치 -여야 -국회 -논란 -비판'),
    ],

    # 과학/기술은 순수 테크와 한국의 IT 발전상 위주
    "Science & Technology": [
        make_gnews_rss('"한국" (인공지능 OR 우주 OR 신기술 OR IT) -사건 -논란'),
        "https://rss.donga.com/science.xml",  # 동아사이언스 (검증된 과학 매체)
    ],

    # 건강은 의학 칼럼, 식습관, 수면 등 보편적이지만 한국어로 된 정보
    "Health & Lifestyle": [
        make_gnews_rss('"한국" (건강 OR 식습관 OR 수면 OR 웰빙) -사망 -사고'),
        "https://kormedi.com/feed/",          # 코메디닷컴 (국내 1위 건강/의학 전문 매체)
    ],

    # K-컬쳐, 한류, 언어, 전통문화 (정부 정책브리핑 문화 섹션 포함)
    "Culture & Society": [
        make_gnews_rss('"한국" (K팝 OR 전통문화 OR 한류 OR 영화 OR 전시) -논란 -사건 -경찰'),
        "https://www.korea.kr/rss/culture.xml", # 정책브리핑 문화/체육/관광 (매우 깔끔한 국문)
    ],

    # 한국 내 숨겨진 명소, 축제, 여행기
    "Travel & Experiences": [
        make_gnews_rss('"국내여행" (명소 OR 축제 OR 한옥 OR 체험) -사고 -단속 -민원'),
        make_gnews_rss('"한국" (관광 OR 여행지 OR 축제) -사고 -단속 -민원 -논란'),
        # (참고) korea.kr RSS는 2026-07-01 공식 중단되어 사용 불가
    ],
}

# (참고) 구글 뉴스 RSS는 구글 도메인이지만 원문 링크를 타고 넘어가므로 BLOCKED_DOMAINS 에서 구글을 뺄 필요가 있음
# 단, 구글 리다이렉트 동의 페이지는 여전히 필터링
BLOCKED_DOMAINS = (
    "consent.google.com",
    "accounts.google.com",
)

# ── 3. 중립적이고 세련된 스톡 이미지 고정 ──────────────────────────────
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

LEVEL_PLAN = {
    "Business & Politics": [4, 5, 6, 7, 8, 9],
    "Science & Technology": [4, 5, 6, 7, 8, 9],
    "Health & Lifestyle": [1, 2, 3, 4, 5, 6],
    "Culture & Society": [1, 2, 3, 5, 6, 7],
    "Travel & Experiences": [1, 2, 3, 4, 5, 6],
}

def _env_int(name: str, default: int, low: int, high: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(low, min(high, value))

ARTICLES_PER_CATEGORY = _env_int("ARTICLES_PER_CATEGORY", 6, 1, 6)

def daily_level_plan() -> dict:
    return {category: LEVEL_PLAN[category][:ARTICLES_PER_CATEGORY] for category in CATEGORIES}
