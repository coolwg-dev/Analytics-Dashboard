import yfinance as yf
import pandas as pd
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


logger = logging.getLogger(__name__)


def fetch_price_data(ticker: str, start: str, end: str) -> pd.DataFrame:
    """Download historical price data for `ticker` between `start` and `end`.

    Dates should be strings like '2023-01-01'. Returns a DataFrame with Date index reset.
    """
    logger.info("requesting yfinance price data ticker=%s start=%s end=%s", ticker, start, end)
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df is None or df.empty:
        logger.info("yfinance price data returned no rows for ticker=%s", ticker)
        return pd.DataFrame()
    logger.info("yfinance price data returned %d rows for ticker=%s", len(df), ticker)
    df = df.reset_index()
    return df


def fetch_news_headlines(ticker: str, limit: int = 30) -> list:
    """Fetch recent news headlines for `ticker` using yfinance's news feed.

    Returns a list of headline strings (may be empty).
    """
    try:
        tk = yf.Ticker(ticker)
        logger.info("requesting yfinance headlines ticker=%s", ticker)
        news = tk.news
        headlines = []
        for item in news:
            if isinstance(item, dict):
                content = item.get("content") or item
                title = content.get("title", "") if isinstance(content, dict) else ""
                if title:
                    headlines.append(title)
        logger.info("yfinance headlines returned %d items for ticker=%s", len(headlines), ticker)
        return headlines[:limit]
    except Exception:
        logger.exception("failed to fetch yfinance headlines for ticker=%s", ticker)
        return []


def compute_sentiment(headlines: list) -> pd.DataFrame:
    """Run VADER sentiment on a list of headlines and return a DataFrame."""
    analyzer = SentimentIntensityAnalyzer()
    rows = []
    for h in headlines:
        s = analyzer.polarity_scores(h)
        rows.append({"headline": h, **s})
    return pd.DataFrame(rows)
