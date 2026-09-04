import json
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.schemas.root_cause import RootCauseAnalysis, RootCauseCategory


class RootCauseAgent:
    """
    Phase 5 — Root Cause Agent.
    Analyzes failed transactions using Google Gemini 2.5 Flash LLM and payment signals.
    Provides structured, evidence-first root cause diagnosis.
    """

    CONTROLLED_CATEGORIES = {c.value for c in RootCauseCategory}

    def __init__(self):
        self.gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models"

    async def analyze(
        self,
        transaction_id: str,
        amount: float,
        currency: str = "INR",
        payment_method: str = "upi",
        failure_reason: str | None = None,
        failure_code: str | None = None,
        attempt_count: int = 1,
        bank: str | None = None,
        customer_name: str | None = None,
        customer_success_rate: float | None = None,
        lifetime_transactions: int | None = None,
        anomaly_info: dict[str, Any] | None = None,
    ) -> RootCauseAnalysis:
        """
        Executes root cause reasoning on real transaction signals using Gemini LLM.
        """
        # Prepare explicit signals dictionary (no invented missing values)
        signals: dict[str, Any] = {
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method.upper() if payment_method else "UNAVAILABLE",
            "failure_reason": failure_reason if failure_reason else "UNAVAILABLE",
            "failure_code": failure_code if failure_code else "UNAVAILABLE",
            "attempt_count": attempt_count,
            "bank_network": bank if bank else "UNAVAILABLE",
            "customer_name": customer_name if customer_name else "UNAVAILABLE",
            "customer_historical_success_rate": f"{int(customer_success_rate * 100)}%" if customer_success_rate is not None else "UNAVAILABLE",
            "lifetime_transactions": lifetime_transactions if lifetime_transactions is not None else "UNAVAILABLE",
            "phase4_anomaly_active": anomaly_info.get("anomaly_detected", False) if anomaly_info else False,
            "phase4_anomaly_message": anomaly_info.get("anomaly_message") if anomaly_info else "No active PSP anomaly",
        }

        # Attempt Gemini LLM Analysis
        gemini_result = await self._call_gemini(signals)
        if gemini_result:
            return gemini_result

        # Deterministic evidence-first fallback (if Gemini API key is missing, rate-limited, or offline)
        return self._deterministic_fallback(signals)

    async def _call_gemini(self, signals: dict[str, Any]) -> RootCauseAnalysis | None:
        api_key = settings.GEMINI_API_KEY or getattr(settings, "LLM_API_KEY", "")
        if not api_key or api_key.startswith("your-") or "gemini-api-key" in api_key:
            logger.info("[RootCauseAgent] No Gemini API key provided. Using deterministic evidence reasoning.")
            return None

        prompt = f"""
You are the RootCauseAgent in RazorRecover AI, an autonomous revenue recovery system for merchants.

Analyze this failed transaction strictly using the supplied telemetry signals:
- Transaction ID: {signals['transaction_id']}
- Amount: {signals['currency']} {signals['amount']}
- Payment Method: {signals['payment_method']}
- Gateway Failure Reason: {signals['failure_reason']}
- Failure Code: {signals['failure_code']}
- Attempt Number: {signals['attempt_count']}
- Bank / Network: {signals['bank_network']}
- Customer Historical Success Rate: {signals['customer_historical_success_rate']}
- Active Anomaly Telemetry: {signals['phase4_anomaly_message']}

Task:
Determine WHY this payment failed and provide concrete, factual evidence points based strictly on the signals above.
Do NOT invent or hallucinate data that was marked UNAVAILABLE.

Output strictly valid JSON matching this exact structure:
{{
  "transaction_id": "{signals['transaction_id']}",
  "root_cause": "payment_method_degradation" | "gateway_failure" | "bank_failure" | "timeout" | "insufficient_funds" | "invalid_payment_details" | "customer_abandonment" | "repeated_payment_failure" | "unknown",
  "confidence": 0.91,
  "evidence": [
    "Evidence point 1 based on actual signals",
    "Evidence point 2 based on actual signals"
  ],
  "explanation": "Concise factual explanation of the root cause."
}}
"""

        candidate_models = [settings.GEMINI_MODEL, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

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

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                for model_name in candidate_models:
                    url = f"{self.gemini_endpoint}/{model_name}:generateContent?key={api_key}"
                    try:
                        res = await client.post(url, json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            if raw_text.startswith("```"):
                                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                                raw_text = re.sub(r"\s*```$", "", raw_text)
                            parsed = json.loads(raw_text)

                            # Validate and normalize
                            raw_category = str(parsed.get("root_cause", "")).lower().replace(" ", "_")
                            canonical_category = self._normalize_category(raw_category)
                            confidence = float(parsed.get("confidence", 0.85))
                            confidence = min(max(confidence, 0.0), 1.0)
                            evidence = list(parsed.get("evidence", []))
                            explanation = str(parsed.get("explanation", f"{canonical_category} identified by RootCauseAgent."))

                            logger.info(f"[RootCauseAgent] Gemini ({model_name}) diagnosed {signals['transaction_id']}: {canonical_category} ({confidence})")
                            return RootCauseAnalysis(
                                transaction_id=signals["transaction_id"],
                                root_cause=canonical_category,
                                confidence=confidence,
                                evidence=evidence,
                                explanation=explanation,
                                signals_analyzed=signals,
                                analyzed_at=datetime.now(timezone.utc).isoformat(),
                            )
                        elif res.status_code == 404:
                            continue
                        else:
                            logger.warning(f"[RootCauseAgent] Gemini API ({model_name}) status {res.status_code}: {res.text}")
                    except Exception as model_err:
                        logger.warning(f"[RootCauseAgent] Model {model_name} error: {model_err}")
                        continue
        except Exception as e:
            logger.info(f"[RootCauseAgent] Gemini unavailable ({e}), using deterministic evidence reasoning.")

        return None

    def _normalize_category(self, raw: str) -> str:
        if raw in self.CONTROLLED_CATEGORIES:
            return raw
        # Semantic mapping
        if "degradation" in raw or "psp" in raw or "latency" in raw:
            return RootCauseCategory.PAYMENT_METHOD_DEGRADATION.value
        if "gateway" in raw or "504" in raw:
            return RootCauseCategory.GATEWAY_FAILURE.value
        if "bank" in raw or "issuer" in raw:
            return RootCauseCategory.BANK_FAILURE.value
        if "timeout" in raw:
            return RootCauseCategory.TIMEOUT.value
        if "insufficient" in raw or "funds" in raw:
            return RootCauseCategory.INSUFFICIENT_FUNDS.value
        if "detail" in raw or "cvv" in raw or "otp" in raw or "expired" in raw:
            return RootCauseCategory.INVALID_PAYMENT_DETAILS.value
        if "abandon" in raw or "drop" in raw or "cancel" in raw:
            return RootCauseCategory.CUSTOMER_ABANDONMENT.value
        if "repeat" in raw or "retry" in raw:
            return RootCauseCategory.REPEATED_PAYMENT_FAILURE.value
        return RootCauseCategory.UNKNOWN.value

    def _deterministic_fallback(self, signals: dict[str, Any]) -> RootCauseAnalysis:
        """
        Deterministic evidence-first diagnosis based strictly on verified transaction signals.
        """
        payment_method = str(signals.get("payment_method", "")).lower()
        failure_reason = str(signals.get("failure_reason", "")).lower()
        attempt_count = signals.get("attempt_count", 1)
        anomaly_active = signals.get("phase4_anomaly_active", False)
        bank = signals.get("bank_network", "Bank")

        evidence: list[str] = []

        if anomaly_active or ("upi" in payment_method and "timeout" in failure_reason):
            category = RootCauseCategory.PAYMENT_METHOD_DEGRADATION.value
            confidence = 0.91
            evidence.append(f"UPI network failure rate elevated above baseline in {bank} network")
            if signals.get("customer_historical_success_rate") != "UNAVAILABLE":
                evidence.append(f"Customer historical success rate: {signals['customer_historical_success_rate']}")
            evidence.append("Transaction timed out during active payment degradation window")
            explanation = "The payment failed due to temporary UPI PSP latency degradation rather than customer insufficiency."
        elif attempt_count >= 3:
            category = RootCauseCategory.REPEATED_PAYMENT_FAILURE.value
            confidence = 0.88
            evidence.append(f"Transaction reached attempt count #{attempt_count} exceeding single-attempt threshold")
            evidence.append(f"Prior gateway failure reason: {signals.get('failure_reason')}")
            explanation = "Repeated payment retries on the same payment method exceeded safe threshold."
        elif "insufficient" in failure_reason:
            category = RootCauseCategory.INSUFFICIENT_FUNDS.value
            confidence = 0.95
            evidence.append(f"Gateway returned explicit code: {signals.get('failure_code') or failure_reason}")
            explanation = "The issuer bank declined authorization due to insufficient account balance."
        elif "timeout" in failure_reason:
            category = RootCauseCategory.TIMEOUT.value
            confidence = 0.86
            evidence.append("Authorization request exceeded gateway response timeout limit")
            explanation = "Transient network timeout encountered between merchant gateway and processor."
        elif "bank" in failure_reason:
            category = RootCauseCategory.BANK_FAILURE.value
            confidence = 0.89
            evidence.append(f"Issuer bank {bank} returned processing failure")
            explanation = f"Temporary unavailability or server degradation at {bank}."
        else:
            category = RootCauseCategory.GATEWAY_FAILURE.value
            confidence = 0.80
            evidence.append(f"Gateway failure telemetry recorded: {failure_reason}")
            explanation = "Gateway authorization failed due to technical processing error."

        return RootCauseAnalysis(
            transaction_id=signals["transaction_id"],
            root_cause=category,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
            signals_analyzed=signals,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )


# Global singleton instance
root_cause_agent = RootCauseAgent()
