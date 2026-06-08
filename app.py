import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
from datetime import date, timedelta

from data_fetcher import fetch_price_data, fetch_news_headlines, compute_sentiment
from processing import clean_price_df, summarize_sentiment
from alt_data import fetch_reddit_posts, fetch_newsapi_headlines
from cache import get_cache, set_cache


st.set_page_config(page_title="Investment Dashboard", layout="wide")


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _cache_key(*parts):
    return "::".join([str(p) for p in parts])


def _fetch_with_cache(key, fetcher, ttl):
    cached = get_cache(key, ttl)
    if cached is not None:
        logger.info("cache hit for %s", key)
        return cached
    logger.info("cache miss for %s", key)
    val = fetcher()
    set_cache(key, val, ttl_seconds=ttl if ttl else 0)
    return val


def main():
    st.title("Automated Investment & Data Analytics Dashboard")

    with st.sidebar:
        ticker = st.text_input("Ticker (e.g. AAPL)", value="AAPL")
        end = st.date_input("End date", value=date.today())
        start = st.date_input("Start date", value=end - timedelta(days=90))
        cache_ttl = st.selectbox("Cache TTL (seconds)", [0, 3600, 86400, 604800], index=1)
        enable_reddit = st.checkbox("Include Reddit sentiment (Pushshift)")
        newsapi_key = st.text_input("NewsAPI key (optional)")
        fetch = st.button("Fetch Data")

    if fetch and ticker:
        status = st.empty()
        with st.spinner("Fetching price and external data..."):
            status.info("Starting data fetch")
            logger.info("fetch started ticker=%s start=%s end=%s", ticker, start.isoformat(), end.isoformat())
            # Price data (cached)
            status.info("Fetching price data")
            logger.info("calling fetch_price_data for %s", ticker)
            price_key = _cache_key('price', ticker, start, end)
            price_df = _fetch_with_cache(price_key, lambda: fetch_price_data(ticker, start.isoformat(), end.isoformat()), cache_ttl)
            price_df = clean_price_df(price_df) if isinstance(price_df, pd.DataFrame) else pd.DataFrame()

            # YFinance headlines + sentiment (cached)
            status.info("Fetching YFinance headlines")
            logger.info("calling fetch_news_headlines for %s", ticker)
            ynews_key = _cache_key('ynews', ticker)
            ynews = _fetch_with_cache(ynews_key, lambda: fetch_news_headlines(ticker), cache_ttl)
            ysent = compute_sentiment(ynews) if ynews else pd.DataFrame()

            # NewsAPI (if provided)
            newsapi_key_used = newsapi_key.strip() or None
            news_key = _cache_key('newsapi', ticker, start, end)
            newsapi = []
            if newsapi_key_used:
                status.info("Fetching NewsAPI articles")
                logger.info("calling fetch_newsapi_headlines for %s", ticker)
                newsapi = _fetch_with_cache(news_key, lambda: fetch_newsapi_headlines(newsapi_key_used, ticker, from_date=start.isoformat(), to_date=end.isoformat()), cache_ttl)
                logger.info("NewsAPI returned %d articles", len(newsapi))
            else:
                logger.info("NewsAPI skipped because no key was provided")

            # Reddit (Pushshift) sentiment (optional)
            reddit_df = pd.DataFrame()
            reddit_sent_df = pd.DataFrame()
            if enable_reddit:
                status.info("Fetching Reddit posts")
                logger.info("calling fetch_reddit_posts for %s", ticker)
                reddit_key = _cache_key('reddit', ticker, start, end)
                reddit_df = _fetch_with_cache(reddit_key, lambda: fetch_reddit_posts(ticker, after=start.isoformat(), before=end.isoformat()), cache_ttl)
                if not reddit_df.empty:
                    titles = reddit_df['title'].fillna('').astype(str).tolist()
                    sent = compute_sentiment(titles)
                    if not sent.empty:
                        reddit_sent_df = sent.copy()
                        reddit_sent_df['created_utc'] = reddit_df['created_utc'].reset_index(drop=True)

            status.success("Fetch complete")
            logger.info("fetch complete ticker=%s price_rows=%d ynews=%d newsapi=%d reddit_rows=%d", ticker, len(price_df), len(ynews), len(newsapi), len(reddit_df))

        # Price visuals
        if price_df.empty:
            st.warning("No price data found for that ticker/date range.")
        else:
            st.subheader(f"Price chart — {ticker}")
            # compute moving averages
            price_df['SMA_20'] = price_df['Close'].rolling(20).mean()
            price_df['SMA_50'] = price_df['Close'].rolling(50).mean()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=price_df['Date'], y=price_df['Close'], name='Close', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=price_df['Date'], y=price_df['SMA_20'], name='SMA 20', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=price_df['Date'], y=price_df['SMA_50'], name='SMA 50', line=dict(color='green')))
            # volume as bars on secondary y
            fig.update_layout(xaxis=dict(rangeslider=dict(visible=False)))
            st.plotly_chart(fig, use_container_width=True)

            # Volume
            if 'Volume' in price_df.columns:
                st.subheader('Volume')
                fig2 = px.bar(price_df, x='Date', y='Volume', title='Volume')
                st.plotly_chart(fig2, use_container_width=True)

        # YFinance news sentiment
        st.subheader("YFinance News Sentiment")
        if ysent.empty:
            st.info("No yfinance headlines found to analyze sentiment.")
        else:
            st.table(ysent[['headline', 'compound']].sort_values('compound', ascending=False).head(10))
            summary = summarize_sentiment(ysent)
            if not summary.empty:
                st.bar_chart(summary[['neg', 'neu', 'pos']].T)

        # NewsAPI results
        if newsapi:
            st.subheader('NewsAPI results')
            st.write(f"Found {len(newsapi)} articles from NewsAPI")
            df_newsapi = pd.DataFrame(newsapi)
            st.dataframe(df_newsapi[['publishedAt', 'source', 'title']].head(20))

        # Reddit sentiment over time
        if enable_reddit:
            st.subheader('Reddit sentiment (Pushshift)')
            if reddit_df.empty:
                st.info('No Reddit posts found for that query.')
            else:
                st.write(f"Fetched {len(reddit_df)} Reddit posts")
                if not reddit_sent_df.empty:
                    reddit_sent_df['date'] = pd.to_datetime(reddit_sent_df['created_utc']).dt.date
                    daily = reddit_sent_df.groupby('date')['compound'].mean().reset_index()
                    fig3 = px.line(daily, x='date', y='compound', title='Daily mean Reddit sentiment')
                    st.plotly_chart(fig3, use_container_width=True)


if __name__ == "__main__":
    main()
