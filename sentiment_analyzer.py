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
        text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
        return ' '.join(text.split())

    def get_sentiment_score(self, text):
        """Get sentiment score for a piece of text."""
        analysis = TextBlob(self.clean_text(text))
        return analysis.sentiment.polarity

    def analyze_market_sentiment(self, symbol, cache_ok=True):
        """Analyze market sentiment for a given symbol using news headlines."""
        try:
            # Check cache first
            if cache_ok and symbol in self.cache:
                cached_result = self.cache[symbol]
                if datetime.now() - cached_result['timestamp'] < self.cache_duration:
                    return cached_result

            # Fetch news using yfinance
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                return {
                    'symbol': symbol,
                    'average_sentiment': 0,
                    'news_count': 0,
                    'sentiment_direction': 'Neutral',
                    'timestamp': datetime.now()
                }

            # Analyze sentiment of headlines and descriptions
            sentiments = []
            for item in news:
                headline = item.get('title', '')
                description = item.get('description', '')

                # Combine headline and description for better context
                full_text = f"{headline} {description}"
                sentiment = self.get_sentiment_score(full_text)
                sentiments.append(sentiment)

            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

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
            print(f"Error analyzing market sentiment: {str(e)}")
            return None

    def get_market_mood(self, symbols):
        """Get overall market mood based on multiple symbols."""
        try:
            sentiments = []
            for symbol in symbols:
                sentiment = self.analyze_market_sentiment(symbol)
                if sentiment:
                    sentiments.append(sentiment)

            if not sentiments:
                return None

            # Calculate average market sentiment
            avg_market_sentiment = sum(s['average_sentiment'] for s in sentiments) / len(sentiments)

            return {
                'market_sentiment': avg_market_sentiment,
                'analyzed_symbols': len(sentiments),
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error getting market mood: {str(e)}")
            return None