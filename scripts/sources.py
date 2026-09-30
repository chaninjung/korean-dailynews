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

CATEGORY_RSS_FALLBACK = {
    "Business & Politics": "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C%20%EC%A0%95%EC%B1%85&hl=ko&gl=KR&ceid=KR:ko",
    "Science & Technology": "https://news.google.com/rss/search?q=IT%20%EA%B3%BC%ED%95%99&hl=ko&gl=KR&ceid=KR:ko",
    "Health & Lifestyle": "https://news.google.com/rss/search?q=%EA%B1%B4%EA%B0%95%20%EC%8B%9D%EC%83%9D%ED%99%9C&hl=ko&gl=KR&ceid=KR:ko",
    "Culture & Society": "https://news.google.com/rss/search?q=%EB%AC%B8%ED%99%94%20%EC%82%AC%ED%98%8C&hl=ko&gl=KR&ceid=KR:ko",
    "Travel & Experiences": "https://news.google.com/rss/search?q=%ED%95%9C%EA%B5%AD%20%EC%97%AC%ED%96%89&hl=ko&gl=KR&ceid=KR:ko",
}

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
