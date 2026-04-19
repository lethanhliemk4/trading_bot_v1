import json
import logging
import os

import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ===== TEST MODE =====
TEST_MODE_AI_ALWAYS_PASS = settings.is_test_mode

api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None


def build_prompt(signal: dict) -> str:
    return f"""
You are a crypto trading assistant.

Evaluate this signal:

Symbol: {signal['symbol']}
Score: {signal['score']}
Price Change (5m): {signal['price_change_5m']}%
Volume: {signal['quote_volume_5m']}
Spike: {signal['volume_spike_ratio']}
Side: {signal.get('side', 'LONG')}

Decide:
- BUY or SKIP
- Confidence (0-100)
- Short reason

Respond JSON only:
{{
  "decision": "BUY or SKIP",
  "confidence": 0,
  "reason": "short reason"
}}
"""


def ai_filter_signal(signal: dict) -> dict | None:
    if TEST_MODE_AI_ALWAYS_PASS:
        return {
            "decision": "BUY",
            "confidence": 95.0,
            "reason": "test mode always pass",
        }

    if model is None:
        logger.warning("AI filter skipped: GEMINI_API_KEY missing")
        return {
            "decision": "BUY",
            "confidence": 80.0,
            "reason": "fallback pass because Gemini is not configured",
        }

    try:
        prompt = build_prompt(signal)
        response = model.generate_content(prompt)

        text = response.text.strip()

        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json", "", 1).strip()

        data = json.loads(text)

        decision = str(data.get("decision", "")).upper().strip()
        confidence = float(data.get("confidence", 0))
        reason = str(data.get("reason", "")).strip()

        if decision in {"BUY", "PASS"} and confidence >= 60:
            return {
                "decision": "BUY",
                "confidence": confidence,
                "reason": reason or "AI approved",
            }

        return None

    except Exception as e:
        logger.warning("AI filter error: %s", str(e))
        return None
