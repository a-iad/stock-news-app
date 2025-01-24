import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import re
import yfinance as yf

class SentimentAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)

    def clean_text(self, text):
        """Clean text by removing special characters and extra whitespace."""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
        return ' '.join(text.split())

    def get_sentiment_score(self, text):
        """Get sentiment score for a piece of text."""
        if not text or not isinstance(text, str):
            return 0.0
        text = self.clean_text(text)
        if not text:
            return 0.0
        analysis = TextBlob(text)
        return analysis.sentiment.polarity

    def analyze_market_sentiment(self, symbol, cache_ok=True):
        """Analyze market sentiment for a given symbol using news headlines."""
        try:
            print(f"\nAnalyzing sentiment for {symbol}")

            # Check cache first
            if cache_ok and symbol in self.cache:
                cached_result = self.cache[symbol]
                if datetime.now() - cached_result['timestamp'] < self.cache_duration:
                    print(f"Using cached sentiment for {symbol}")
                    return cached_result

            # Fetch news using yfinance
            print(f"Fetching news for {symbol}")
            ticker = yf.Ticker(symbol)
            news = ticker.news or []

            # Process headlines and descriptions
            print(f"Analyzing {len(news)} news items for {symbol}")
            sentiments = []

            for item in news:
                headline = str(item.get('title', ''))
                description = str(item.get('description', ''))

                # Process each text piece separately for better granularity
                if headline:
                    sentiment = self.get_sentiment_score(headline)
                    sentiments.append(sentiment * 1.5)  # Headlines weighted more

                if description:
                    sentiment = self.get_sentiment_score(description)
                    sentiments.append(sentiment)

            # If no valid sentiments found, return neutral sentiment
            if not sentiments:
                print(f"No valid sentiment data for {symbol}")
                return {
                    'symbol': symbol,
                    'average_sentiment': 0,
                    'news_count': len(news),
                    'sentiment_direction': 'Neutral',
                    'timestamp': datetime.now()
                }

            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            print(f"Average sentiment for {symbol}: {avg_sentiment:.2f}")

            # Determine sentiment direction
            if avg_sentiment > 0.2:
                direction = 'Very Positive'
            elif avg_sentiment > 0:
                direction = 'Positive'
            elif avg_sentiment < -0.2:
                direction = 'Very Negative'
            elif avg_sentiment < 0:
                direction = 'Negative'
            else:
                direction = 'Neutral'

            result = {
                'symbol': symbol,
                'average_sentiment': avg_sentiment,
                'news_count': len(news),
                'sentiment_direction': direction,
                'timestamp': datetime.now()
            }

            # Cache the result
            self.cache[symbol] = result
            return result

        except Exception as e:
            print(f"Error analyzing market sentiment for {symbol}: {str(e)}")
            return None

    def get_market_mood(self, symbols):
        """Get overall market mood based on multiple symbols."""
        try:
            print("\nAnalyzing overall market mood")
            sentiments = []
            for symbol in symbols:
                sentiment = self.analyze_market_sentiment(symbol)
                if sentiment:
                    sentiments.append(sentiment)

            if not sentiments:
                print("No valid sentiment data for market mood")
                return None

            # Calculate average market sentiment
            avg_market_sentiment = sum(s['average_sentiment'] for s in sentiments) / len(sentiments)
            print(f"Overall market sentiment: {avg_market_sentiment:.2f}")

            return {
                'market_sentiment': avg_market_sentiment,
                'analyzed_symbols': len(sentiments),
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error getting market mood: {str(e)}")
            return None