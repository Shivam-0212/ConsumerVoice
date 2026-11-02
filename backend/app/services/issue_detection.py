"""Issue Detection and Aspect-Based Feedback Analysis Service for ConsumerVoice.

Implements a contextual multi-label issue detection engine across
10 customer feedback taxonomy categories with negation awareness,
evidence span extraction, and aspect-level sentiment association.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 10 Taxonomy categories
ISSUE_TAXONOMY = [
    "Product quality",
    "Delivery and shipping",
    "Packaging",
    "Product performance",
    "Usability",
    "Pricing and value",
    "Durability",
    "Size and fit",
    "Returns and refunds",
    "Customer support",
]

# Patterns for each issue category: (regex_pattern, aspect_sentiment, base_confidence)
# Notice we include negative context guards and specific complaint indicators
ISSUE_PATTERNS = {
    "Product quality": [
        (r"\b(?:poor|bad|cheap|worst|terrible|horrible|inferior|defective|faulty|low)\s+(?:quality|material|plastic|build|finish)\b", "negative", 0.95),
        (r"\bquality\s+(?:is\s+)?(?:very\s+)?(?:bad|poor|cheap|worst|terrible|low|not\s+good)\b", "negative", 0.95),
        (r"\b(?:duplicate|fake|counterfeit|used|old)\s+(?:item|product|goods)\b", "negative", 0.98),
        (r"\b(?:good|super|excellent|high|great)\s+quality\b", "positive", 0.90),
        (r"\bquality\s+(?:is\s+)?(?:very\s+)?(?:good|super|excellent|great|nice)\b", "positive", 0.90),
    ],
    "Delivery and shipping": [
        (r"\b(?:delivery|shipping|courier|dispatch)\s+(?:was\s+|is\s+)?(?:very\s+|extremely\s+)?(?:delayed|late|slow|bad|poor|worst)\b", "negative", 0.95),
        (r"\b(?:delayed|late|slow)\s+(?:by\s+)?(?:\d+\s+(?:days?|weeks?)|delivery)\b", "negative", 0.95),
        (r"\bnever\s+(?:received|delivered|arrived)\b", "negative", 0.98),
        (r"\bnot\s+delivered\s+on\s+time\b", "negative", 0.95),
        (r"\b(?:fast|quick|speedy|on\s+time)\s+delivery\b", "positive", 0.92),
        (r"\bdelivery\s+(?:was\s+|is\s+)?(?:very\s+)?(?:fast|quick|on\s+time|superb|prompt)\b", "positive", 0.92),
    ],
    "Packaging": [
        (r"\b(?:packaging|package|box|parcel)\s+(?:was\s+)?(?:damaged|broken|torn|open|crushed|poor|worst|bad)\b", "negative", 0.96),
        (r"\b(?:damaged|broken|torn|crushed|open)\s+(?:packaging|package|box|parcel)\b", "negative", 0.96),
        (r"\b(?:bad|poor|worst)\s+packaging\b", "negative", 0.94),
        (r"\b(?:good|nice|safe|secure|excellent)\s+packaging\b", "positive", 0.90),
        (r"\bpackaging\s+(?:was\s+)?(?:good|safe|secure|well\s+packed)\b", "positive", 0.90),
    ],
    "Product performance": [
        (r"\b(?:not\s+working|stopped\s+working|doesn't\s+work|does\s+not\s+work|not\s+functioning)\b", "negative", 0.98),
        (r"\b(?:heating|overheating|heat\s+problem|battery\s+draining|drains\s+fast|slow\s+speed)\b", "negative", 0.92),
        (r"\b(?:poor|bad|worst|low)\s+(?:performance|battery\s+backup|cooling|sound|air\s+flow)\b", "negative", 0.94),
        (r"\b(?:great|good|excellent|awesome)\s+(?:performance|battery\s+backup|cooling|sound|air\s+flow)\b", "positive", 0.92),
        (r"\bworks?\s+(?:very\s+)?(?:well|fine|great|perfectly|smoothly)\b", "positive", 0.92),
    ],
    "Usability": [
        (r"\b(?:hard|difficult|complicated|confusing)\s+to\s+(?:use|install|assemble|operate|setup)\b", "negative", 0.92),
        (r"\b(?:no\s+manual|unclear\s+instructions|manual\s+missing)\b", "negative", 0.90),
        (r"\b(?:easy|simple)\s+to\s+(?:use|install|assemble|operate|setup)\b", "positive", 0.92),
        (r"\buser\s+friendly\b", "positive", 0.92),
    ],
    "Pricing and value": [
        (r"\b(?:overpriced|too\s+expensive|waste\s+of\s+money|not\s+worth|not\s+value\s+for\s+money|costly)\b", "negative", 0.95),
        (r"\bprice\s+is\s+(?:too\s+)?(?:high|expensive)\b", "negative", 0.92),
        (r"\b(?:value\s+for\s+money|worth\s+the\s+money|worth\s+buying|budget\s+friendly|reasonable\s+price)\b", "positive", 0.94),
        (r"\b(?:cheap|good)\s+price\b", "positive", 0.88),
    ],
    "Durability": [
        (r"\b(?:broke|broken|cracked|damaged|torn|stopped)\s+(?:within|after)\s+(?:a\s+few\s+days?|1\s+day|2\s+days?|one\s+week|a\s+month)\b", "negative", 0.96),
        (r"\b(?:not\s+durable|low\s+durability|fragile|poor\s+durability)\b", "negative", 0.92),
        (r"\b(?:durable|long\s+lasting|sturdy|strong\s+build)\b", "positive", 0.92),
    ],
    "Size and fit": [
        (r"\b(?:size\s+too\s+small|size\s+too\s+large|tight\s+fit|loose\s+fit|wrong\s+size|mismatched\s+size)\b", "negative", 0.94),
        (r"\b(?:does\s+not\s+fit|doesn't\s+fit|fit\s+is\s+bad)\b", "negative", 0.92),
        (r"\b(?:perfect\s+fit|fits\s+well|true\s+to\s+size)\b", "positive", 0.92),
    ],
    "Returns and refunds": [
        (r"\b(?:refund\s+not\s+received|return\s+rejected|replacement\s+denied|no\s+refund|unable\s+to\s+return)\b", "negative", 0.96),
        (r"\b(?:applied\s+for\s+return|request\s+replacement|return\s+this|want\s+refund)\b", "neutral", 0.88),
        (r"\b(?:easy\s+return|quick\s+refund|smooth\s+replacement)\b", "positive", 0.92),
    ],
    "Customer support": [
        (r"\b(?:customer\s+(?:support|care|service)|support\s+team|service\s+center)\s+(?:was\s+|is\s+)?(?:very\s+|extremely\s+)?(?:rude|unhelpful|worst|useless|not\s+responding|poor|terrible|bad|unresponsive)\b", "negative", 0.95),
        (r"\b(?:rude|unhelpful|useless|terrible|unresponsive)\s+(?:customer\s+(?:support|care|service)|support\s+team|agent|rep|representative)\b", "negative", 0.95),
        (r"\bno\s+response\s+from\s+(?:customer\s+(?:support|care|service)|support|seller|care)\b", "negative", 0.95),
        (r"\b(?:helpful|prompt|great|responsive|courteous|excellent)\s+(?:customer\s+(?:support|care|service)|support\s+team|service)\b", "positive", 0.92),
        (r"\b(?:customer\s+(?:support|care|service))\s+(?:was\s+|is\s+)?(?:very\s+|extremely\s+)?(?:helpful|prompt|great|responsive|courteous|excellent)\b", "positive", 0.92),
    ],
}

# Category-specific negation guards: phrases that invert or negate a specific category complaint
CATEGORY_NEGATION_GUARDS = {
    "Delivery and shipping": [
        r"\b(?:no|not|never|without\s+any)\s+(?:delay|delayed|delivery\s+delay)\b",
        r"\bdelivery\s+(?:was\s+)?not\s+delayed\b",
        r"\b(?:on\s+time|fast|quick)\s+delivery\b",
    ],
    "Product quality": [
        r"\b(?:no|not|never|without\s+any)\s+(?:defect|defects|damage|defective|poor\s+quality|quality\s+issue)\b",
        r"\bquality\s+(?:is|was)\s+not\s+(?:bad|poor)\b",
    ],
    "Packaging": [
        r"\b(?:no|not|never|without\s+any)\s+(?:damage|damaged|tear|torn)\s+(?:packaging|package|box)\b",
        r"\bpackaging\s+(?:was\s+)?not\s+(?:damaged|broken|bad)\b",
    ],
    "Customer support": [
        r"\b(?:no|not|never)\s+(?:issue\s+with|complaint\s+about)\s+(?:support|customer\s+support)\b",
        r"\b(?:support|customer\s+support)\s+(?:was\s+)?not\s+(?:rude|unhelpful|bad)\b",
    ],
    "Product performance": [
        r"\b(?:no|not|never|without\s+any)\s+(?:performance\s+issue|heating|lag)\b",
    ],
}

# Global negation guards: phrases that negate complaints within a specific clause
GLOBAL_NEGATION_GUARDS = [
    r"\bno\s+(?:issue|issues|problem|problems|complaint|complaints|defect|defects)\b",
    r"\bwithout\s+any\s+(?:issue|issues|problem|problems|complaint|complaints|defect|defects)\b",
    r"\bnever\s+(?:faced\s+any\s+problem|had\s+any\s+issue|disappointed)\b",
]


class IssueDetector:
    """Multi-label contextual issue detection and aspect extractor."""

    def __init__(self):
        self.taxonomy = ISSUE_TAXONOMY

    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences while respecting abbreviations."""
        if not text:
            return []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def split_clauses(self, sentence: str) -> List[str]:
        """Split a sentence into contrastive clauses to isolate negation context."""
        if not sentence:
            return []
        clauses = re.split(
            r"[,;]?\s*(?:\bbut\b|\bhowever\b|\balthough\b|\byet\b|\bexcept\b|\bwhereas\b|\bthough\b)\s*",
            sentence,
            flags=re.IGNORECASE,
        )
        return [c.strip() for c in clauses if c.strip()]

    def detect_issues(self, text: str) -> List[Dict[str, Any]]:
        """Identify multi-label product issues and aspect sentiments from text."""
        if not text or not text.strip():
            return []

        cleaned = text.strip()
        sentences = self.split_sentences(cleaned)
        if not sentences:
            sentences = [cleaned]

        detected: List[Dict[str, Any]] = []
        found_categories = set()

        for category, rules in ISSUE_PATTERNS.items():
            category_guards = CATEGORY_NEGATION_GUARDS.get(category, [])

            for pattern, aspect_sentiment, base_conf in rules:
                rule_matched = False

                for sentence in sentences:
                    # Test each clause within the sentence to isolate negation scope
                    clauses = self.split_clauses(sentence)
                    if not clauses:
                        clauses = [sentence]

                    for clause in clauses:
                        match = re.search(pattern, clause, re.IGNORECASE)
                        if match:
                            matched_phrase = match.group(0)

                            # Negation check for complaints
                            is_negated = False
                            if aspect_sentiment == "negative":
                                # 1. Local preceding negation check (e.g. "was not delayed")
                                pre_text = clause[: match.start()].strip()
                                if re.search(r"\b(?:not|never|no)\s+(?:was\s+|is\s+|be\s+|seem\s+)?$", pre_text, re.IGNORECASE):
                                    is_negated = True

                                # 2. Category-specific negation in clause or sentence
                                if not is_negated:
                                    for guard in category_guards:
                                        if re.search(guard, clause, re.IGNORECASE) or re.search(guard, sentence, re.IGNORECASE):
                                            is_negated = True
                                            break

                                # 3. Global negation within the local clause
                                if not is_negated:
                                    for guard in GLOBAL_NEGATION_GUARDS:
                                        if re.search(guard, clause, re.IGNORECASE):
                                            is_negated = True
                                            break

                            if is_negated:
                                continue

                            # Avoid duplicate detections for same category in same text
                            dedup_key = (category, aspect_sentiment)
                            if dedup_key in found_categories:
                                continue
                            found_categories.add(dedup_key)

                            detected.append({
                                "category": category,
                                "aspect_sentiment": aspect_sentiment,
                                "is_complaint": aspect_sentiment == "negative",
                                "matched_evidence": matched_phrase,
                                "evidence_sentence": sentence,
                                "confidence": base_conf,
                                "detection_method": "contextual_rule_pattern",
                            })
                            rule_matched = True
                            break  # matched clause for this rule

                    if rule_matched:
                        break  # rule matched for this category

        return detected

    def summarize_issues(self, detected_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary aggregates of detected issues."""
        complaints = [i for i in detected_issues if i.get("is_complaint")]
        praise = [i for i in detected_issues if i.get("aspect_sentiment") == "positive"]
        neutral = [i for i in detected_issues if i.get("aspect_sentiment") == "neutral"]

        return {
            "total_aspects_detected": len(detected_issues),
            "complaint_count": len(complaints),
            "praise_count": len(praise),
            "neutral_count": len(neutral),
            "complaint_categories": [c["category"] for c in complaints],
            "praise_categories": [p["category"] for p in praise],
            "is_actionable_complaint": len(complaints) > 0,
        }

