import pandas as pd
from textblob import TextBlob
from datetime import datetime, timedelta
import yfinance as yf

class SentimentAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)

    def analyze_market_sentiment(self, symbol):
        """Get sentiment analysis for a stock symbol."""
        try:
            print(f"\nAnalyzing sentiment for {symbol}")
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                print(f"No news found for {symbol}")
                return self._get_neutral_sentiment(symbol)

            sentiments = []
            news_count = 0

            for article in news:
                title = article.get('title', '')
                if not title:
                    continue

                analysis = TextBlob(title)
                sentiment_score = analysis.sentiment.polarity
                sentiments.append(sentiment_score)
                news_count += 1
                print(f"Analyzed: {title[:50]}... Score: {sentiment_score:.2f}")

            if not sentiments:
                return self._get_neutral_sentiment(symbol)

            avg_sentiment = sum(sentiments) / len(sentiments)
            print(f"Average sentiment for {symbol}: {avg_sentiment:.2f}")

            # Map sentiment to direction
            if avg_sentiment >= 0.3:
                direction = "Very Positive"
            elif avg_sentiment >= 0.1:
                direction = "Positive"
            elif avg_sentiment <= -0.3:
                direction = "Very Negative"
            elif avg_sentiment <= -0.1:
                direction = "Negative"
            else:
                direction = "Neutral"

            return {
                'symbol': symbol,
                'average_sentiment': avg_sentiment,
                'news_count': news_count,
                'sentiment_direction': direction,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error in sentiment analysis for {symbol}: {str(e)}")
            return self._get_neutral_sentiment(symbol)

    def _get_neutral_sentiment(self, symbol):
        return {
            'symbol': symbol,
            'average_sentiment': 0,
            'news_count': 0,
            'sentiment_direction': 'Neutral',
            'timestamp': datetime.now()
        }

    def get_market_mood(self, symbols):
        """Get overall market sentiment based on multiple symbols."""
        try:
            all_sentiments = []
            for symbol in symbols:
                sentiment = self.analyze_market_sentiment(symbol)
                if sentiment and sentiment['news_count'] > 0:
                    all_sentiments.append(sentiment)

            if not all_sentiments:
                return None

            # Calculate weighted average sentiment
            total_news = sum(s['news_count'] for s in all_sentiments)
            if total_news == 0:
                return None

            weighted_sentiment = sum(
                s['average_sentiment'] * s['news_count'] 
                for s in all_sentiments
            ) / total_news

            return {
                'market_sentiment': weighted_sentiment,
                'analyzed_symbols': len(all_sentiments),
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error in market mood analysis: {str(e)}")
            return None