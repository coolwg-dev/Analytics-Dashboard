# Automated Investment & Data Analytics Dashboard

This project demonstrates a minimal pipeline to fetch financial price data and news headlines, compute basic sentiment, and present an interactive dashboard using Streamlit.

Getting started

1. Create and activate a Python virtual environment (Python 3.9+ recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:

```bash
streamlit run app.py
```

Notes
- Price data and headlines are fetched using `yfinance`.
- Sentiment is computed with VADER (`vaderSentiment`).
- This is a starter template — you can extend data sources, add caching, and improve UI.
 - Alternative data sources: Reddit (Pushshift) and NewsAPI support have been added.
 - Simple file-based caching is provided in `cache.py` to avoid re-fetching during development.
 - To use NewsAPI, provide your API key in the sidebar when running the app.
