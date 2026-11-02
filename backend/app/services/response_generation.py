"""Customer Support Response Generation Service for ConsumerVoice.

Generates grounded, non-hallucinatory customer support responses based on
original customer feedback, predicted sentiment, detected issue categories,
and verified organizational policies.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Enterprise-safe customer response generator with anti-hallucination guardrails."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"ResponseGenerator connected to google-genai using {self.model_name}")
            except Exception as e:
                logger.warning(f"ResponseGenerator could not initialize Gemini: {e}")

    def generate_local_response(
        self,
        customer_text: str,
        sentiment: str,
        detected_issues: List[Dict[str, Any]],
        company_policies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate deterministic, grounded template response without unverified promises."""
        complaints = [i["category"] for i in detected_issues if i.get("is_complaint")]
        praise = [i["category"] for i in detected_issues if i.get("aspect_sentiment") == "positive"]

        sentences: List[str] = []

        if sentiment == "positive":
            sentences.append("Thank you for sharing your positive feedback with us!")
            if praise:
                praise_str = ", ".join(praise).lower()
                sentences.append(f"We are delighted to hear that you appreciated the {praise_str}.")
            else:
                sentences.append("We are glad that our product met your expectations.")
            sentences.append("We look forward to serving you again soon.")

        elif sentiment == "negative" or complaints:
            sentences.append("Thank you for bringing this to our attention, and we apologize for any inconvenience caused.")
            if complaints:
                issues_str = " and ".join(complaints).lower()
                sentences.append(f"We have noted your concerns regarding {issues_str}.")

            # Grounded policy handling - only reference policies if explicitly supplied!
            if company_policies:
                sentences.append(f"According to our service policy: {company_policies[0]}")
            else:
                # Strictly avoid promising refunds, replacements, or delivery dates
                sentences.append(
                    "Our customer support team is actively reviewing your feedback. "
                    "Please keep your order details accessible so our representative can assist you directly."
                )
            sentences.append("We appreciate your patience while we investigate this matter.")

        else:  # neutral
            sentences.append("Thank you for taking the time to share your review.")
            if detected_issues:
                aspects_str = ", ".join([i["category"] for i in detected_issues]).lower()
                sentences.append(f"We have registered your comments regarding {aspects_str}.")
            sentences.append(
                "If you need any assistance or have further suggestions, please feel free to reach out to our team."
            )

        response_text = " ".join(sentences)
        return {
            "response": response_text,
            "mode": "local_template",
            "grounding_safeguards_applied": True,
            "sentiment_acknowledged": sentiment,
            "issues_addressed": complaints if complaints else praise,
        }

    def generate_response(
        self,
        customer_text: str,
        sentiment: str,
        detected_issues: List[Dict[str, Any]],
        company_policies: Optional[List[str]] = None,
        review_id: Optional[str] = None,
        use_gemini: bool = True,
    ) -> Dict[str, Any]:
        """Generate response via Gemini if available, or fall back to local grounded templates."""
        if use_gemini and self.client and self.api_key:
            try:
                complaint_names = [i["category"] for i in detected_issues if i.get("is_complaint")]
                policy_text = "\n".join(f"- {p}" for p in company_policies) if company_policies else "None provided."

                prompt = (
                    "You are a professional customer support representative for ConsumerVoice.\n"
                    "Draft an empathetic, professional response to the customer feedback.\n\n"
                    f"CUSTOMER FEEDBACK: \"{customer_text}\"\n"
                    f"PREDICTED SENTIMENT: {sentiment}\n"
                    f"DETECTED ISSUES: {', '.join(complaint_names) if complaint_names else 'None'}\n"
                    f"VERIFIED COMPANY POLICIES:\n{policy_text}\n\n"
                    "CRITICAL GROUNDING RULES (NEVER VIOLATE):\n"
                    "1. Acknowledge only facts mentioned in the customer's review.\n"
                    "2. DO NOT invent or promise refunds, replacements, compensation, or dates unless explicitly confirmed in verified company policies above.\n"
                    "3. If no policy confirms a refund or replacement, invite the customer to connect with support for case review.\n"
                    "4. Keep the tone helpful, professional, and concise (3-4 sentences).\n\n"
                    "SUPPORT RESPONSE:"
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return {
                        "response": response.text.strip(),
                        "mode": "gemini_grounded",
                        "model": self.model_name,
                        "review_id": review_id,
                        "grounding_safeguards_applied": True,
                        "sentiment_acknowledged": sentiment,
                        "issues_addressed": complaint_names,
                    }
            except Exception as e:
                logger.warning(f"Gemini response generation error: {e}. Falling back to local template.")

        # Local template fallback
        result = self.generate_local_response(customer_text, sentiment, detected_issues, company_policies)
        result["review_id"] = review_id
        return result

