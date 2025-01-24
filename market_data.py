import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from predictions import MarketPredictor
from sentiment_analyzer import SentimentAnalyzer

class MarketData:
    def __init__(self):
        self.predictor = MarketPredictor()
        self.sentiment_analyzer = SentimentAnalyzer()

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

    def get_sentiment_analysis(self, symbol):
        """Get sentiment analysis for a stock."""
        return self.sentiment_analyzer.analyze_market_sentiment(symbol)

    def get_market_sentiment(self):
        """Get overall market sentiment."""
        major_symbols = ['^GSPC', '^DJI', 'AAPL', 'MSFT', 'GOOGL']
        return self.sentiment_analyzer.get_market_mood(major_symbols)

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