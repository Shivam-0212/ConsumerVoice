# ConsumerVoice — Beginner-Friendly UI Walkthrough

Welcome to **ConsumerVoice**! This guide is designed so anyone on the team can understand the entire application in 5 minutes while running and demoing it.

---

## 🚀 How to Open the App

- **Live Web App (Production)**: [https://consumer-voice-rose.vercel.app](https://consumer-voice-rose.vercel.app)
- **Local URL (If running locally)**: [http://localhost:5173](http://localhost:5173)

---

## 🧭 The 4 Pages at a Glance

The application sidebar has exactly **4 primary pages**:

| # | Page Name | What It Is in One Sentence | Guide File |
| :-: | :--- | :--- | :--- |
| **1** | **Dashboard** | The big-picture overview of all 50,000 customer reviews, ratings, and top complaints. | [01_dashboard.md](01_dashboard.md) |
| **2** | **Review Explorer** | The search engine to browse, filter, inspect, and summarize individual customer reviews. | [02_review_explorer.md](02_review_explorer.md) |
| **3** | **Analyze Feedback** | The interactive AI playground where you type any review and see instant predictions, explanations, and issue detection. | [03_analyze_feedback.md](03_analyze_feedback.md) |
| **4** | **Model Comparison** | The scientific scorecard comparing our fast Logistic Regression model against fine-tuned DistilBERT. | [04_model_comparison.md](04_model_comparison.md) |

---

## 💡 Quick Demo Tips for Your Teammate

1. **Start on Dashboard (`/`)**: Show the 50,000 total imported reviews, the sentiment donut chart, and the rating distribution.
2. **Move to Review Explorer (`/explorer`)**: Type `"cooler"` or `"battery"` in the search bar, filter by `Negative` sentiment, and click **"Inspect"** on any review.
3. **Show Analyze Feedback (`/analyze`)**: Click one of the preset buttons (e.g. `"Mixed Review"`) or type a custom sentence to show how the model explains every word and detects issues.
4. **Finish on Model Comparison (`/models`)**: Highlight that DistilBERT achieves **91.4% accuracy** (+6.59% over baseline), while Logistic Regression provides **instant CPU explanations**.

---

Click into any individual file in this folder for the simple bullet-point breakdown!
