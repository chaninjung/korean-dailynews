"""LLM 호출. 키 우선순위: OpenAI -> Anthropic -> Gemini."""

import os
import random
import re
import json
import time
import warnings
from typing import Any, Dict, List, Optional

from prompts import SYSTEM_PROMPT, build_user_prompt

# AFC 경고는 단순 텍스트/JSON 생성과 무관한 SDK 내부 안내이므로 숨긴다.
# (실제 호출은 권장 경로인 Chat.send_message 로 옮겼다.)
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

# ── 모델 폴백: 메인 1개 + 경량 폴백 1개, 총 2단계만 사용합니다. ─────────────
# GEMINI_MODEL 환경변수가 있으면 그 모델이 메인 자리를 대신합니다.
GEMINI_DEFAULT_MODELS: List[str] = [
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]

HTTP_TIMEOUT_MS = 120_000     # 응답이 멈춰도 파이프라인 전체가 멈추지 않도록
MAX_ATTEMPTS_PER_MODEL = 3    # 모델당 최대 재시도 횟수
BACKOFF_BASE_SECONDS = 4.0    # 지수 백오프 시작값: 4s -> 8s -> 16s (+지터)
BACKOFF_MAX_SECONDS = 30.0
TIER_SLEEP_SECONDS = 3.0      # 메인 모델 소진 후 폴백 모델로 넘어가기 전 휴식


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    try:
        return float(raw)
    except ValueError:
        return default


# 하루 30건을 연속 호출하므로, API 속도 제한에 걸리지 않게 호출 사이에 쉬는 시간(초)
# 짧게 쉬면 429(할당량 초과)로 실패-재시도가 반복돼 오히려 전체가 느려집니다.
LLM_CALL_SLEEP = _env_float("LLM_CALL_SLEEP", 4.0)

RETRYABLE_TOKENS = (
    "429", "500", "502", "503", "504",
    "RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED",
    "overloaded", "high demand", "rate limit", "quota",
)


def _is_retryable(message: str) -> bool:
    lowered = (message or "").lower()
    return any(token.lower() in lowered for token in RETRYABLE_TOKENS)


def _backoff_sleep(fail_count: int) -> None:
    """지수 백오프: 4s -> 8s -> 16s (+최대 1s 지터, 상한 30s)."""
    delay = min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * (2 ** max(0, fail_count - 1)))
    time.sleep(delay + random.uniform(0.0, 1.0))


def extract_json(raw: str) -> Optional[Dict[str, Any]]:
    """LLM 응답에서 순수 JSON 객체를 뽑아 파싱한다.

    - 마크다운 펜스(```json ... ```) 제거
    - 앞뒤 설명 문구 제거: 첫 '{' 부터 마지막 '}' 까지만 잘라냄
    - 잘린 JSON(Unterminated string) 은 수리하지 않고 None 반환
    """
    text = (raw or "").strip()
    if not text:
        return None
    # 1) 마크다운 펜스 벗기기
    if "```" in text:
        fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if fence:
            text = fence.group(1).strip()
        else:
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
    # 2) 순수 JSON 이 아니면 첫 '{' ~ 마지막 '}' 만 잘라냄
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        text = text[start:end + 1]
    # 3) 꼬리표(Extra data) 방지: 마지막 '}' 뒤는 버린다
    if not text.endswith("}"):
        end = text.rfind("}")
        if end == -1:
            return None
        text = text[:end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _gemini_model_candidates() -> List[str]:
    preferred = (os.environ.get("GEMINI_MODEL") or "").strip()
    models = [preferred] if preferred else []
    models.extend(m for m in GEMINI_DEFAULT_MODELS if m not in models)
    return models


def _call_gemini(prompt: str, api_key: str) -> str:
    """새 google-genai SDK 를 우선 사용하고, 없으면 구 SDK 로 넘어갑니다.

    - 권장 경로인 Chat.send_message 로 호출해 AFC 경고를 원천 제거
    - response_mime_type=application/json 으로 JSON 모드 강제
    - 429/503/504 는 지수 백오프로 재시도, 모델당 소진 후에만 다음 모델로 폴백
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _call_gemini_legacy(prompt, api_key)

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=HTTP_TIMEOUT_MS),
    )
    last_error: Optional[Exception] = None
    for model_name in _gemini_model_candidates():
        fail_count = 0
        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                chat = client.chats.create(
                    model=model_name,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        temperature=0.3,
                        # 3개 언어 본문 + vocab + questions 가 한 번에 나오므로
                        # 잘림(Unterminated string) 방지를 위해 넉넉히 준다.
                        max_output_tokens=16000,
                    ),
                )
                # 순수 텍스트만 보낸다. tools / function-calling 설정은 일절 넘기지 않는다.
                resp = chat.send_message(prompt)
                text = (getattr(resp, "text", "") or "").strip()
                if text:
                    if model_name != _gemini_model_candidates()[0]:
                        print(f"    · 폴백 모델 사용: {model_name}")
                    if attempt > 1:
                        print(f"    · Gemini 모델: {model_name} ({attempt}번째 시도에 성공)")
                    return text
                last_error = RuntimeError("빈 응답")
                break
            except Exception as e:
                last_error = e
                message = str(e).replace("\n", " ")
                if _is_retryable(message) and attempt < MAX_ATTEMPTS_PER_MODEL:
                    fail_count += 1
                    print(f"    · Gemini {model_name} 재시도 {attempt}/{MAX_ATTEMPTS_PER_MODEL}: {message[:90]}")
                    _backoff_sleep(fail_count)
                    continue
                print(f"    · Gemini {model_name} 실패: {message[:90]}")
                break
        print(f"    · {model_name} 재시도 소진, 다음 모델로 폴백")
        if TIER_SLEEP_SECONDS:
            time.sleep(TIER_SLEEP_SECONDS)
    raise RuntimeError(f"Gemini 호출 실패: {last_error}")


def _call_gemini_legacy(prompt: str, api_key: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        # GEMINI_MODEL 이 빈 문자열로 넘어올 수 있어(미설정 시크릿) 목록에서 고릅니다.
        model_name=_gemini_model_candidates()[0],
        system_instruction=SYSTEM_PROMPT,
        generation_config={
            "response_mime_type": "application/json",
            "max_output_tokens": 16000,
        },
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
    data = extract_json(raw)
    if data is None:
        print(f"  [제외] JSON 파싱 실패: {raw[:80]!r}")
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
