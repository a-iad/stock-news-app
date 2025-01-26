import os
import requests
from datetime import datetime, timedelta
from textblob import TextBlob
from typing import Dict, Any

class SentimentAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.news_api_url = "https://newsapi.org/v2/everything"

        # Keywords that indicate market relevance
        self.market_keywords = [
            'stock price', 'market cap', 'trading volume', 'earnings report',
            'quarterly results', 'revenue growth', 'profit margin', 'market share',
            'analyst rating', 'price target', 'financial results', 'market performance'
        ]

    def analyze_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze sentiment from news and market data for a stock symbol."""
        try:
            print(f"\nAnalyzing market sentiment for {symbol}")

            # Get recent news articles and social discussions
            articles = self._fetch_market_news(symbol)

            if not articles:
                print(f"No recent news found for {symbol}")
                return self._get_neutral_sentiment(symbol)

            sentiments = []
            significant_posts = []

            for article in articles:
                try:
                    text = f"{article.get('title', '')} {article.get('description', '')}"
                    blob = TextBlob(text)
                    sentiment_score = blob.sentiment.polarity

                    # Weight articles with market-relevant keywords more heavily
                    weight = 1.0
                    text_lower = text.lower()
                    relevant_keywords = sum(1 for keyword in self.market_keywords if keyword in text_lower)
                    if relevant_keywords > 0:
                        weight += 0.5 * relevant_keywords

                    sentiments.append((sentiment_score, weight))

                    if abs(sentiment_score) > 0.3:
                        significant_posts.append({
                            'text': article.get('title', ''),
                            'sentiment': sentiment_score,
                            'timestamp': article.get('publishedAt', datetime.now().isoformat()),
                            'impact': 'High' if abs(sentiment_score) > 0.6 else 'Medium'
                        })
                except Exception as e:
                    print(f"Error analyzing article: {str(e)}")
                    continue

            if not sentiments:
                return self._get_neutral_sentiment(symbol)

            total_weight = sum(weight for _, weight in sentiments)
            weighted_sentiment = sum(score * weight for score, weight in sentiments) / total_weight

            sentiment_trend = self._get_sentiment_trend(weighted_sentiment)
            confidence_score = min(len(sentiments) / 10, 1.0) * (1 + abs(weighted_sentiment))

            return {
                'symbol': symbol,
                'average_sentiment': weighted_sentiment,
                'sentiment_direction': sentiment_trend['direction'],
                'confidence': confidence_score * 100,
                'total_posts': len(sentiments),
                'key_posts': significant_posts[:5],
                'market_impact': sentiment_trend['impact'],
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return self._get_neutral_sentiment(symbol)

    def _get_sentiment_trend(self, sentiment_score):
        """Get detailed sentiment trend analysis."""
        if sentiment_score >= 0.5:
            return {'direction': 'Strong Bullish', 'impact': 'High Positive'}
        elif sentiment_score >= 0.2:
            return {'direction': 'Bullish', 'impact': 'Positive'}
        elif sentiment_score <= -0.5:
            return {'direction': 'Strong Bearish', 'impact': 'High Negative'}
        elif sentiment_score <= -0.2:
            return {'direction': 'Bearish', 'impact': 'Negative'}
        else:
            return {'direction': 'Neutral', 'impact': 'Low'}

    def _get_neutral_sentiment(self, symbol):
        """Return neutral sentiment for cases with no data."""
        return {
            'symbol': symbol,
            'average_sentiment': 0,
            'sentiment_direction': 'Neutral',
            'confidence': 0,
            'total_posts': 0,
            'key_posts': [],
            'market_impact': 'No Impact',
            'timestamp': datetime.now()
        }

    def _fetch_market_news(self, symbol: str) -> list:
        """Fetch recent market news for analysis."""
        try:
            if not self.news_api_key:
                print("NEWS_API_KEY not found")
                return []

            query = f"({symbol} stock) AND (market OR trading OR finance OR investor)"
            from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

            response = requests.get(
                self.news_api_url,
                params={
                    'q': query,
                    'apiKey': self.news_api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'from': from_date,
                    'pageSize': 25
                }
            )

            if response.status_code != 200:
                print(f"News API error: {response.status_code}")
                return []

            return response.json().get('articles', [])
        except Exception as e:
            print(f"Error fetching market news: {str(e)}")
            return []

    def get_market_mood(self, symbols):
        """Get overall market sentiment."""
        try:
            all_sentiments = []
            total_confidence = 0
            total_posts = 0

            for symbol in symbols:
                sentiment = self.analyze_social_sentiment(symbol)
                if sentiment and sentiment['total_posts'] > 0:
                    all_sentiments.append(sentiment)
                    total_confidence += sentiment['confidence']
                    total_posts += sentiment['total_posts']

            if not all_sentiments:
                return None

            weighted_sentiment = sum(
                s['average_sentiment'] * (s['confidence'] / 100) * s['total_posts']
                for s in all_sentiments
            ) / (total_confidence * len(all_sentiments) if total_confidence * len(all_sentiments) > 0 else 1)

            return {
                'market_sentiment': weighted_sentiment,
                'analyzed_symbols': len(all_sentiments),
                'total_posts': total_posts,
                'average_confidence': total_confidence / len(all_sentiments) if all_sentiments else 0,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error in market mood analysis: {str(e)}")
            return None