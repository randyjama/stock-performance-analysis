import yfinance as yf
import pandas as pd
from pandas_datareader import data as pdr
import requests
import os
from textblob import TextBlob
from bs4 import BeautifulSoup

yf.pdr_override()

# Get API Key from Environment Variable
# NEWS_API_KEY = os.environ.get("NEWSDATA_API_KEY")

def get_sp1500_tickers():
    table_500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    table_400 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies')[0]
    table_600 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_600_companies')[0]

    tickers_500 = table_500['Symbol'].tolist()
    tickers_400 = table_400['Symbol'].tolist()
    tickers_600 = table_600['Symbol'].tolist()

    all_tickers = tickers_500 + tickers_400 + tickers_600
    return all_tickers

# def get_news_sentiment(ticker):
#     # Check if the API key is available
#     if not NEWS_API_KEY:
#         print("Please set the NEWSDATA_API_KEY environment variable!")
#         return 0

#     # Define the endpoint for newsdata.io
#     # endpoint = f"https://api.newsdata.io/v1/articles?tickers={ticker}&limit={num_articles}&apikey={NEWS_API_KEY}"
#     endpoint = f"https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&q={ticker}"
    
#     # Get news articles related to the ticker
#     response = requests.get(endpoint)
#     articles = response.json().get('data', [])
    
#     # Calculate the sentiment of each article's title + description
#     sentiments = [TextBlob(article['title'] + ' ' + article['description']).sentiment.polarity for article in articles]
    
#     # Average the sentiment values
#     avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    
#     return avg_sentiment

def get_nth_trading_day_back(ticker, n, end_date):
    # Get enough data to ensure we capture at least n trading days
    temp_start_date = end_date - pd.Timedelta(days=n*2)  # 2x to ensure we capture weekends, holidays, etc.
    df = pdr.get_data_yahoo(ticker, start=temp_start_date, end=end_date)
    
    # Ensure there are enough trading days in the data
    if len(df) < n:
        raise ValueError(f"Data contains less than {n} trading days.")
    
    return df.index[-n]

def stock_analysis(tickers):
    end_date = pd.to_datetime('today')
    start_date = get_nth_trading_day_back('^GSPC', 2, end_date)

    sp500 = pdr.get_data_yahoo('^GSPC', start=start_date, end=end_date)
    sp500_return = ((sp500['Close'][-1] - sp500['Close'][0]) / sp500['Close'][0]) * 100

    stock_data = {}

    for ticker in tickers:
        try:
            df = pdr.get_data_yahoo(ticker, start=start_date, end=end_date)

            # Simple Rate of Return
            simple_return = ((df['Close'][-1] - df['Close'][0]) / df['Close'][0]) * 100

            # Volume Analysis
            volume_increase = (df['Volume'][-1] > df['Volume'].rolling(window=5).mean().iloc[-1])

            # Relative Strength vs. Market
            relative_strength = simple_return - sp500_return

            # Recent Momentum
            recent_momentum = (df['Close'][-10:].pct_change().mean()) * 100

            # Check for recent sudden dips
            recent_dip = 1 if df['Close'].pct_change().iloc[-1] < -0.05 else 0

            # Pivot Points
            pivot = (df['High'][-1] + df['Low'][-1] + df['Close'][-1]) / 3
            r1 = 2 * pivot - df['Low'][-1]
            s1 = 2 * pivot - df['High'][-1]
            bullish_pivot = df['Close'][-1] > r1
            bearish_pivot = df['Close'][-1] < s1

            # 50-Day Moving Average Cross
            ma50 = df['Close'].rolling(window=50).mean()
            ma_cross = df['Close'][-1] > ma50.iloc[-1]

            # News Sentiment
            # news_sentiment = get_news_sentiment(ticker)
            # Add Value to Score
            # (5 * news_sentiment)
            
            # Score calculation
            score = simple_return + (5 if volume_increase else 0) + (5 if bullish_pivot else -5 if bearish_pivot else 0) + relative_strength + (10 if recent_dip else 0) + recent_momentum + (10 if ma_cross else 0)

            stock_data[ticker] = score

        except Exception as e:
            print(f"Couldn't fetch data for {ticker}. Error: {e}")
            continue

    sorted_stocks = sorted(stock_data.items(), key=lambda x: x[1], reverse=True)

    return sorted_stocks[:10]

if __name__ == '__main__':
    tickers = get_sp1500_tickers()
    top_stocks = stock_analysis(tickers)

    print("Top 10 stocks for potential short term growth:")
    if not top_stocks:
        print("No stocks met the criteria.")
    else:
        for stock, growth in top_stocks:
            print(f"Ticker: {stock}, Predicted Growth: {growth:.2f}%")

