import pandas as pd


def clean_price_df(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: ensure datetime column is named 'Date' and sorted."""
    if df.empty:
        return df
    # If the DataFrame has a DatetimeIndex, bring it into a column named 'Date'
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    # If columns are a MultiIndex (e.g., yfinance output), flatten them to simple names.
    if isinstance(df.columns, pd.MultiIndex):
        def _flatten(col):
            # prefer first level name; if second level is meaningful (not empty), append it
            first, second = col[0], col[1]
            if second is None or second == "":
                return first
            return f"{first}_{second}"

        df.columns = [ _flatten(c) for c in df.columns ]

    # Make sure there's a Date column (case-insensitive)
    if 'Date' not in df.columns:
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'Date'})
        else:
            df['Date'] = pd.to_datetime(df.iloc[:, 0])

    df['Date'] = pd.to_datetime(df['Date'])
    # Normalize common price column names so downstream code can rely on them
    def _find_col(key: str):
        kl = key.lower()
        # exact match first
        for c in df.columns:
            if c.lower() == kl:
                return c
        # then partial match
        for c in df.columns:
            if kl in c.lower():
                return c
        return None

    for canonical in ['Close', 'Volume', 'Open', 'High', 'Low']:
        if canonical not in df.columns:
            found = _find_col(canonical)
            if found:
                df[canonical] = df[found]

    df = df.sort_values('Date').reset_index(drop=True)
    return df


def summarize_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sentiment scores into a simple summary."""
    if df.empty:
        return pd.DataFrame()
    mean_scores = df[['neg', 'neu', 'pos', 'compound']].mean()
    summary = pd.DataFrame(mean_scores).T
    return summary
