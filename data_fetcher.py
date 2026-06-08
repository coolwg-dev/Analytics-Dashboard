import yfinance as yf
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def fetch_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download historical price data for `ticker` between `start` and `end`.

    Dates should be strings like '2023-01-01'. Returns a DataFrame with Date index reset.
    """
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    return df


def fetch_news_headlines(ticker: str, limit: int = 30) -> list:
    """Fetch recent news headlines for `ticker` using yfinance's news feed.

    Returns a list of headline strings (may be empty).
    """
    try:
        tk = yf.Ticker(ticker)
        news = tk.news
        headlines = [item.get("title", "") for item in news if item.get("title")]
        return headlines[:limit]
    except Exception:
        return []


def compute_sentiment(headlines: list) -> pd.DataFrame:
    """Run VADER sentiment on a list of headlines and return a DataFrame."""
    analyzer = SentimentIntensityAnalyzer()
    rows = []
    for h in headlines:
        s = analyzer.polarity_scores(h)
        rows.append({"headline": h, **s})
    return pd.DataFrame(rows)
