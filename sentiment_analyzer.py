import os
import requests
from datetime import datetime, timedelta
from textblob import TextBlob

class SentimentAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.news_api_url = "https://newsapi.org/v2/everything"

    def analyze_market_sentiment(self, symbol):
        """Get sentiment analysis for a stock symbol."""
        try:
            print(f"\nAnalyzing sentiment for {symbol}")

            if not self.news_api_key:
                print("Error: NEWS_API_KEY not found in environment variables")
                return self._get_neutral_sentiment(symbol)

            # Prepare search query with company name and stock symbol
            query = f"{symbol} stock market news"

            # Fetch news from News API
            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20
            }

            print(f"Fetching news for {symbol}...")
            response = requests.get(self.news_api_url, params=params)

            if response.status_code != 200:
                print(f"Error fetching news: Status {response.status_code}")
                print(f"Response: {response.text}")
                return self._get_neutral_sentiment(symbol)

            data = response.json()
            articles = data.get('articles', [])
            total_articles = len(articles)
            print(f"Found {total_articles} articles for {symbol}")

            if not articles:
                print(f"No articles found for {symbol}")
                return self._get_neutral_sentiment(symbol)

            sentiments = []
            news_count = 0

            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')

                if title and isinstance(title, str):
                    try:
                        analysis = TextBlob(title)
                        sentiment_score = analysis.sentiment.polarity
                        sentiments.append(sentiment_score * 1.5)  # Weight headlines more
                        news_count += 1
                        print(f"Title sentiment: {sentiment_score:.2f} - {title[:50]}...")
                    except Exception as e:
                        print(f"Error analyzing title: {str(e)}")

                if description and isinstance(description, str):
                    try:
                        analysis = TextBlob(description)
                        sentiment_score = analysis.sentiment.polarity
                        sentiments.append(sentiment_score)
                        print(f"Description sentiment: {sentiment_score:.2f}")
                    except Exception as e:
                        print(f"Error analyzing description: {str(e)}")

            if not sentiments:
                print("No valid sentiment scores calculated")
                return self._get_neutral_sentiment(symbol)

            avg_sentiment = sum(sentiments) / len(sentiments)
            print(f"Average sentiment for {symbol}: {avg_sentiment:.2f}")

            # Map sentiment to direction with more granular thresholds
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

            result = {
                'symbol': symbol,
                'average_sentiment': avg_sentiment,
                'news_count': news_count,
                'sentiment_direction': direction,
                'timestamp': datetime.now()
            }
            print(f"Sentiment analysis result for {symbol}: {direction} (Score: {avg_sentiment:.2f}, News: {news_count})")
            return result

        except Exception as e:
            print(f"Error in sentiment analysis for {symbol}: {str(e)}")
            return self._get_neutral_sentiment(symbol)

    def _get_neutral_sentiment(self, symbol):
        """Return neutral sentiment for cases with no data."""
        return {
            'symbol': symbol,
            'average_sentiment': 0,
            'news_count': 0,
            'sentiment_direction': 'Neutral',
            'timestamp': datetime.now()
        }

    def get_market_mood(self, symbols):
        """Get overall market sentiment."""
        try:
            all_sentiments = []
            analyzed_count = 0

            for symbol in symbols:
                sentiment = self.analyze_market_sentiment(symbol)
                if sentiment and sentiment['news_count'] > 0:
                    all_sentiments.append(sentiment)
                    analyzed_count += 1
                    print(f"Added sentiment for {symbol}: {sentiment['sentiment_direction']}")

            if not all_sentiments:
                print("No valid sentiments found for market mood calculation")
                return None

            # Calculate weighted average sentiment
            total_news = sum(s['news_count'] for s in all_sentiments)
            if total_news == 0:
                print("No news articles found for sentiment calculation")
                return None

            weighted_sentiment = sum(
                s['average_sentiment'] * s['news_count'] 
                for s in all_sentiments
            ) / total_news

            result = {
                'market_sentiment': weighted_sentiment,
                'analyzed_symbols': analyzed_count,
                'timestamp': datetime.now()
            }
            print(f"Market mood calculation complete. Overall sentiment: {weighted_sentiment:.2f}")
            return result

        except Exception as e:
            print(f"Error in market mood analysis: {str(e)}")
            return None