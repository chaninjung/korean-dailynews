"""카테고리별 검색어, RSS, 사진 대체 주소."""

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
