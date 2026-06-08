import pandas as pd


def clean_price_df(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning: ensure datetime column is named 'Date' and sorted."""
    if df.empty:
        return df
    # Make sure there's a Date column
    if 'Date' not in df.columns:
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'Date'})
        else:
            df['Date'] = pd.to_datetime(df.iloc[:, 0])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df


def summarize_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sentiment scores into a simple summary."""
    if df.empty:
        return pd.DataFrame()
    mean_scores = df[['neg', 'neu', 'pos', 'compound']].mean()
    summary = pd.DataFrame(mean_scores).T
    return summary
