"""Hallucination-Aware Evidence-Based Claim Verification Service for ConsumerVoice.

Performs fine-grained factual claim extraction from AI-generated text,
retrieves corroborating/conflicting evidence spans from source feedback
and verified policies, and classifies claims into SUPPORTED, CONTRADICTED,
or UNSUPPORTED / NEEDS REVIEW.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Courtesy and conversational patterns that make no factual assertion
COURTESY_PATTERNS = [
    r"^thank\s+you\s+(?:for\s+)?.*",
    r"^we\s+apologize\s+(?:for\s+)?.*",
    r"^sorry\s+(?:for\s+)?.*",
    r"^we\s+are\s+glad\s+to\s+hear\s+.*",
    r"^we\s+appreciate\s+your\s+(?:patience|feedback|business|support).*",
    r"^please\s+feel\s+free\s+to\s+.*",
    r"^have\s+a\s+(?:great|wonderful|good)\s+day.*",
    r"^we\s+look\s+forward\s+to\s+serving\s+you.*",
    r"^best\s+regards.*",
    r"^sincerely.*",
]

# Unverified promise patterns (refunds, replacements, delivery dates, compensation)
UNVERIFIED_PROMISE_PATTERNS = [
    (r"\b(?:refund\s+of\s+(?:rs\.?|inr|\$)?\s*\d+|refunded\s+(?:rs\.?|inr|\$)?\s*\d+|processed\s+(?:your\s+)?refund)\b", "refund_promise"),
    (r"\b(?:replacement\s+will\s+arrive|sending\s+a\s+replacement|dispatched\s+a\s+new|new\s+unit\s+will\s+be\s+delivered)\b", "replacement_promise"),
    (r"\b(?:will\s+arrive\s+tomorrow|delivery\s+(?:is\s+)?scheduled\s+for\s+tomorrow|within\s+24\s+hours)\b", "delivery_date_promise"),
    (r"\b(?:credited\s+to\s+your\s+bank|coupon\s+of\s+rs|free\s+gift)\b", "compensation_promise"),
    (r"\b(?:warranty\s+approved|claim\s+has\s+been\s+accepted)\b", "warranty_promise"),
]

# Contradiction indicators between claims and evidence
CONTRADICTION_PAIRS = [
    (r"\b(?:on\s+time|ahead\s+of\s+time|speedy\s+delivery|delivered\s+early)\b", r"\b(?:delayed|late|delay|slow\s+delivery)\b"),
    (r"\b(?:delayed|late)\b", r"\b(?:on\s+time|fast\s+delivery|early)\b"),
    (r"\b(?:flawless|intact|undamaged|perfect\s+condition|good\s+packaging)\b", r"\b(?:damaged|broken|crushed|torn|open\s+packaging)\b"),
    (r"\b(?:damaged|broken|crushed)\b", r"\b(?:good|perfect|intact|safe\s+packaging)\b"),
    (r"\b(?:works?\s+perfectly|functions?\s+well|great\s+performance)\b", r"\b(?:not\s+working|stopped\s+working|defective|poor\s+performance)\b"),
]


class HallucinationDetector:
    """Evidence-based claim verification engine for customer service text."""

    def __init__(self, lazy_load_nli: bool = True):
        self.nli_model = None
        self.nli_tokenizer = None
        self.lazy_load_nli = lazy_load_nli

    def _ensure_nli(self) -> bool:
        """Lazily initialize DeBERTa-v3 NLI model if installed and resources permit."""
        if self.nli_model is not None:
            return True
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            model_id = "cross-encoder/nli-deberta-v3-small"
            logger.info(f"Attempting lazy load of NLI model: {model_id}...")
            self.nli_tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.nli_model = AutoModelForSequenceClassification.from_pretrained(model_id)
            self.nli_model.eval()
            logger.info("DeBERTa-v3 NLI model loaded successfully.")
            return True
        except Exception as e:
            logger.info(f"NLI model not loaded ({e}). Using robust calibrated evidence verification.")
            return False

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences cleanly, preserving abbreviations like Rs., Dr., etc."""
        if not text:
            return []
        # Protect common abbreviations and numbers
        cleaned = text.strip()
        cleaned = re.sub(r"\b(Rs|Mr|Ms|Mrs|Dr|Prof|vs|eg|ie)\.", r"\1<DOT>", cleaned, flags=re.IGNORECASE)
        # Protect decimal numbers
        cleaned = re.sub(r"(\d+)\.(\d+)", r"\1<NUMDOT>\2", cleaned)
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        # Restore protected tokens
        restored = []
        for s in sentences:
            s_clean = s.replace("<DOT>", ".").replace("<NUMDOT>", ".").strip()
            if s_clean:
                restored.append(s_clean)
        return restored

    def is_courtesy(self, sentence: str) -> bool:
        """Check if sentence is generic politeness/courtesy without factual claims."""
        s_clean = sentence.strip().lower()
        # If very short polite sentence
        if len(s_clean.split()) <= 4 and any(w in s_clean for w in ["thank you", "thanks", "sorry", "welcome"]):
            return True
        for pattern in COURTESY_PATTERNS:
            if re.match(pattern, s_clean):
                return True
        return False

    def extract_claims(self, response_text: str) -> Tuple[List[str], List[str]]:
        """Separate response into factual claim candidates and non-factual courtesy statements."""
        sentences = self.split_into_sentences(response_text)
        factual_claims = []
        courtesy_sentences = []

        for s in sentences:
            if self.is_courtesy(s):
                courtesy_sentences.append(s)
            else:
                factual_claims.append(s)

        return factual_claims, courtesy_sentences

    def retrieve_evidence(
        self,
        claim: str,
        source_texts: List[str]
    ) -> List[Dict[str, Any]]:
        """Retrieve candidate evidence sentences from source feedback and company policy."""
        # Clean claim tokens (words >= 4 chars, ignoring common stop words)
        claim_words = set(re.findall(r"\b[a-z]{3,}\b", claim.lower()))
        stopwords = {"this", "that", "with", "have", "from", "your", "been", "were", "what", "which", "there", "their", "will"}
        informative_words = claim_words - stopwords

        evidence_spans: List[Dict[str, Any]] = []

        for text in source_texts:
            if not text:
                continue
            sentences = self.split_into_sentences(text)
            for s in sentences:
                s_words = set(re.findall(r"\b[a-z]{3,}\b", s.lower()))
                overlap = informative_words.intersection(s_words)
                overlap_ratio = len(overlap) / max(len(informative_words), 1)

                if overlap_ratio >= 0.25 or len(overlap) >= 2:
                    evidence_spans.append({
                        "evidence_text": s,
                        "overlap_tokens": list(overlap),
                        "overlap_ratio": round(overlap_ratio, 3),
                    })

        # Sort candidate evidence by overlap ratio descending
        evidence_spans.sort(key=lambda x: x["overlap_ratio"], reverse=True)
        return evidence_spans

    def check_contradiction(self, claim: str, evidence: str) -> bool:
        """Check if claim and evidence hold logically contradictory assertions."""
        c_low = claim.lower()
        e_low = evidence.lower()

        for pat_a, pat_b in CONTRADICTION_PAIRS:
            if re.search(pat_a, c_low) and re.search(pat_b, e_low):
                return True
            if re.search(pat_b, c_low) and re.search(pat_a, e_low):
                return True
        return False

    def verify_single_claim(
        self,
        claim: str,
        review_text: str,
        company_policies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Verify an individual claim against customer review and company policies."""
        policies = company_policies or []
        all_sources = [review_text] + policies

        # 1. Unverified promise check (hallucinated commitments)
        for pattern, promise_type in UNVERIFIED_PROMISE_PATTERNS:
            if re.search(pattern, claim, re.IGNORECASE):
                # Check if an explicit policy or review justifies this exact promise
                policy_justified = False
                matched_policy = None
                for p in policies:
                    if re.search(pattern, p, re.IGNORECASE):
                        policy_justified = True
                        matched_policy = p
                        break

                if not policy_justified:
                    return {
                        "claim": claim,
                        "status": "UNSUPPORTED",
                        "verdict_reason": f"Claim makes an unverified transactional commitment ({promise_type}) with no corroborating policy or review evidence.",
                        "matched_evidence": None,
                        "confidence": 0.96,
                        "method": "commitment_audit",
                    }

        # 2. Retrieve evidence from source texts
        retrieved_evidence = self.retrieve_evidence(claim, all_sources)

        if not retrieved_evidence:
            return {
                "claim": claim,
                "status": "UNSUPPORTED",
                "verdict_reason": "No relevant corroborating evidence found in customer feedback or company policy.",
                "matched_evidence": None,
                "confidence": 0.88,
                "method": "evidence_retrieval",
            }

        top_evidence = retrieved_evidence[0]
        ev_text = top_evidence["evidence_text"]

        # 3. Contradiction check
        for ev in retrieved_evidence:
            if self.check_contradiction(claim, ev["evidence_text"]):
                return {
                    "claim": claim,
                    "status": "CONTRADICTED",
                    "verdict_reason": f"Claim directly conflicts with customer feedback: '{ev['evidence_text']}'.",
                    "matched_evidence": ev["evidence_text"],
                    "confidence": 0.94,
                    "method": "conflict_detection",
                }

        # 4. Neural NLI verification if loaded
        if self.nli_model is not None and self.nli_tokenizer is not None:
            try:
                import torch
                features = self.nli_tokenizer(
                    ev_text,
                    claim,
                    padding=True,
                    truncation=True,
                    return_tensors="pt"
                )
                with torch.no_grad():
                    scores = self.nli_model(**features).logits[0]
                    probs = torch.softmax(scores, dim=-1).tolist()
                # DeBERTa NLI mapping: 0: Contradiction, 1: Entailment, 2: Neutral
                entailment_prob = probs[1]
                contradiction_prob = probs[0]

                if contradiction_prob > 0.65:
                    return {
                        "claim": claim,
                        "status": "CONTRADICTED",
                        "verdict_reason": f"NLI DeBERTa detected logical contradiction ({contradiction_prob*100:.1f}%) against evidence.",
                        "matched_evidence": ev_text,
                        "confidence": round(contradiction_prob, 3),
                        "method": "neural_nli_deberta",
                    }
                elif entailment_prob > 0.60:
                    return {
                        "claim": claim,
                        "status": "SUPPORTED",
                        "verdict_reason": f"NLI DeBERTa verified claim entailment ({entailment_prob*100:.1f}%) with source evidence.",
                        "matched_evidence": ev_text,
                        "confidence": round(entailment_prob, 3),
                        "method": "neural_nli_deberta",
                    }
            except Exception as e:
                logger.warning(f"NLI evaluation failed: {e}. Falling back to calibrated overlap.")

        # 5. Calibrated lexical-semantic support check
        overlap_ratio = top_evidence["overlap_ratio"]
        if overlap_ratio >= 0.40 or len(top_evidence["overlap_tokens"]) >= 3:
            return {
                "claim": claim,
                "status": "SUPPORTED",
                "verdict_reason": f"Corroborated by source evidence span: '{ev_text}'.",
                "matched_evidence": ev_text,
                "confidence": round(min(0.70 + overlap_ratio * 0.25, 0.95), 3),
                "method": "semantic_evidence_overlap",
            }
        else:
            return {
                "claim": claim,
                "status": "UNSUPPORTED",
                "verdict_reason": "Partial evidence found but insufficient semantic alignment to establish factual support.",
                "matched_evidence": ev_text,
                "confidence": 0.75,
                "method": "insufficient_alignment",
            }

    def verify_response(
        self,
        response_text: str,
        customer_review: str,
        company_policies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Perform end-to-end evidence verification across all claims in a customer response."""
        factual_claims, courtesy_items = self.extract_claims(response_text)

        if not factual_claims:
            return {
                "verdict": "NO_FACTUAL_CLAIMS",
                "overall_status": "PASS",
                "claim_support_rate": 100.0,
                "unsupported_claim_rate": 0.0,
                "contradiction_rate": 0.0,
                "evidence_coverage": 100.0,
                "claims": [],
                "courtesy_statements": courtesy_items,
                "total_claims": 0,
                "supported_count": 0,
                "unsupported_count": 0,
                "contradicted_count": 0,
                "disclaimer": "All statements identified as standard courtesy phrases. Evidence-based hallucination screening applied.",
            }

        verified_claims: List[Dict[str, Any]] = []
        supported_cnt = 0
        unsupported_cnt = 0
        contradicted_cnt = 0
        with_evidence_cnt = 0

        for claim in factual_claims:
            res = self.verify_single_claim(claim, customer_review, company_policies)
            status = res["status"]
            if status == "SUPPORTED":
                supported_cnt += 1
            elif status == "CONTRADICTED":
                contradicted_cnt += 1
            else:
                unsupported_cnt += 1

            if res.get("matched_evidence"):
                with_evidence_cnt += 1

            verified_claims.append(res)

        total = len(factual_claims)
        support_rate = round((supported_cnt / total) * 100.0, 1)
        unsupported_rate = round((unsupported_cnt / total) * 100.0, 1)
        contradiction_rate = round((contradicted_cnt / total) * 100.0, 1)
        coverage_rate = round((with_evidence_cnt / total) * 100.0, 1)

        # Overall verdict
        if contradicted_cnt > 0:
            overall_status = "FAIL_CONTRADICTED"
        elif unsupported_cnt > 0:
            overall_status = "WARNING_UNSUPPORTED"
        else:
            overall_status = "PASS_VERIFIED"

        return {
            "overall_status": overall_status,
            "claim_support_rate": support_rate,
            "unsupported_claim_rate": unsupported_rate,
            "contradiction_rate": contradiction_rate,
            "evidence_coverage": coverage_rate,
            "total_claims": total,
            "supported_count": supported_cnt,
            "unsupported_count": unsupported_cnt,
            "contradicted_count": contradicted_cnt,
            "claims": verified_claims,
            "courtesy_statements": courtesy_items,
            "disclaimer": (
                "Notice: This assessment is an algorithmic, evidence-based hallucination screening "
                "and does not represent an absolute guarantee of factual ground truth."
            ),
        }
