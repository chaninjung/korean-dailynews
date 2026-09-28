"""
Huko News Data Pipeline
수집(네이버 검색 API / RSS) -> LLM 가공 -> data/lessons.json 업데이트
"""

import os
import re
import json
import datetime
import html
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS_PATH = os.path.join(BASE_DIR, "data", "lessons.json")

CATEGORIES = [
    "Business & Politics",
    "Science & Technology",
    "Culture & Society",
    "Travel & Experiences"
]

CATEGORY_SEARCH_QUERIES = {
    "Business & Politics": ["한국 경제 정책", "글로벌 무역", "거시 경제 산업"],
    "Science & Technology": ["인공지능 IT 신기술", "우주 과학 기술", "친환경 신재생에너지"],
    "Culture & Society": ["한국 전통 문화 K컬처", "한국어 교육 한글", "현대 사회 라이프스타일"],
    "Travel & Experiences": ["한국 유네스코 여행 명소", "한국 지역 축제 관광", "한국 자연 국립공원"]
}

CATEGORY_RSS_FALLBACK = {
    "Business & Politics": "https://news.google.com/rss/search?q=%EA%B2%BD%EC%A0%9C%20%EC%A0%95%EC%B1%85&hl=ko&gl=KR&ceid=KR:ko",
    "Science & Technology": "https://news.google.com/rss/search?q=IT%20%EA%B3%BC%ED%95%99%20%EA%B8%B0%EC%88%A0&hl=ko&gl=KR&ceid=KR:ko",
    "Culture & Society": "https://news.google.com/rss/search?q=%EB%AC%B8%ED%99%94%20%EC%82%AC%ED%98%8C&hl=ko&gl=KR&ceid=KR:ko",
    "Travel & Experiences": "https://news.google.com/rss/search?q=%ED%95%9C%EA%B5%AD%20%EC%97%AC%ED%96%89%20%EA%B4%80%EA%B4%91&hl=ko&gl=KR&ceid=KR:ko"
}

CATEGORY_UNSPLASH_FALLBACK = {
    "Business & Politics": "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&w=800&q=80",
    "Science & Technology": "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
    "Culture & Society": "https://images.unsplash.com/photo-1538485399081-7191377e8241?auto=format&fit=crop&w=800&q=80",
    "Travel & Experiences": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=800&q=80"
}

LEVEL_LABEL_MAP = {
    1: "Beginner", 2: "Beginner", 3: "Elementary",
    4: "Intermediate", 5: "Intermediate", 6: "Intermediate",
    7: "Advanced", 8: "Advanced", 9: "Proficient"
}

SYSTEM_PROMPT = """당신은 외국인을 위한 한국어 학습 뉴스 플랫폼 'Huko'의 전문 콘텐츠 에디터이자 언어학자입니다.
수집된 뉴스 기사를 분석하여 가이드라인 위반 여부를 확인하고, 외국인 학습자를 위한 레벨별 한국어 학습 아티클로 재작성하세요.

[콘텐츠 가이드라인]
1. 허용 카테고리: "Travel & Experiences", "Culture & Society", "Science & Technology", "Business & Politics"
2. 엄격한 배제 기준 (위반 시 is_suitable=false):
   - 연예인 사생활, 자극적 루머, 가십성 기사
   - 극단적인 정치 대립/비방
   - 자극적인 범죄, 잔혹한 사건사고
   - 단순 찌라시 및 클릭베이트 기사
3. 레벨 체계 (1~9):
   - Level 1~3: TOPIK 1~2 수준 (초급)
   - Level 4~6: TOPIK 3~4 수준 (중급)
   - Level 7~9: TOPIK 5~6 수준 (고급)
4. 언어 지원: title, desc, article은 반드시 kor, eng, hu 세 가지 언어로 각각 작성하세요.
5. vocab 리스트: '한국어단어 (영어뜻) - 헝가리어뜻' 형식 문자열 3개.

반드시 아래 JSON 형식으로만 응답하세요:
{
  "is_suitable": true,
  "rejection_reason": null,
  "category": "Science & Technology",
  "assessed_level": 6,
  "title": { "kor": "한국어 제목", "eng": "English Title", "hu": "Magyar Cím" },
  "desc": { "kor": "한국어 요약 1줄", "eng": "English summary", "hu": "Magyar összefoglaló" },
  "article": { "kor": "한국어 본문 2~4문장", "eng": "English translation", "hu": "Magyar fordítás" },
  "vocab": ["단어1 (En) - Hu", "단어2 (En) - Hu", "단어3 (En) - Hu"]
}
"""

