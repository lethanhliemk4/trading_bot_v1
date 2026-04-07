import json
import os

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def build_prompt(signal: dict) -> str:
    return f"""
You are a crypto trading assistant.

Evaluate this signal:

Symbol: {signal['symbol']}
Score: {signal['score']}
Price Change (5m): {signal['price_change_5m']}%
Volume: {signal['quote_volume_5m']}
Spike: {signal['volume_spike_ratio']}

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
    try:
        prompt = build_prompt(signal)
        response = model.generate_content(prompt)

        text = response.text.strip()

        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json", "", 1).strip()

        data = json.loads(text)

        decision = str(data.get("decision", "")).upper()
        confidence = float(data.get("confidence", 0))

        if decision == "BUY" and confidence >= 60:
            return {
                "decision": decision,
                "confidence": confidence,
                "reason": data.get("reason", ""),
            }

        return None

    except Exception as e:
        print("AI filter error:", e)
        return None