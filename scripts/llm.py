"""LLM 호출. 키 우선순위: OpenAI -> Anthropic -> Gemini."""

import os
import re
import json
import time
from typing import Any, Dict, List, Optional

from prompts import SYSTEM_PROMPT, build_user_prompt

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

HTTP_TIMEOUT_MS = 120_000     # 응답이 멈춰도 파이프라인 전체가 멈추지 않도록
RETRY_SLEEP_SECONDS = 8


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    try:
        return float(raw)
    except ValueError:
        return default


# 하루 30건을 연속 호출하므로, API 속도 제한에 걸리지 않게 호출 사이에 쉬는 시간(초)
# 짧게 쉬면 429(할당량 초과)로 실패-재시도가 반복돼 오히려 전체가 느려집니다.
LLM_CALL_SLEEP = _env_float("LLM_CALL_SLEEP", 4.0)

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
                        max_output_tokens=8000,
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
            max_tokens=8000,
        )
        return resp.choices[0].message.content

    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    if gemini_key:
        return _call_gemini(prompt, gemini_key)

    raise ValueError("LLM API 키가 필요합니다 (OPENAI / ANTHROPIC / GEMINI).")


def process_candidate(candidate: Dict[str, Any], target_level: int) -> Optional[Dict[str, Any]]:
    """원문을 지정된 목표 레벨(target_level)에 맞춰 다시 쓴다."""
    body = (candidate.get("body") or "").strip()
    if len(body) < 280:
        print(f"  [제외] 원문 전문 없음: {candidate.get('title')}")
        return None
    prompt = build_user_prompt(candidate, target_level)
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
    data["vocab"] = _normalize_vocab(data.get("vocab"))
    data["questions"] = _normalize_questions(data.get("questions"))
    return data


def _normalize_vocab(vocab: Any) -> List[Dict[str, str]]:
    """예전 단일 문자열 형식을 새 객체 형식으로 변환한다 (하위 호환)."""
    if not isinstance(vocab, list):
        return []
    normalized: List[Dict[str, str]] = []
    for item in vocab:
        if isinstance(item, dict) and item.get("word"):
            normalized.append({
                "word": str(item.get("word", "")).strip(),
                "meaning_en": str(item.get("meaning_en", "")).strip(),
                "meaning_hu": str(item.get("meaning_hu", "")).strip(),
            })
        elif isinstance(item, str) and item.strip():
            normalized.append(_parse_legacy_vocab(item.strip()))
    return [v for v in normalized if v.get("word")][:5]


def _parse_legacy_vocab(text: str) -> Dict[str, str]:
    """'단어 (English) - Magyar' 같은 예전 문자열을 객체로 변환."""
    word, meaning_en, meaning_hu = text, "", ""
    if " - " in text:
        left, meaning_hu = text.split(" - ", 1)
    else:
        left, meaning_hu = text, ""
    match = re.match(r"^(.*?)\s*\((.*?)\)\s*$", left.strip())
    if match:
        word, meaning_en = match.group(1).strip(), match.group(2).strip()
    else:
        word = left.strip()
    return {"word": word, "meaning_en": meaning_en.strip(), "meaning_hu": meaning_hu.strip()}


def _normalize_questions(questions: Any) -> List[Dict[str, str]]:
    if not isinstance(questions, list):
        return []
    normalized: List[Dict[str, str]] = []
    for item in questions:
        if isinstance(item, dict):
            normalized.append({
                "kor": str(item.get("kor", "")).strip(),
                "eng": str(item.get("eng", "")).strip(),
                "hu": str(item.get("hu", "")).strip(),
            })
        elif isinstance(item, str) and item.strip():
            normalized.append({"kor": item.strip(), "eng": "", "hu": ""})
    return [q for q in normalized if q.get("kor")][:3]
