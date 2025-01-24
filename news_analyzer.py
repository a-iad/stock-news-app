import requests
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import os

class NewsAnalyzer:
    def __init__(self):
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.deepseek_api_key = "sk-0d6270c9b0bf422f8617e207a3236ec6"
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.deepseek_url = "https://api.deepseek.ai/v1/chat/completions"

    def _get_cached_news(self, query: str) -> Dict[str, Any]:
        """Get cached news if available and not expired."""
        if query in self.cache:
            cached_data = self.cache[query]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
        return None

    def fetch_relevant_news(self, symbol: str, company_name: str = None) -> List[Dict[str, Any]]:
        """Fetch relevant news for a given stock symbol."""
        try:
            # Check cache first
            cache_key = f"{symbol}_{company_name or ''}"
            cached_news = self._get_cached_news(cache_key)
            if cached_news:
                return cached_news

            # Prepare search query
            query_parts = [symbol]
            if company_name:
                query_parts.append(company_name)
            query = ' OR '.join(query_parts)

            # Add financial and economic terms
            query += ' AND (economy OR market OR finance OR stocks)'

            # Fetch news from News API
            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 10
            }

            response = requests.get(self.news_api_url, params=params)
            if response.status_code != 200:
                print(f"Error fetching news: {response.status_code} - {response.text}")
                return []

            articles = response.json().get('articles', [])

            # Process each article with DeepSeek
            processed_articles = []
            for article in articles:
                analysis = self._analyze_article_sentiment(article, symbol)
                if analysis:
                    processed_article = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'analysis': analysis
                    }
                    processed_articles.append(processed_article)

            # Cache the results
            self.cache[cache_key] = {
                'data': processed_articles,
                'timestamp': datetime.now()
            }

            return processed_articles

        except Exception as e:
            print(f"Error fetching news for {symbol}: {str(e)}")
            return []

    def _analyze_article_sentiment(self, article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze article sentiment using rule-based approach as fallback."""
        try:
            title = article.get('title', '')
            description = article.get('description', '')

            # Default analysis using simple rules
            positive_words = ['surge', 'gain', 'rise', 'jump', 'growth', 'profit', 'success', 'positive']
            negative_words = ['fall', 'drop', 'decline', 'loss', 'crash', 'risk', 'down', 'negative']

            text = (title + ' ' + description).lower()
            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)

            # Determine impact
            total = pos_count + neg_count
            if total == 0:
                impact = "Neutral"
                confidence = 50
            else:
                ratio = pos_count / total
                if ratio > 0.7:
                    impact = "Very Positive"
                    confidence = 85
                elif ratio > 0.5:
                    impact = "Positive"
                    confidence = 70
                elif ratio < 0.3:
                    impact = "Very Negative"
                    confidence = 85
                elif ratio < 0.5:
                    impact = "Negative"
                    confidence = 70
                else:
                    impact = "Neutral"
                    confidence = 60

            explanation = f"Based on keyword analysis: found {pos_count} positive and {neg_count} negative indicators."

            return {
                'impact': impact,
                'explanation': explanation,
                'confidence_score': confidence
            }

        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return {
                'impact': 'Neutral',
                'explanation': 'Unable to analyze sentiment',
                'confidence_score': 50
            }

    def get_economic_impact(self, symbols: List[str]) -> Dict[str, Any]:
        """Get aggregated economic impact for multiple symbols."""
        all_news = []
        for symbol in symbols:
            news = self.fetch_relevant_news(symbol)
            all_news.extend(news)

        if not all_news:
            return {
                'total_articles': 0,
                'timestamp': datetime.now(),
                'news_items': []
            }

        # Sort by published date
        all_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)

        return {
            'total_articles': len(all_news),
            'timestamp': datetime.now(),
            'news_items': all_news[:5]  # Return top 5 most relevant news items
        }