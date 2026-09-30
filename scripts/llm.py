"""LLM 호출. 키 우선순위: OpenAI -> Anthropic -> Gemini."""

import os
import re
import json
import time
from typing import Any, Dict, List, Optional

from prompts import SYSTEM_PROMPT

# Gemini 기본 후보 모델. GEMINI_MODEL 환경변수가 있으면 그 모델을 가장 먼저 시도합니다.
# (gemini-2.0-flash / gemini-2.5-flash 는 2026년 기준 서비스 종료되어 404 가 돌아옵니다)
GEMINI_DEFAULT_MODELS: List[str] = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]

HTTP_TIMEOUT_MS = 90_000      # 응답이 멈춰도 파이프라인 전체가 멈추지 않도록
RETRY_SLEEP_SECONDS = 3

RETRYABLE_TOKENS = ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "overloaded", "high demand")


def _is_retryable(message: str) -> bool:
    return any(token in message for token in RETRYABLE_TOKENS)


def _gemini_model_candidates() -> List[str]:
    preferred = (os.environ.get("GEMINI_MODEL") or "").strip()
    models = [preferred] if preferred else []
    models.extend(m for m in GEMINI_DEFAULT_MODELS if m not in models)
    return models


def _call_gemini(prompt: str, api_key: str) -> str:
    """새 google-genai SDK 를 우선 사용하고, 없으면 구 SDK 로 넘어갑니다."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _call_gemini_legacy(prompt, api_key)

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=HTTP_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )
    last_error: Optional[Exception] = None
    for model_name in _gemini_model_candidates():
        for attempt in (1, 2):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.3,
                    ),
                )
                text = (resp.text or "").strip()
                if text:
                    print(f"    · Gemini 모델: {model_name}")
                    return text
                last_error = RuntimeError("빈 응답")
                break
            except Exception as e:
                last_error = e
                message = str(e).replace("\n", " ")
                print(f"    · Gemini {model_name} 실패: {message[:90]}")
                if attempt == 1 and _is_retryable(message):
                    time.sleep(RETRY_SLEEP_SECONDS)
                    continue
                break
    raise RuntimeError(f"Gemini 호출 실패: {last_error}")


def _call_gemini_legacy(prompt: str, api_key: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        # GEMINI_MODEL 이 빈 문자열로 넘어올 수 있어(미설정 시크릿) 목록에서 고릅니다.
        model_name=_gemini_model_candidates()[0],
        system_instruction=SYSTEM_PROMPT,
        generation_config={"response_mime_type": "application/json"},
    )
    return model.generate_content(prompt).text


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
        return _call_gemini(prompt, gemini_key)

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
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [제외] JSON 파싱 실패: {e}")
        return None
    if not data.get("is_suitable", False):
        print(f"  [제외] {candidate.get('title')} ({data.get('rejection_reason')})")
        return None
    return data