def clean_html_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()

def fetch_naver_news(query: str, client_id: str, client_secret: str, count: int = 2) -> List[Dict[str, Any]]:
    url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(query)}&display={count}&sort=sim"
    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    items = []
    for item in resp.json().get("items", []):
        items.append({
            "title": clean_html_text(item.get("title", "")),
            "description": clean_html_text(item.get("description", "")),
            "link": item.get("originallink") or item.get("link", ""),
            "pubDate": item.get("pubDate", "")
        })
    return items

def fetch_rss_news(rss_url: str, count: int = 2) -> List[Dict[str, Any]]:
    resp = requests.get(rss_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall(".//item")[:count]:
        items.append({
            "title": clean_html_text(item.findtext("title", "")),
            "description": clean_html_text(item.findtext("description", "")),
            "link": item.findtext("link", ""),
            "pubDate": item.findtext("pubDate", "")
        })
    return items

def collect_candidates() -> List[Dict[str, Any]]:
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    candidates = []

    print("[1] 뉴스 수집 진행 중...")
    for category in CATEGORIES:
        gathered = []
        if client_id and client_secret:
            for q in CATEGORY_SEARCH_QUERIES.get(category, [category]):
                try:
                    res = fetch_naver_news(q, client_id, client_secret, count=1)
                    gathered.extend(res)
                    if len(gathered) >= 2: break
                except Exception as e:
                    print(f"  - 네이버 API 실패 ({q}): {e}")
        if not gathered:
            rss = CATEGORY_RSS_FALLBACK.get(category)
            if rss:
                try:
                    gathered = fetch_rss_news(rss, count=1)
                except Exception as e:
                    print(f"  - RSS 수집 실패 ({rss}): {e}")
        for item in gathered[:1]:
            if item:
                item["target_category"] = category
                candidates.append(item)
    return candidates

def call_llm(prompt: str) -> str:
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return resp.choices[0].message.content

    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text

    if gemini_key:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"}
        )
        resp = model.generate_content(prompt)
        return resp.text

    raise ValueError("LLM API 키가 필요합니다 (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY).")

def process_candidate(candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    prompt = f"""다음 뉴스를 Huko 학습 콘텐츠로 재작성해 주세요:
카테고리: {candidate.get('target_category')}
제목: {candidate.get('title')}
요약: {candidate.get('description')}
링크: {candidate.get('link')}
"""
    raw = call_llm(prompt).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n", "", raw)
        raw = re.sub(r"\n```$", "", raw)
    data = json.loads(raw)
    if not data.get("is_suitable", False):
        print(f"  [제외] {candidate.get('title')} ({data.get('rejection_reason')})")
def run():
    candidates = collect_candidates()
    new_entries = []
    print(f"[2] LLM 가공 시작 (후보 {len(candidates)}개)...")
    for i, c in enumerate(candidates):
        try:
            print(f"  - 처리 ({i+1}/{len(candidates)}): {c['title'][:25]}...")
            res = process_candidate(c)
            if res:
                lvl = int(res.get("assessed_level", 6))
                cat = res.get("category") or c.get("target_category") or "Culture & Society"
                img = CATEGORY_UNSPLASH_FALLBACK.get(cat, CATEGORY_UNSPLASH_FALLBACK["Culture & Society"])
                t_str = datetime.date.today().strftime("%Y%m%d")
                entry = {
                    "id": f"news-{t_str}-{len(new_entries)+1}",
                    "category": cat,
                    "level": LEVEL_LABEL_MAP.get(lvl, "Intermediate"),
                    "levelNum": lvl,
                    "isNew": True,
                    "image": img,
                    "title": res.get("title", {}),
                    "desc": res.get("desc", {}),
                    "article": res.get("article", {}),
                    "vocab": res.get("vocab", [])
                }
                new_entries.append(entry)
                print(f"    ✓ 완료: Level {lvl} | {cat}")
        except Exception as e:
            print(f"    ✗ 에러: {e}")

    if not new_entries:
        print("추가할 기사가 없습니다.")
        return

    print(f"[3] lessons.json 업데이트 ({len(new_entries)}개 추가)...")
    data = {"featured": [], "categories": CATEGORIES}
    if os.path.exists(LESSONS_PATH):
        with open(LESSONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

    for item in data.get("featured", []):
        item["isNew"] = False

    data["featured"] = (new_entries + data.get("featured", []))[:20]
    with open(LESSONS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✓ 완료!")

if __name__ == "__main__":
    run()
