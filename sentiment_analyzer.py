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
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text, flags=re.MULTILINE)
        # Remove special characters but keep punctuation for better sentiment analysis
        text = re.sub(r'[^A-Za-z0-9\s.,!?]', ' ', text)
        # Remove extra whitespace
        return ' '.join(text.split())

    def get_sentiment_score(self, text):
        """Get sentiment score for a piece of text."""
        try:
            if not text or not isinstance(text, str):
                return 0.0

            text = self.clean_text(text)
            if not text:
                return 0.0

            analysis = TextBlob(text)
            # Combine polarity and subjectivity for a more nuanced score
            score = analysis.sentiment.polarity * (1 + analysis.sentiment.subjectivity)
            return score
        except Exception as e:
            print(f"Error in sentiment scoring: {str(e)}")
            return 0.0

    def analyze_market_sentiment(self, symbol, cache_ok=True):
        """Analyze market sentiment for a given symbol using news headlines."""
        try:
            print(f"\nAnalyzing sentiment for {symbol}")

            # Check cache first
            if cache_ok and symbol in self.cache:
                cached_result = self.cache[symbol]
                if datetime.now() - cached_result['timestamp'] < self.cache_duration:
                    print(f"Using cached sentiment for {symbol}")
                    return cached_result['data']

            # Fetch news using yfinance
            print(f"Fetching news for {symbol}")
            ticker = yf.Ticker(symbol)
            news = ticker.news or []

            # Process headlines and descriptions
            print(f"Analyzing {len(news)} news items for {symbol}")
            sentiments = []
            news_items = []

            for item in news:
                try:
                    headline = str(item.get('title', ''))
                    description = str(item.get('description', ''))

                    # Store news items for reference
                    news_items.append({
                        'headline': headline,
                        'description': description,
                        'timestamp': item.get('providerPublishTime', '')
                    })

                    # Process headline (weighted more heavily)
                    if headline:
                        headline_score = self.get_sentiment_score(headline)
                        sentiments.append(headline_score * 1.5)  # Headlines weighted more

                    # Process description
                    if description:
                        desc_score = self.get_sentiment_score(description)
                        sentiments.append(desc_score)

                except Exception as e:
                    print(f"Error processing news item: {str(e)}")
                    continue

            # Calculate sentiment metrics
            result = self._calculate_sentiment_metrics(symbol, sentiments, news_items)

            # Cache the result
            self.cache[symbol] = {
                'data': result,
                'timestamp': datetime.now()
            }

            print(f"Sentiment analysis completed for {symbol}: {result['sentiment_direction']}")
            return result

        except Exception as e:
            print(f"Error in market sentiment analysis for {symbol}: {str(e)}")
            return self._get_neutral_sentiment(symbol)

    def _calculate_sentiment_metrics(self, symbol, sentiments, news_items):
        """Calculate sentiment metrics from collected scores."""
        if not sentiments:
            return self._get_neutral_sentiment(symbol)

        avg_sentiment = sum(sentiments) / len(sentiments)

        # Determine sentiment direction with more granular categories
        if avg_sentiment > 0.3:
            direction = 'Very Positive'
        elif avg_sentiment > 0.1:
            direction = 'Positive'
        elif avg_sentiment < -0.3:
            direction = 'Very Negative'
        elif avg_sentiment < -0.1:
            direction = 'Negative'
        else:
            direction = 'Neutral'

        return {
            'symbol': symbol,
            'average_sentiment': avg_sentiment,
            'news_count': len(news_items),
            'sentiment_direction': direction,
            'timestamp': datetime.now(),
            'news_items': news_items[:5]  # Store last 5 news items
        }

    def _get_neutral_sentiment(self, symbol):
        """Return neutral sentiment for cases with no data."""
        return {
            'symbol': symbol,
            'average_sentiment': 0,
            'news_count': 0,
            'sentiment_direction': 'Neutral',
            'timestamp': datetime.now(),
            'news_items': []
        }

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

            # Calculate weighted market sentiment
            total_weight = sum(s['news_count'] for s in sentiments)
            if total_weight == 0:
                avg_market_sentiment = 0
            else:
                avg_market_sentiment = sum(
                    s['average_sentiment'] * s['news_count'] 
                    for s in sentiments
                ) / total_weight

            print(f"Overall market sentiment: {avg_market_sentiment:.2f}")

            return {
                'market_sentiment': avg_market_sentiment,
                'analyzed_symbols': len(sentiments),
                'total_news_analyzed': total_weight,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error getting market mood: {str(e)}")
            return None