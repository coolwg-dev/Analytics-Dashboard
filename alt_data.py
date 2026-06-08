import requests
import pandas as pd
import logging
from datetime import datetime
from typing import Optional


logger = logging.getLogger(__name__)


def _to_epoch(dt):
    if isinstance(dt, (int, float)):
        return int(dt)
    if isinstance(dt, datetime):
        return int(dt.timestamp())
    # assume isoformat string
    return int(datetime.fromisoformat(dt).timestamp())


def fetch_reddit_posts(query: str, after: Optional[str] = None, before: Optional[str] = None, size: int = 500) -> pd.DataFrame:
    """Fetch Reddit submissions from Pushshift matching `query` between `after` and `before`.

    `after` and `before` can be ISO date strings (YYYY-MM-DD) or epoch ints.
    Returns a DataFrame with columns: title, selftext, created_utc, url, subreddit.
    """
    base = "https://api.pushshift.io/reddit/search/submission/"
    params = {"q": query, "size": size}
    if after:
        params["after"] = _to_epoch(after)
    if before:
        params["before"] = _to_epoch(before)
    try:
        logger.info("requesting reddit posts query=%s after=%s before=%s size=%s", query, after, before, size)
        resp = requests.get(base, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        rows = []
        for item in data:
            rows.append({
                "title": item.get("title", ""),
                "selftext": item.get("selftext", ""),
                "created_utc": item.get("created_utc"),
                "url": item.get("url", ""),
                "subreddit": item.get("subreddit", ""),
            })
        df = pd.DataFrame(rows)
        if not df.empty and "created_utc" in df.columns:
            df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s")
        logger.info("reddit request returned %d rows for query=%s", len(df), query)
        return df
    except Exception:
        logger.exception("failed to fetch reddit posts for query=%s", query)
        return pd.DataFrame()


def fetch_newsapi_headlines(api_key: Optional[str], query: str, from_date: Optional[str] = None, to_date: Optional[str] = None, page_size: int = 100) -> list:
    """Fetch headlines via NewsAPI.org (requires API key). Returns list of article dicts.

    If `api_key` is None or empty, returns an empty list.
    """
    if not api_key:
        logger.info("newsapi skipped because no api key was provided")
        return []
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "pageSize": page_size, "apiKey": api_key}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    try:
        logger.info("requesting newsapi headlines query=%s from=%s to=%s page_size=%s", query, from_date, to_date, page_size)
        r = requests.get(url, params=params, timeout=1000)
        r.raise_for_status()
        data = r.json().get("articles", [])
        # normalize to simple dicts
        out = []
        for a in data:
            out.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "publishedAt": a.get("publishedAt"),
                "url": a.get("url"),
                "source": a.get("source", {}).get("name"),
            })
        logger.info("newsapi returned %d articles for query=%s", len(out), query)
        return out
    except Exception:
        logger.exception("failed to fetch newsapi headlines for query=%s", query)
        return []
