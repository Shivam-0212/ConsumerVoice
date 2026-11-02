# Page 2: Review Explorer

> **Route**: `/explorer`  
> **Purpose**: Lets you search, filter, read, and inspect the real 50,000 customer reviews like a search engine.

---

## 📌 What Is on This Page?

- **Search Bar**:
  - A text input box where you can type keywords (like `"cooler"`, `"sound"`, `"battery"`, or `"damage"`).

- **Filter Dropdowns**:
  - **Sentiment Filter**: Lets you filter by *All Sentiments*, *Positive*, *Negative*, or *Neutral*.
  - **Rating Filter**: Lets you filter by *All Ratings*, *1 Star*, *2 Star*, *3 Star*, *4 Star*, or *5 Star*.
  - **Clear Filters Button**: One click resets everything back to the default view.

- **Reviews Table**:
  - Displays customer reviews with 6 columns:
    1. **Record ID**: Unique identifier (e.g., `REV_000001`).
    2. **Product**: Full product name.
    3. **Rating**: Star badge (e.g., `★ 5.0`).
    4. **Customer Review / Summary**: The actual text written by the buyer.
    5. **Dataset Sentiment**: Color-coded pill (`Positive` in green, `Negative` in red, `Neutral` in orange).
    6. **View Details**: An **"Inspect"** button on each row.

- **Pagination Controls (Bottom)**:
  - Displays count summary (e.g., *"Showing 15 of 2,000 reviews"*).
  - Page navigation arrows (`<` and `>`) and current page number (e.g., *Page 1 of 134*).

- **"Summarize Filtered Reviews" Button (Top Right)**:
  - A blue button that creates an on-the-fly extractive summary of the currently visible/filtered reviews.

---

## 🎮 What Can You Do on This Page?

- **Search by keyword**:
  - Type `"cooler"` and click **Search** $\rightarrow$ Instantly displays only reviews about air coolers.
- **Filter by complaint**:
  - Select **Negative** in the Sentiment dropdown $\rightarrow$ Shows customer complaints and poor experiences.
- **Filter by 1-Star ratings**:
  - Select **1 Star** in the Rating dropdown $\rightarrow$ Shows the most critical feedback.
- **Click "Inspect" on any review**:
  - Opens a pop-up modal showing:
    - The complete customer review and title.
    - AI sentiment probabilities (how confident the model is).
    - Detected issue categories with matched quote snippets.
- **Click "Summarize Filtered Reviews"**:
  - Opens a summary modal that condenses hundreds of reviews into 3 key takeaways with source citations.
- **Click "Clear Filters"**:
  - Clears all search keywords and dropdowns back to showing all 50,000 records.
