import requests
import pandas as pd
from datetime import datetime
from typing import Optional


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
        return df
    except Exception:
        return pd.DataFrame()


def fetch_newsapi_headlines(api_key: Optional[str], query: str, from_date: Optional[str] = None, to_date: Optional[str] = None, page_size: int = 100) -> list:
    """Fetch headlines via NewsAPI.org (requires API key). Returns list of article dicts.

    If `api_key` is None or empty, returns an empty list.
    """
    if not api_key:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "pageSize": page_size, "apiKey": api_key}
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    try:
        r = requests.get(url, params=params, timeout=10)
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
        return out
    except Exception:
        return []
