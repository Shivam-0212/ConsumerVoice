# Page 1: Customer Feedback Dashboard

> **Route**: `/` (Home)  
> **Purpose**: Gives you a quick bird's-eye view of all customer feedback, sentiment trends, and system health.

---

## 📌 What Is on This Page?

- **Dataset Scope & Lineage Banner (Top)**:
  - Shows the raw Flipkart dataset size (**205,052** reviews) vs. what is imported in the SQLite database (**50,000** records).
  - Shows the model split counts (**73,512** train, **9,189** validation, **9,189** test).

- **4 KPI Metric Cards**:
  - **Total Reviews Analyzed**: 50,000 imported reviews.
  - **Positive Reviews**: 40,855 (81.71% of dataset).
  - **Negative Reviews**: 6,889 (13.78% of dataset).
  - **Neutral Reviews**: 2,256 (4.51% of dataset).

- **Customer Feedback Insights Box**:
  - An AI extractive synthesis summarizing overall customer feedback across 50 records.
  - Displays immutable source review citations (e.g., `REV_000001`, `REV_000003`) so you can verify the summary is grounded.

- **Sentiment Distribution Donut Chart**:
  - Visual circle chart showing the split between Positive (green), Negative (red), and Neutral (orange).

- **Customer Rating Distribution Bar Chart**:
  - Bar chart showing counts from 1-star to 5-star customer ratings (5-star is the largest at 28,781 reviews).

- **Most Commonly Detected Issues Bar Chart**:
  - Top complaint categories detected across the reviews (e.g., *Product Quality*, *Product Performance*, *Pricing & Value*, *Delivery & Shipping*).

- **Highest-Volume Products List**:
  - The top 5 products with the most customer reviews in the dataset (e.g., *Lakme Eyeconic Kajal*, *DOMS Pencil Kit*, *Pigeon Kettle*).

- **System Health Pill (Bottom Left Sidebar)**:
  - Shows the active model (**Logistic Regression**) and backend status (**Operational** with a green dot).

---

## 🎮 What Can You Do on This Page?

- **Hover over charts**: Move your mouse over any slice or bar in the charts to see the exact count and percentage.
- **Click "Analyze Feedback" (Top Right Button)**: Jumps directly to the interactive AI testing page.
- **Click "Inspect Supporting Reviews"**: Opens the explorer filtered by the cited reviews in the feedback insights box.
- **Click the Refresh Icon**: Re-queries the backend API to update all stats in real time.
