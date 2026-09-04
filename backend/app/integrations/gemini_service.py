import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger


class GeminiLLMService:
    """
    Google Gemini AI LLM Service.
    Performs autonomous root cause diagnosis, evidence synthesis, and structured recovery reasoning.
    """

    def __init__(self):
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def analyze_failure(
        self,
        transaction_id: str,
        amount: float,
        payment_method: str,
        failure_reason: str,
        bank: str,
        attempt_number: int,
        customer_name: str,
        customer_success_rate: float,
        retrieved_policy: str,
    ) -> dict[str, Any] | None:
        """
        Calls Google Gemini API to analyze payment failure and generate structured reasoning.
        """
        api_key = settings.GEMINI_API_KEY or getattr(settings, "LLM_API_KEY", "")
        if not api_key or api_key.startswith("your-") or "gemini-api-key" in api_key:
            logger.info("No Gemini API key configured. Using deterministic reasoning engine.")
            return None

        prompt = f"""
You are the RootCauseAgent & RecoveryStrategyAgent in RazorRecover AI, an autonomous fintech revenue recovery platform.

Analyze this failed transaction:
- Transaction ID: {transaction_id}
- Amount: INR {amount:,.2f}
- Payment Method: {payment_method.upper()}
- Gateway Failure Reason: {failure_reason}
- Bank / PSP Network: {bank}
- Attempt Number: {attempt_number}
- Customer Name: {customer_name}
- Customer Historical Success Rate: {int(customer_success_rate * 100)}%

Relevant Merchant Policy Context:
{retrieved_policy}

Task:
Diagnose the failure root cause and provide evidence. Output strictly valid JSON matching this schema:
{{
  "root_cause": "Payment Method Degradation" | "Authorization Blip" | "Checkout Abandonment" | "Insufficient Funds" | "Mandate Expired",
  "confidence": 0.91,
  "reason": "Detailed summary of root cause",
  "evidence": [
    "Evidence point 1",
    "Evidence point 2",
    "Evidence point 3"
  ],
  "recommended_action": "payment_link" | "retry" | "reminder" | "human_review" | "do_nothing"
}}
"""

        candidate_models = [settings.GEMINI_MODEL, "gemini-2.0-flash", "gemini-1.5-flash"]
        # Deduplicate while preserving order
        candidate_models = list(dict.fromkeys(candidate_models))

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=12.0) as client:
            for model_name in candidate_models:
                endpoint = f"{self.base_url}/{model_name}:generateContent?key={api_key}"
                try:
                    res = await client.post(endpoint, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(raw_text)
                        logger.info(f"Gemini AI ({model_name}) reasoning completed for {transaction_id}: {parsed.get('root_cause')}")
                        return parsed
                    elif res.status_code == 404:
                        logger.info(f"Model {model_name} not available, trying next fallback model...")
                        continue
                    else:
                        logger.warning(f"Gemini API ({model_name}) returned status {res.status_code}: {res.text}")
                except Exception as e:
                    logger.warning(f"Gemini API ({model_name}) invocation error: {e}")

        logger.info("Falling back to deterministic reasoning engine.")
        return None


gemini_service = GeminiLLMService()
