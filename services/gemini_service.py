from google import genai
import os
import json

from typing import List, Dict, Any
def get_gemini_findings(
    columns: List[str],
    samples: List[Dict[str, Any]]
):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("⚠ GEMINI_API_KEY not set")
        return []

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an AI fairness auditor.

Analyze dataset samples:
{json.dumps(samples, indent=2)}

Return JSON:
[
  {{
    "column": "name",
    "type": "sensitive|proxy",
    "reason": "short explanation"
  }}
]
"""

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        if not response or not hasattr(response, "text") or not response.text:
            print("⚠ Empty Gemini response")
            return []

        text = response.text.strip()

        try:
            return json.loads(text)
        except:
            return []

    except Exception as e:
        print("Gemini error:", e)
        return []