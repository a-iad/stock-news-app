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
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"

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
                print(f"Error fetching news: {response.status_code}")
                return []

            articles = response.json().get('articles', [])
            
            # Process each article with DeepSeek
            processed_articles = []
            for article in articles:
                analysis = self._analyze_with_deepseek(article, symbol)
                if analysis:
                    processed_article = {
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'published_at': article['publishedAt'],
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

    def _analyze_with_deepseek(self, article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze article content using DeepSeek API."""
        try:
            prompt = f"""
            Analyze the following news article about stock {symbol} and provide:
            1. Potential impact on the stock (positive/negative/neutral)
            2. Brief explanation of why
            3. Confidence level (0-100)

            Article Title: {article['title']}
            Article Description: {article['description']}

            Format the response as JSON with keys: impact, explanation, confidence_score
            """

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }

            response = requests.post(self.deepseek_url, headers=headers, json=data)
            if response.status_code != 200:
                print(f"Error from DeepSeek API: {response.status_code}")
                return None

            # Parse the response
            analysis = response.json()['choices'][0]['message']['content']
            return json.loads(analysis)

        except Exception as e:
            print(f"Error analyzing with DeepSeek: {str(e)}")
            return None

    def get_economic_impact(self, symbols: List[str]) -> Dict[str, Any]:
        """Get aggregated economic impact for multiple symbols."""
        all_news = []
        for symbol in symbols:
            news = self.fetch_relevant_news(symbol)
            all_news.extend(news)

        if not all_news:
            return None

        return {
            'total_articles': len(all_news),
            'timestamp': datetime.now(),
            'news_items': all_news[:5]  # Return top 5 most relevant news items
        }
