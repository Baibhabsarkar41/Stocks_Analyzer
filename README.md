# 📊 Stocks Analyzer — Smart Indian Stock Market Insights (NSE)

> A modern, AI-powered stock analysis and prediction platform built using React and FastAPI. Designed to help investors make better decisions with scraped data, real-time news, and intelligent recommendations.

---

## 🔥 Features

### 🧠 AI-Powered Stock Predictions
- Analyze NSE/BSE listed stocks using Google-scraped data.
- Generate intelligent recommendations ("Buy", "Hold", "Sell") using large language models (LLMs).

### 🔎 Real-time Stock Data Scraping
- Input any listed stock.
- Scrapes detailed financial metrics from Google such as:
  - Market Cap
  - Day/Year Range
  - P/E Ratio
  - Previous Close
  - Dividend Yield
  - Average Volume
  - Exchange Info

### 📰 Trending Market News (India)
- Scrapes Yahoo News daily for top Indian stock market headlines.
- Cleans and stores headlines, snippets, and full articles.
- Summarizes articles using LLMs for quick consumption.

### ⭐ "My Stocks" Watchlist
- Users can save stocks of interest with all scraped and analyzed data.
- Backend-persisted stock list available across sessions.
- Designed for future user-based authentication and expansion.

---

## 📐 Architecture

```

Frontend (React.js)
└── StockScraperPage
└── MyStocksPage
↓ API Calls
Backend (FastAPI + BeautifulSoup + httpx)
└── /stock-data/       → Scrapes and returns stock metrics
└── /summarize/        → Summarizes stock news + data
└── /trending-news-india/ → Daily Yahoo news scraping
Database (SQLite / PostgreSQL)

````

## 🚀 Installation

### Backend Setup

```bash
git clone https://github.com/yourusername/Stocks_Analyzer.git
cd Stocks_Analyzer/backend

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install -r requirements.txt

# Create a .env file for sensitive variables (e.g., Gemini API key)
touch .env
````

### Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

---

## 🔐 Environment Variables (`.env`)

Store in `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./stocks.db
```

## 🧪 Example Walkthrough

- Search → Ticker map
User types “Tata Motors”. Frontend maps the name to the ticker from a local CSV (e.g., TATAMOTORS.NS for NSE / TATAMOTORS.BO for BSE).

- Live scrape from Google Finance (fresh every search)
Backend (FastAPI + BeautifulSoup) fetches Google Finance for that ticker and extracts:

- Price snapshot & change

- Details: previous close, day range, 52-week range, market cap, average volume, P/E ratio, dividend yield, primary exchange, and other tags

- Latest GF news items (ads/videos filtered out)
(None of this GF data is stored in the DB.)

- News enrichment with caching (Yahoo News, 24h reuse)
Backend checks SQLite for a Yahoo News summary stored in the last 24 hours.

- If missing/expired → scrape Yahoo News → summarize with Gemini → store summary + timestamp in DB.

- If present → reuse the cached summary (no re-scrape).

- AI brief (final summary)
Backend sends [GF snapshot + cached Yahoo summary] to Gemini with a structured prompt.
Gemini returns a concise insight (e.g., “Moderate Buy — strong growth signals, solid volume.”)
(Insight is informational, not financial advice.)

- Deliver & persist
Frontend displays: GF details, GF news, and the Gemini brief.
User clicks “Save to My Stocks” → persists the ticker, key details, and AI brief to /my-stocks (SQLite) for future tracking.
Optional: user can email the AI brief.

## Data & Design Notes

* Sources: Google Finance (live, per search) + Yahoo News (summarized & cached for 24h).

* Storage: Users, search history, and Yahoo News summaries only (no GF data persisted).

* Stack: React (frontend), FastAPI (backend), SQLite (DB), BeautifulSoup (scraping), Gemini API (summaries).

* Scope: This app summarizes public info; it does not provide investment advice.

## 📈 Planned Enhancements

* ✅ Add daily news scraping with deduplication
* ✅ Summarize using Gemini
* ✅ User Authentication (JWT-based)
* 🔄 Add stock charts using `TradingView` or `recharts`
* 🔄 Export saved stocks as CSV
* 🔄 Deploy to AWS (EC2 + RDS/PostgreSQL)


## 👨‍💻 Author

**Baibhab Sarkar**

> Third-year CS Undergrad | Backend & AI Developer
> [LinkedIn](https://www.linkedin.com/in/baibhab-sarkar-b69913293/) | [GitHub](https://github.com/Baibhabsarkar41)

---

## 📜 License

MIT License — feel free to use and expand this project.

---

## ⭐ If you find this useful...

Give it a ⭐ on GitHub — it helps others discover the project!



