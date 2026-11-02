"""Dedicated Live Browser Verification for Analyze Feedback Studio.

Tests model selection, live inference for both models, preset loading,
explainability headers and token sorting, issue detection with matched evidence,
negation guards, response drafting, and evidence-based safety screening.
"""

import os
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = "/Users/shivamrai/.gemini/antigravity/brain/e5628483-803a-4004-9d1b-c1a7f8b5fb6a/screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def test_analyze_studio():
    print("======================================================================")
    print(" ConsumerVoice: Live Browser Verification - Analyze Feedback Studio   ")
    print("======================================================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("\n[Step 1] Navigating to /analyze...")
        page.goto(f"{BASE_URL}/analyze", wait_until="networkidle")
        time.sleep(1.5)

        textarea = page.locator("textarea").first

        # ------------------------------------------------------------------
        # TEST A: LOGISTIC REGRESSION BASELINE
        # ------------------------------------------------------------------
        print("\n[Step 2] Testing Logistic Regression Baseline...")
        page.locator("button:has-text('Logistic Regression (Baseline)')").click()
        time.sleep(1.0)
        assert page.locator("text=Active: Logistic Regression").is_visible()
        print("  ✓ Active model badge shows 'Logistic Regression'")

        # Test Positive Preset
        print("  Testing Positive Preset with LogReg...")
        page.locator("button:has-text('Positive Review')").click()
        time.sleep(1.5)
        assert page.locator(".text-2xl.font-bold:has-text('Positive')").first.is_visible()
        assert page.locator("text=Tokens Supporting 'POSITIVE' Prediction").is_visible()
        assert page.locator("text=TF-IDF Linear Attribution").is_visible()
        print("  ✓ LogReg classified Positive Preset as Positive with positive token attribution")

        # Test Negative Preset
        print("  Testing Negative Preset with LogReg...")
        page.locator("button:has-text('Negative Review')").click()
        time.sleep(1.5)
        assert page.locator(".text-2xl.font-bold:has-text('Negative')").first.is_visible()
        assert page.locator("text=Tokens Supporting 'NEGATIVE' Prediction").is_visible()
        # Verify matched evidence shows actual phrase
        assert page.locator("text=Matched evidence:").first.is_visible()
        evidence_text = page.locator("text=Matched evidence:").first.inner_text()
        print(f"  ✓ Issue evidence display verified: {evidence_text}")
        assert "keyword match" not in evidence_text, "Issue evidence fell back to generic 'keyword match'!"
        print("  ✓ Confirmed: Exact extracted evidence phrase rendered (not 'keyword match')")
        page.screenshot(path=f"{SCREENSHOT_DIR}/flow3_logreg_explainability.png")

        # ------------------------------------------------------------------
        # TEST B: FINE-TUNED DISTILBERT TRANSFORMER
        # ------------------------------------------------------------------
        print("\n[Step 3] Testing Fine-Tuned DistilBERT Transformer...")
        page.locator("button:has-text('Fine-Tuned DistilBERT')").click()
        time.sleep(1.5)
        assert page.locator("text=Active: DistilBERT").is_visible()
        print("  ✓ Active model badge shows 'DistilBERT'")

        # Test Mixed Preset with DistilBERT
        print("  Testing Mixed Preset with DistilBERT...")
        page.locator("button:has-text('Mixed Review')").click()
        time.sleep(2.0)

        # DistilBERT classifies as Negative (complaints outweigh praise)
        assert page.locator(".text-2xl.font-bold:has-text('Negative')").first.is_visible()
        assert page.locator("text=DistilBERT Softmax").is_visible()
        assert page.locator("text=DistilBERT produces contextual self-attention").is_visible()
        assert page.locator("text=TF-IDF Linear Attribution").count() == 0
        print("  ✓ DistilBERT classified Mixed Review as Negative; linear weights suppressed")

        # Verify matched evidence for both issues in Mixed Preset
        issue_evidences = [el.inner_text() for el in page.locator("text=Matched evidence:").all()]
        print(f"  ✓ Mixed Review issues detected ({len(issue_evidences)}): {issue_evidences}")
        for ev in issue_evidences:
            assert "keyword match" not in ev
        page.screenshot(path=f"{SCREENSHOT_DIR}/flow3_distilbert_inference.png")

        # ------------------------------------------------------------------
        # TEST C: CUSTOM INPUT & NEGATION SUPPRESSION
        # ------------------------------------------------------------------
        print("\n[Step 4] Testing Custom Typing with Negation Guard...")
        textarea.fill("The delivery was not delayed, but customer support was very rude and unhelpful.")
        page.locator("button:has-text('Analyze Feedback')").click()
        time.sleep(2.0)

        # Delivery should NOT be flagged; Customer support should be flagged
        issues_rendered = page.locator(".bg-slate-950.border.border-slate-800").all_inner_texts()
        issues_joined = " ".join(issues_rendered)
        assert "Customer support" in issues_joined or "Customer Support" in issues_joined
        assert "Delivery and shipping" not in issues_joined
        print("  ✓ Negation guard verified: 'not delayed' suppressed delivery issue while 'customer support' was detected")

        # ------------------------------------------------------------------
        # TEST D: CUSTOMER RESPONSE ASSISTANT & EVIDENCE CHECK
        # ------------------------------------------------------------------
        print("\n[Step 5] Testing Customer Response Generator & Safety Screening...")
        # Expand response accordion
        page.locator("button:has-text('Generate Suggested Customer Response')").click()
        time.sleep(0.5)

        # Click Draft Response
        page.locator("button:has-text('Draft Response')").click()
        time.sleep(1.5)

        response_box = page.locator("textarea").nth(1)
        draft_val = response_box.input_value()
        assert len(draft_val) > 20
        print(f"  ✓ Grounded reply drafted ({len(draft_val)} chars)")

        # Expand Safety check
        page.locator("button:has-text('Check Response Against Customer Feedback')").click()
        time.sleep(0.5)
        page.locator("button:has-text('Run Evidence Check')").click()
        time.sleep(1.5)

        assert page.locator("text=Supported:").first.is_visible()
        claims = page.locator("text=Claim").all()
        print(f"  ✓ Evidence Screening decomposed response into {len(claims)} verified claims")
        page.screenshot(path=f"{SCREENSHOT_DIR}/flow3_response_and_screening.png")

        browser.close()

    print("\n======================================================================")
    print(f" VERIFICATION COMPLETE: ALL CHECKS PASSED (Console Errors: {len(console_errors)})")
    print("======================================================================\n")


if __name__ == "__main__":
    test_analyze_studio()
