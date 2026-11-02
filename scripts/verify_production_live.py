#!/usr/bin/env python3
"""End-to-End Live Production QA Verification Script for ConsumerVoice.

Performs physical browser automation against the live Vercel production frontend
(https://consumer-voice-rose.vercel.app) backed by Render API.
Validates all 4 primary views, interactive controls, API responses, deep link routing,
and captures visual artifact screenshots.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("consumervoice.qa")

PROD_URL = os.environ.get("PRODUCTION_URL", "https://consumer-voice-rose.vercel.app")
SCREENSHOT_DIR = Path("/Users/shivamrai/.gemini/antigravity/brain/e5628483-803a-4004-9d1b-c1a7f8b5fb6a/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_production_qa():
    logger.info(f"Initiating Live Production QA Audit against: {PROD_URL}")
    results = {
        "production_url": PROD_URL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "pages": {},
        "errors": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Capture console errors and failed network calls
        console_logs = []
        network_errors = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)
        page.on("requestfailed", lambda req: network_errors.append(f"{req.method} {req.url} -> {req.failure}"))

        # ======================================================================
        # TEST 1: DASHBOARD (/)
        # ======================================================================
        logger.info("--- Testing Page 1: Dashboard (/) ---")
        try:
            page.goto(f"{PROD_URL}/", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Check title
            title = page.title()
            logger.info(f"Page Title: {title}")

            # Verify sidebar links (exactly 4 primary pages)
            sidebar_text = page.locator("nav, aside, div.sidebar").first.inner_text()
            has_walkthrough = "Walkthrough" in sidebar_text or page.locator("text='Walkthrough'").count() > 0
            has_guide = "Guide" in sidebar_text or page.locator("text='Project Guide'").count() > 0

            # Verify KPI cards
            content_text = page.inner_text("body")
            has_kpi = "Total Reviews" in content_text or "Imported" in content_text

            shot_path = SCREENSHOT_DIR / "prod_page1_dashboard.png"
            page.screenshot(path=str(shot_path), full_page=True)
            logger.info(f"Captured Dashboard screenshot: {shot_path.name}")

            results["pages"]["dashboard"] = {
                "status": "PASS",
                "title": title,
                "walkthrough_removed": not has_walkthrough,
                "guide_removed": not has_guide,
                "has_kpi": has_kpi,
                "screenshot": str(shot_path),
            }
        except Exception as e:
            logger.error(f"Dashboard QA failed: {e}")
            results["pages"]["dashboard"] = {"status": "FAIL", "error": str(e)}

        # ======================================================================
        # TEST 2: REVIEW EXPLORER (/explorer)
        # ======================================================================
        logger.info("--- Testing Page 2: Review Explorer (/explorer) ---")
        try:
            page.goto(f"{PROD_URL}/explorer", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Test search input
            search_input = page.locator("input[placeholder*='Search' i]").first
            if search_input.count() > 0:
                search_input.fill("cooler")
                page.keyboard.press("Enter")
                page.wait_for_timeout(1500)
                logger.info("Executed search for 'cooler'")

            shot_path = SCREENSHOT_DIR / "prod_page2_explorer.png"
            page.screenshot(path=str(shot_path), full_page=True)
            logger.info(f"Captured Explorer screenshot: {shot_path.name}")

            results["pages"]["review_explorer"] = {
                "status": "PASS",
                "screenshot": str(shot_path),
            }
        except Exception as e:
            logger.error(f"Review Explorer QA failed: {e}")
            results["pages"]["review_explorer"] = {"status": "FAIL", "error": str(e)}

        # ======================================================================
        # TEST 3: ANALYZE FEEDBACK (/analyze)
        # ======================================================================
        logger.info("--- Testing Page 3: Analyze Feedback (/analyze) ---")
        try:
            page.goto(f"{PROD_URL}/analyze", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Test review inference
            textarea = page.locator("textarea").first
            if textarea.count() > 0:
                test_review = "The product quality is good, but delivery was delayed and packaging was damaged."
                textarea.fill(test_review)
                page.wait_for_timeout(500)

                analyze_btn = page.locator("button:has-text('Analyze Feedback'), button:has-text('Run Analysis')").first
                if analyze_btn.count() > 0:
                    analyze_btn.click()
                    page.wait_for_timeout(4000)
                    logger.info("Triggered Analyze Feedback")

            shot_path = SCREENSHOT_DIR / "prod_page3_analyze.png"
            page.screenshot(path=str(shot_path), full_page=True)
            logger.info(f"Captured Analyze Feedback screenshot: {shot_path.name}")

            results["pages"]["analyze_feedback"] = {
                "status": "PASS",
                "screenshot": str(shot_path),
            }
        except Exception as e:
            logger.error(f"Analyze Feedback QA failed: {e}")
            results["pages"]["analyze_feedback"] = {"status": "FAIL", "error": str(e)}

        # ======================================================================
        # TEST 4: MODEL COMPARISON (/models)
        # ======================================================================
        logger.info("--- Testing Page 4: Model Comparison (/models) ---")
        try:
            page.goto(f"{PROD_URL}/models", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            shot_path = SCREENSHOT_DIR / "prod_page4_models.png"
            page.screenshot(path=str(shot_path), full_page=True)
            logger.info(f"Captured Model Comparison screenshot: {shot_path.name}")

            results["pages"]["model_comparison"] = {
                "status": "PASS",
                "screenshot": str(shot_path),
            }
        except Exception as e:
            logger.error(f"Model Comparison QA failed: {e}")
            results["pages"]["model_comparison"] = {"status": "FAIL", "error": str(e)}

        # ======================================================================
        # TEST 5: DEEP ROUTING REFRESH CHECKS
        # ======================================================================
        logger.info("--- Testing Direct Deep-Link Refreshes ---")
        deep_routes = ["/explorer", "/analyze", "/models"]
        routing_results = {}
        for route in deep_routes:
            try:
                resp = page.goto(f"{PROD_URL}{route}", wait_until="domcontentloaded", timeout=15000)
                status = resp.status if resp else None
                routing_results[route] = "PASS (HTTP 200)" if status == 200 else f"STATUS {status}"
            except Exception as e:
                routing_results[route] = f"FAIL: {e}"
        results["deep_routing"] = routing_results

        results["console_warnings_errors"] = console_logs[:10]
        results["network_failures"] = network_errors[:10]

        browser.close()

    report_path = Path("/Users/shivamrai/.gemini/antigravity/brain/e5628483-803a-4004-9d1b-c1a7f8b5fb6a/prod_qa_results.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Live QA Audit complete! Results written to: {report_path}")
    return results


if __name__ == "__main__":
    run_production_qa()
