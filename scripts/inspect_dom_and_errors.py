"""Deep DOM Extraction and Runtime Error Inspector for ConsumerVoice.

Navigates through all 5 pages using headless Chrome, extracts DOM structure,
monitors console messages and network failures, and reports findings.
"""

import json
import time
from playwright.sync_api import sync_playwright

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://localhost:5173"

def inspect_app():
    audit_data = {
        "routes": {},
        "console_errors": [],
        "console_warnings": [],
        "network_errors": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Listen to console
        def handle_console(msg):
            if msg.type == "error":
                audit_data["console_errors"].append({"page": page.url, "text": msg.text})
                print(f"  [CONSOLE ERROR]: {msg.text}")
            elif msg.type == "warning":
                audit_data["console_warnings"].append({"page": page.url, "text": msg.text})
                print(f"  [CONSOLE WARN]: {msg.text}")

        page.on("console", handle_console)

        # Listen to failed network requests
        def handle_response(response):
            if response.status >= 400:
                audit_data["network_errors"].append({
                    "url": response.url,
                    "status": response.status,
                    "status_text": response.status_text,
                })
                print(f"  [HTTP ERROR {response.status}]: {response.url}")

        page.on("response", handle_response)

        pages_to_test = [
            ("Dashboard", "/"),
            ("Review Explorer", "/explorer"),
            ("Analyze Feedback", "/analyze"),
            ("Model Comparison", "/models"),
            ("Project Guide", "/guide"),
        ]

        for name, route in pages_to_test:
            print(f"\n=======================================================")
            print(f" Inspecting DOM & Runtime: {name} ({route})")
            print(f"=======================================================")
            page.goto(f"{BASE_URL}{route}", wait_until="networkidle")
            time.sleep(1.5)

            # Extract basic DOM details
            title = page.title()
            headings = [h.inner_text().strip() for h in page.locator("h1, h2, h3").all()]
            buttons = [b.inner_text().strip() for b in page.locator("button").all() if b.inner_text().strip()]
            links = [a.get_attribute("href") for a in page.locator("a").all() if a.get_attribute("href")]
            text_preview = page.locator("main").inner_text()[:400]

            audit_data["routes"][route] = {
                "title": title,
                "headings": headings,
                "buttons_count": len(buttons),
                "buttons_sample": buttons[:8],
                "links": links[:6],
                "text_preview": text_preview.replace("\n", " "),
            }

            print(f"  Title: {title}")
            print(f"  Headings: {headings[:4]}")
            print(f"  Buttons ({len(buttons)}): {buttons[:6]}")

        # Now test specific interactive features to check for errors during user interactions
        print("\n=======================================================")
        print(" Testing Interactive Features for Runtime Errors")
        print("=======================================================")

        # 1. Test Review Explorer - Summarize and Inspect Modals
        print("  -> Interacting with Review Explorer...")
        page.goto(f"{BASE_URL}/explorer", wait_until="networkidle")
        time.sleep(1.0)
        
        # Click Summarize Filtered Reviews
        page.locator("button:has-text('Summarize Filtered Reviews')").click()
        time.sleep(2.0)
        # Check if modal is visible
        modal_visible = page.locator("text=Summary of Filtered Reviews").is_visible()
        print(f"     Summarize Modal Opened: {modal_visible}")
        page.locator("button:has-text('Done')").click()
        time.sleep(0.5)

        # Click Inspect on first row
        page.locator("button:has-text('Inspect')").first.click()
        time.sleep(1.0)
        inspect_visible = page.locator("text=Review Inspection & Lineage").is_visible()
        print(f"     Inspect Modal Opened: {inspect_visible}")
        
        # Run Live Prediction inside Inspect Modal
        page.locator("button:has-text('Run Live Prediction')").click()
        time.sleep(1.5)
        print(f"     Live prediction executed in modal")
        page.locator("button:has-text('Close')").click()
        time.sleep(0.5)

        # 2. Test Analyze Feedback - Full Pipeline
        print("  -> Interacting with Analyze Feedback...")
        page.goto(f"{BASE_URL}/analyze", wait_until="networkidle")
        time.sleep(1.0)

        # Switch Model to LogReg
        page.locator("button:has-text('Logistic Regression (Baseline)')").click()
        time.sleep(1.0)

        # Click Positive Preset
        page.locator("button:has-text('Positive Review')").click()
        time.sleep(1.5)

        # Switch to DistilBERT
        page.locator("button:has-text('Fine-Tuned DistilBERT')").click()
        time.sleep(1.0)

        # Click Mixed Preset
        page.locator("button:has-text('Mixed Review')").click()
        time.sleep(1.5)

        # Expand Customer Response
        page.locator("button:has-text('Generate Suggested Customer Response')").click()
        time.sleep(0.5)
        page.locator("button:has-text('Draft Response')").click()
        time.sleep(1.5)

        # Expand Evidence Check
        page.locator("button:has-text('Check Response Against Customer Feedback')").click()
        time.sleep(0.5)
        page.locator("button:has-text('Run Evidence Check')").click()
        time.sleep(1.5)

        # 3. Test Model Comparison
        print("  -> Interacting with Model Comparison...")
        page.goto(f"{BASE_URL}/models", wait_until="networkidle")
        time.sleep(1.0)
        page.locator("button:has-text('View Detailed Evaluation')").click()
        time.sleep(0.5)

        browser.close()

    print("\n=======================================================")
    print(" Audit Summary")
    print("=======================================================")
    print(f"Total Console Errors: {len(audit_data['console_errors'])}")
    print(f"Total Console Warnings: {len(audit_data['console_warnings'])}")
    print(f"Total Network HTTP Errors: {len(audit_data['network_errors'])}")
    if audit_data["console_errors"]:
        print("Console Errors Details:")
        for err in audit_data["console_errors"]:
            print(f"  - {err}")
    if audit_data["console_warnings"]:
        print("Console Warnings Details:")
        for warn in audit_data["console_warnings"]:
            print(f"  - {warn}")
    if audit_data["network_errors"]:
        print("Network Errors Details:")
        for err in audit_data["network_errors"]:
            print(f"  - {err}")

    with open("presentation_guide/dom_audit_result.json", "w") as f:
        json.dump(audit_data, f, indent=2)

    return audit_data

if __name__ == "__main__":
    inspect_app()
