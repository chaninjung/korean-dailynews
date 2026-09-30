"""LLM 호출. 키 우선순위: OpenAI -> Anthropic -> Gemini."""

import os
import re
import json
from typing import Any, Dict, Optional

from prompts import SYSTEM_PROMPT


def call_llm(prompt: str) -> str:
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return resp.choices[0].message.content

    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    if gemini_key:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config={"response_mime_type": "application/json"},
        )
        return model.generate_content(prompt).text

    raise ValueError("LLM API 키가 필요합니다 (OPENAI / ANTHROPIC / GEMINI).")


def process_candidate(candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    body = (candidate.get("body") or "").strip()
    if len(body) < 280:
        print(f"  [제외] 원문 전문 없음: {candidate.get('title')}")
        return None
    prompt = (
        "다음 원문 전문을 읽고 Huko 학습 콘텐츠로 재작성해 주세요.\n"
        f"카테고리 힌트: {candidate.get('target_category')}\n"
        f"제목: {candidate.get('title')}\n"
        f"매체: {candidate.get('source_name') or '미상'}\n"
        f"원문 링크: {candidate.get('source_url') or candidate.get('link')}\n\n"
        f"[원문 전문]\n{body}\n"
    )
    raw = call_llm(prompt).strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    if not data.get("is_suitable", False):
        print(f"  [제외] {candidate.get('title')} ({data.get('rejection_reason')})")
        return None
    return data
