import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class MarketData:
    @staticmethod
    def get_stock_data(symbol, period='1mo'):
        """Fetch stock data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            return pd.DataFrame()

    @staticmethod
    def get_market_indicators():
        """Fetch major market indicators."""
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
