# Page 3: Analyze Feedback (AI Playground)

> **Route**: `/analyze`  
> **Purpose**: The interactive core of ConsumerVoice. Type or paste any customer review to test real-time sentiment prediction, word-level explanations, problem detection, and AI response drafting.

---

## 📌 What Is on This Page?

- **Classification Model Selector (Top)**:
  - Toggle between **Logistic Regression (Baseline)** (active on cloud) and **Fine-Tuned DistilBERT** (evaluated on GPU).

- **1-Click Preset Buttons**:
  - **Positive Review**: Fills in a sample happy review.
  - **Negative Review**: Fills in a sample unhappy review.
  - **Mixed Review**: Fills in a review with both praise and complaints (*"The product quality is good, but delivery was delayed and packaging was damaged."*).

- **Feedback Input Box**:
  - Large text area where you can type or paste any text (up to 5,000 characters).

- **Predicted Sentiment & Confidence Card**:
  - Shows the final verdict: **Positive** (green), **Negative** (red), or **Neutral** (orange).
  - Shows the model's confidence percentage (e.g., `80.5%`).

- **Class Probabilities Bar**:
  - Horizontal progress bars showing the exact softmax probability for all 3 classes (e.g., Positive: 9.1%, Negative: 10.3%, Neutral: 80.5%).

- **Rule-Based Issue Detection Box**:
  - Categorizes customer complaints across 10 business categories (Delivery, Quality, Packaging, Support, etc.).
  - Shows the exact quoted phrase that triggered each issue.
  - Distinguishes between **"Issue Detected"** (red badge) and **"Positive Aspect"** (green badge).
  - Uses **negation guards** (e.g., *"not delayed"* is ignored instead of wrongly flagged as a delivery delay).

- **Model Explainability (Feature Attribution)**:
  - Explains **why** the model made this decision without relying on a black box:
  - **Green Pills (Supporting Tokens)**: Words that pushed the model toward this sentiment with positive weights (e.g., `+0.627`).
  - **Red Pills (Opposing Tokens)**: Words that pulled against this sentiment with negative weights (e.g., `-0.278`).

- **Generate Suggested Customer Response (Expandable Section at Bottom)**:
  - AI Assistant that drafts a professional customer support email reply tailored to the review.
  - **Evidence-Based Hallucination Screening**: Compares every sentence in the AI's reply against the customer review to ensure no fake promises or unmentioned problems were made up.

---

## 🎮 What Can You Do on This Page?

- **Test the 1-click presets**:
  - Click **"Mixed Review"** $\rightarrow$ Click **"Analyze Feedback"** $\rightarrow$ See the model correctly classify it as *Neutral* and identify both good quality and bad packaging.
- **Type your own review**:
  - Example 1: *"Delivery took 3 weeks and the screen was cracked on arrival."* $\rightarrow$ Model predicts *Negative* (98% confidence) and flags *Delivery and Shipping* + *Packaging*.
  - Example 2 (Tricky negation): *"The delivery was not delayed, but customer support was very rude."* $\rightarrow$ Model flags *Customer Support*, but correctly skips *Delivery* because of the word "not".
- **Inspect word-level explanations**:
  - Scroll down to "Model Explainability" to see exactly which words contributed most to the AI's decision.
- **Test the AI Response Generator**:
  - Click the bottom drawer **"Generate Suggested Customer Response"** $\rightarrow$ Click **"Generate Grounded Response"** $\rightarrow$ Watch the hallucination screening check every claim against the review evidence.
