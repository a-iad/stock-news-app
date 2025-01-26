import os
import requests
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

class NewsAnalyzer:
    def __init__(self):
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.deepseek_url = "https://api.deepseek.ai/v1/chat/completions"

    def fetch_relevant_news(self, symbol: str, company_name: str = None) -> Dict[str, Any]:
        """Fetch and analyze news for a stock."""
        try:
            # Prepare search query
            query_parts = [f"({symbol} stock OR {company_name})" if company_name else symbol]
            query = ' '.join(query_parts + ['AND (market OR earnings OR financial OR economy)'])

            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 10,
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            }

            response = requests.get(self.news_api_url, params=params)
            if response.status_code != 200:
                print(f"Error fetching news: {response.status_code}")
                return {'summary_analysis': None, 'articles': []}

            articles = response.json().get('articles', [])
            if not articles:
                return {'summary_analysis': None, 'articles': []}

            # Generate summary analysis using DeepSeek
            summary_prompt = (
                f"Analyze these recent news articles about {symbol}:\n"
                + "\n".join([f"Article {i+1}:\nTitle: {a['title']}\nSummary: {a['description']}"
                            for i, a in enumerate(articles[:3])])
                + "\n\nProvide exactly 3 main points that matter most for investors, considering:"
                + "\n1. Direct stock impact & market reaction"
                + "\n2. Historical context or similar past events"
                + "\n3. Broader implications for the sector/market"
                + "\n\nFormat: Return a JSON object with structure:"
                + "\n{"
                + '\n    "key_points": ['
                + '\n        {'
                + '\n            "point": "The main insight",'
                + '\n            "impact": "Detailed explanation with historical context"'
                + '\n        },'
                + '\n        // ... (3 points total)'
                + '\n    ]'
                + '\n}'
            )

            summary_analysis = None
            if self.deepseek_api_key:
                try:
                    summary_response = requests.post(
                        self.deepseek_url,
                        headers={
                            "Authorization": f"Bearer {self.deepseek_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": summary_prompt}],
                            "temperature": 0.7
                        },
                        timeout=10
                    )

                    if summary_response.status_code == 200:
                        summary_analysis = json.loads(summary_response.json()['choices'][0]['message']['content'])
                except Exception as e:
                    print(f"DeepSeek API error: {str(e)}")

            # Process individual articles
            processed_articles = []
            for article in articles[:4]:  # Limit to 4 most relevant articles
                article_analysis = self._analyze_article(article, symbol)
                if article_analysis:
                    processed_articles.append({
                        'title': article['title'],
                        'summary': article['description'],
                        'url': article['url'],
                        'published_at': article['publishedAt'],
                        'analysis': article_analysis
                    })

            return {
                'summary_analysis': summary_analysis,
                'articles': processed_articles
            }

        except Exception as e:
            print(f"Error in news analysis: {str(e)}")
            return {'summary_analysis': None, 'articles': []}

    def _analyze_article(self, article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze individual article for relevance and impact."""
        if not article.get('title') or not article.get('description'):
            return None

        try:
            prompt = (
                f"Analyze this news article about {symbol}:\n"
                f"Title: {article['title']}\n"
                f"Content: {article['description']}\n\n"
                "Provide:\n"
                "1. Market relevance (specific reason why this matters)\n"
                "2. Potential impact on the stock (positive/negative/neutral with reasoning)\n"
                "3. Confidence in the analysis (0-100)\n"
                "4. Historical context or similar past events if applicable\n\n"
                "Format: JSON with keys 'market_relevance', 'potential_impact', 'confidence', 'historical_context'"
            )

            if self.deepseek_api_key:
                response = requests.post(
                    self.deepseek_url,
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    return json.loads(response.json()['choices'][0]['message']['content'])

            return self._simple_analysis(article['title'], article['description'])

        except Exception as e:
            print(f"Error analyzing article: {str(e)}")
            return self._simple_analysis(article['title'], article['description'])

    def _simple_analysis(self, title: str, description: str) -> Dict[str, Any]:
        """Fallback simple analysis when DeepSeek is unavailable."""
        text = (title + ' ' + description).lower()
        impact_terms = {
            'positive': ['surge', 'gain', 'rise', 'growth', 'profit', 'success'],
            'negative': ['fall', 'drop', 'decline', 'loss', 'risk', 'down']
        }

        sentiment = {'positive': 0, 'negative': 0}
        for impact, terms in impact_terms.items():
            sentiment[impact] = sum(1 for term in terms if term in text)

        total = sum(sentiment.values())
        if total == 0:
            return {
                'market_relevance': 'General market news that may affect the stock',
                'potential_impact': 'Neutral',
                'confidence': 50,
                'historical_context': None
            }

        ratio = sentiment['positive'] / total if total > 0 else 0.5
        if ratio > 0.6:
            impact = 'Positive'
            confidence = 70
        elif ratio < 0.4:
            impact = 'Negative'
            confidence = 70
        else:
            impact = 'Neutral'
            confidence = 60

        return {
            'market_relevance': 'Article contains significant market-related indicators',
            'potential_impact': impact,
            'confidence': confidence,
            'historical_context': None
        }