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

        # Keywords that indicate market relevance
        self.market_keywords = [
            'stock price', 'market cap', 'trading volume', 'earnings report',
            'quarterly results', 'revenue growth', 'profit margin', 'market share',
            'analyst rating', 'price target', 'financial results', 'market performance'
        ]

    def _is_relevant_news(self, title, description, date_published):
        """Check if news is relevant and recent."""
        if not title or not description or not date_published:
            return False

        # Check if the article is recent (within last 7 days)
        try:
            pub_date = datetime.strptime(date_published, "%Y-%m-%dT%H:%M:%SZ")
            if datetime.now() - pub_date > timedelta(days=7):
                return False
        except Exception as e:
            print(f"Error parsing date: {str(e)}")
            return False

        # Check content relevance
        text = (title + ' ' + description).lower()
        relevant_keywords = sum(1 for keyword in self.market_keywords if keyword.lower() in text)
        return relevant_keywords >= 2  # Must contain at least 2 relevant keywords

    def analyze_market_sentiment(self, symbol):
        """Get sentiment analysis for a stock symbol."""
        try:
            print(f"\nAnalyzing sentiment for {symbol}")

            # Prepare search query focusing on market-related news
            query = f"({symbol} stock) AND (market OR trading OR earnings)"
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': from_date,
                'pageSize': 25
            }

            response = requests.get(self.news_api_url, params=params)
            if response.status_code != 200:
                print(f"Error fetching news: {response.status_code}")
                return self._get_neutral_sentiment(symbol)

            articles = response.json().get('articles', [])
            relevant_articles = []
            sentiments = []
            significant_news = []

            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                published_at = article.get('publishedAt', '')

                if self._is_relevant_news(title, description, published_at):
                    relevant_articles.append(article)
                    try:
                        # Analyze title with higher weight
                        title_blob = TextBlob(title)
                        title_score = title_blob.sentiment.polarity
                        title_weight = 1.5 + abs(title_score)  # Weight stronger sentiments more
                        sentiments.append((title_score, title_weight))

                        # Store significant news (strong sentiment)
                        if abs(title_score) > 0.3:
                            pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                            significant_news.append({
                                'title': title,
                                'score': title_score,
                                'impact': 'High' if abs(title_score) > 0.6 else 'Medium',
                                'published_at': pub_date.strftime("%Y-%m-%d %H:%M")
                            })

                        # Analyze description
                        if description:
                            desc_blob = TextBlob(description)
                            desc_score = desc_blob.sentiment.polarity
                            sentiments.append((desc_score, 1.0))

                    except Exception as e:
                        print(f"Error analyzing article: {str(e)}")
                        continue

            if not sentiments:
                print(f"No relevant articles found for {symbol}")
                return self._get_neutral_sentiment(symbol)

            # Calculate weighted average sentiment
            total_weight = sum(weight for _, weight in sentiments)
            weighted_sentiment = sum(score * weight for score, weight in sentiments) / total_weight

            # Sort significant news by date and score
            significant_news.sort(key=lambda x: (
                datetime.strptime(x['published_at'], "%Y-%m-%d %H:%M"),
                abs(x['score'])
            ), reverse=True)

            # Determine trend and confidence
            sentiment_trend = self._get_sentiment_trend(weighted_sentiment)
            confidence_score = min(len(relevant_articles) / 10, 1.0) * (1 + abs(weighted_sentiment))

            result = {
                'symbol': symbol,
                'average_sentiment': weighted_sentiment,
                'sentiment_direction': sentiment_trend['direction'],
                'confidence': confidence_score * 100,
                'news_count': len(relevant_articles),
                'key_insights': significant_news[:3],
                'market_impact': sentiment_trend['impact'],
                'timestamp': datetime.now()
            }

            print(f"Analysis complete for {symbol}: {result['sentiment_direction']} (Score: {weighted_sentiment:.2f})")
            return result

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
            'news_count': 0,
            'key_insights': [],
            'market_impact': 'No Impact',
            'timestamp': datetime.now()
        }

    def get_market_mood(self, symbols):
        """Get overall market sentiment."""
        try:
            all_sentiments = []
            total_confidence = 0
            total_news = 0

            for symbol in symbols:
                sentiment = self.analyze_market_sentiment(symbol)
                if sentiment and sentiment['news_count'] > 0:
                    all_sentiments.append(sentiment)
                    total_confidence += sentiment['confidence']
                    total_news += sentiment['news_count']

            if not all_sentiments:
                return None

            weighted_sentiment = sum(
                s['average_sentiment'] * (s['confidence'] / 100) * s['news_count']
                for s in all_sentiments
            ) / (total_confidence * len(all_sentiments) if total_confidence * len(all_sentiments) > 0 else 1)

            return {
                'market_sentiment': weighted_sentiment,
                'analyzed_symbols': len(all_sentiments),
                'total_news': total_news,
                'average_confidence': total_confidence / len(all_sentiments) if all_sentiments else 0,
                'timestamp': datetime.now()
            }

        except Exception as e:
            print(f"Error in market mood analysis: {str(e)}")
            return None