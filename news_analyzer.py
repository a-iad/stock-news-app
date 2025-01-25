import os
import requests
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any
import os

class NewsAnalyzer:
    def __init__(self):
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY', "sk-0d6270c9b0bf422f8617e207a3236ec6")
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.deepseek_url = "https://api.deepseek.ai/v1/chat/completions"

        # Keywords that indicate market relevance
        self.market_keywords = [
            'stock price', 'market cap', 'trading volume', 'earnings report',
            'quarterly results', 'revenue growth', 'profit margin', 'market share',
            'analyst rating', 'price target', 'financial results', 'market performance'
        ]

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
                analysis = self._analyze_article_content(article, symbol)
                if analysis:
                    processed_article = {
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'url': article.get('url', ''),
                        'published_at': article.get('publishedAt', ''),
                        'analysis': analysis,
                        'relevance_explanation': self._generate_relevance_explanation(article, symbol)
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

    def _analyze_article_content(self, article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze article content using DeepSeek for insights."""
        try:
            title = article.get('title', '')
            description = article.get('description', '')

            if not title or not description:
                return None

            # Prepare prompt for DeepSeek
            prompt = f"""Analyze the following news article about {symbol} stock:
            Title: {title}
            Description: {description}

            Provide:
            1. The potential market impact (positive/negative/neutral)
            2. Confidence level (0-100)
            3. Historical context or similar events if applicable
            4. Key implications for investors

            Format: JSON with keys 'impact', 'confidence_score', 'historical_context', 'implications'
            """

            # Call DeepSeek API
            try:
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
                    }
                )

                if response.status_code == 200:
                    try:
                        analysis = json.loads(response.json()['choices'][0]['message']['content'])
                        return analysis
                    except:
                        # Fallback to simple analysis if DeepSeek response parsing fails
                        return self._simple_sentiment_analysis(title, description)
                else:
                    return self._simple_sentiment_analysis(title, description)

            except Exception as e:
                print(f"DeepSeek API error: {str(e)}")
                return self._simple_sentiment_analysis(title, description)

        except Exception as e:
            print(f"Error in article analysis: {str(e)}")
            return None

    def _simple_sentiment_analysis(self, title: str, description: str) -> Dict[str, Any]:
        """Fallback simple sentiment analysis."""
        text = (title + ' ' + description).lower()

        # Simple keyword-based analysis
        positive_words = ['surge', 'gain', 'rise', 'jump', 'growth', 'profit', 'success']
        negative_words = ['fall', 'drop', 'decline', 'loss', 'crash', 'risk', 'down']

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        total = pos_count + neg_count
        if total == 0:
            return {
                'impact': 'Neutral',
                'confidence_score': 50,
                'explanation': 'No clear sentiment indicators found.'
            }

        sentiment_ratio = pos_count / total
        if sentiment_ratio > 0.6:
            impact = 'Positive'
            confidence = 70
        elif sentiment_ratio < 0.4:
            impact = 'Negative'
            confidence = 70
        else:
            impact = 'Neutral'
            confidence = 60

        return {
            'impact': impact,
            'confidence_score': confidence,
            'explanation': f"Based on keyword analysis: found {pos_count} positive and {neg_count} negative indicators."
        }

    def _generate_relevance_explanation(self, article: Dict[str, Any], symbol: str) -> str:
        """Generate explanation of why the article is relevant."""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        text = title + ' ' + description

        relevance_factors = []

        # Check for direct company mention
        if symbol.lower() in text:
            relevance_factors.append("Direct mention of company stock")

        # Check for market impact keywords
        market_impact = sum(1 for keyword in self.market_keywords if keyword.lower() in text)
        if market_impact > 0:
            relevance_factors.append(f"Contains {market_impact} market-related indicators")

        # Check for financial metrics
        if any(term in text for term in ['revenue', 'profit', 'earnings', 'growth']):
            relevance_factors.append("Discusses key financial metrics")

        # Check for market sentiment
        if any(term in text for term in ['analyst', 'rating', 'upgrade', 'downgrade']):
            relevance_factors.append("Contains market sentiment indicators")

        if not relevance_factors:
            return "General market news that may impact the stock"

        return " • ".join(relevance_factors)

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

        # Sort by published date and relevance score
        all_news.sort(
            key=lambda x: (
                datetime.strptime(x.get('published_at', '2000-01-01T00:00:00Z'), "%Y-%m-%dT%H:%M:%SZ"),
                x['analysis'].get('confidence_score', 0) if x.get('analysis') else 0
            ),
            reverse=True
        )

        return {
            'total_articles': len(all_news),
            'timestamp': datetime.now(),
            'news_items': all_news[:5]  # Return top 5 most relevant news items
        }