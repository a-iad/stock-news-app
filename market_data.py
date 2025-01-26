import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from predictions import MarketPredictor
from news_analyzer import NewsAnalyzer
import traceback

class MarketData:
    def __init__(self):
        self.predictor = MarketPredictor()
        self.news_analyzer = NewsAnalyzer()
        print("MarketData initialized")

    def get_news_analysis(self, symbol):
        """Get news analysis for a stock."""
        try:
            print(f"\nFetching news analysis for {symbol}")
            ticker = yf.Ticker(symbol)
            company_name = ticker.info.get('longName', '')
            print(f"Company name: {company_name}")

            news_data = self.news_analyzer.fetch_relevant_news(symbol, company_name)
            if news_data and news_data.get('articles'):
                print(f"Successfully fetched news for {symbol}")
                print(f"Found {len(news_data['articles'])} articles")
                if news_data.get('summary_analysis'):
                    print("Generated summary analysis")
                return news_data

            print(f"No news data returned for {symbol}")
            return {'summary_analysis': None, 'articles': []}
        except Exception as e:
            print(f"Error in get_news_analysis for {symbol}: {str(e)}")
            traceback.print_exc()
            return {'summary_analysis': None, 'articles': []}

    @staticmethod
    def get_stock_data(symbol, period='1mo'):
        """Fetch stock data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            if data.empty:
                print(f"No data found for symbol: {symbol}")
                return pd.DataFrame()
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_stock_prediction(self, symbol):
        """Get prediction for a specific stock."""
        try:
            print(f"Fetching prediction for {symbol}")
            # Get 6 months of historical data for better prediction
            data = self.get_stock_data(symbol, period='6mo')
            if data.empty:
                print(f"No historical data available for {symbol}")
                return None

            print(f"Training model for {symbol} with {len(data)} data points")
            # Train model if needed
            if self.predictor.train(data):
                prediction = self.predictor.predict_trend(data)
                if prediction:
                    print(f"Prediction generated for {symbol}: {prediction['trend']}")
                    return prediction
            print(f"Failed to generate prediction for {symbol}")
            return None
        except Exception as e:
            print(f"Error in prediction process for {symbol}: {str(e)}")
            return None

    def get_market_sentiment(self):
        """Get overall market sentiment."""
        try:
            print("Fetching overall market sentiment")
            major_symbols = ['^GSPC', '^DJI', 'AAPL', 'MSFT', 'GOOGL']
            sentiment = self.sentiment_analyzer.get_market_mood(major_symbols)
            if sentiment:
                print(f"Market sentiment analysis successful: {sentiment['market_sentiment']:.2f}")
            else:
                print("No market sentiment data available")
            return sentiment
        except Exception as e:
            print(f"Error in market sentiment analysis: {str(e)}")
            return None

    @staticmethod
    def get_market_indicators():
        """Fetch major market indicators."""
        try:
            indicators = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^VIX': 'Volatility Index',
                'GC=F': 'Gold',
                '^TNX': '10-Year Treasury'
            }
            data = {}
            for symbol, name in indicators.items():
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    data[name] = hist['Close'].iloc[-1]
            return data
        except Exception as e:
            print(f"Error fetching market indicators: {str(e)}")
            return {}

    @staticmethod
    def get_economic_calendar():
        """Simulate economic calendar events."""
        today = datetime.now()
        events = [
            {
                'date': today + timedelta(days=1),
                'event': 'Fed Interest Rate Decision',
                'importance': 'High'
            },
            {
                'date': today + timedelta(days=2),
                'event': 'GDP Report',
                'importance': 'High'
            },
            {
                'date': today + timedelta(days=3),
                'event': 'Unemployment Rate',
                'importance': 'Medium'
            }
        ]
        return pd.DataFrame(events)

    def get_economic_news(self):
        """Get overall economic news impact."""
        try:
            print("Fetching economic news impact")
            major_symbols = ['^GSPC', '^DJI', 'AAPL', 'MSFT', 'GOOGL']
            news_impact = self.news_analyzer.get_economic_impact(major_symbols)
            if news_impact:
                print(f"Found {news_impact['total_articles']} economic news items")
            else:
                print("No economic news found")
            return news_impact
        except Exception as e:
            print(f"Error fetching economic news: {str(e)}")
            return None