import os
import requests
from datetime import datetime, timedelta
import json
from typing import Dict, Any
import traceback

class NewsAnalyzer:
    def __init__(self):
        self.news_api_key = os.environ.get('NEWS_API_KEY')
        self.deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')
        self.news_api_url = "https://newsapi.org/v2/everything"
        self.deepseek_url = "https://api.deepseek.ai/v1/chat/completions"
        print("NewsAnalyzer initialized")
        if not self.news_api_key:
            print("WARNING: NEWS_API_KEY not found in environment")
        if not self.deepseek_api_key:
            print("WARNING: DEEPSEEK_API_KEY not found in environment")

    def fetch_relevant_news(self, symbol: str, company_name: str = None) -> Dict[str, Any]:
        """Fetch and analyze news for a stock."""
        try:
            print(f"\nFetching news for {symbol} ({company_name if company_name else 'no company name'})")

            # Prepare search query
            query_parts = [f"({symbol} stock OR {company_name})" if company_name else symbol]
            query = ' '.join(query_parts + ['AND (market OR earnings OR financial OR economy)'])
            print(f"Search query: {query}")

            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 10,
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            }

            # Fetch news articles
            response = requests.get(self.news_api_url, params=params)
            if response.status_code != 200:
                print(f"News API error: Status {response.status_code}")
                print(f"Response: {response.text}")
                return {'summary_analysis': None, 'articles': []}

            articles = response.json().get('articles', [])
            if not articles:
                print("No articles found")
                return {'summary_analysis': None, 'articles': []}

            print(f"Found {len(articles)} articles")

            # Generate summary analysis if possible
            summary_analysis = None
            if self.deepseek_api_key and articles:
                try:
                    summary_analysis = self._generate_summary(symbol, articles[:3])
                    if summary_analysis:
                        print("Successfully generated summary analysis")
                    else:
                        print("Failed to generate summary analysis")
                except Exception as e:
                    print(f"Error in summary generation: {str(e)}")
                    traceback.print_exc()

            # Process individual articles
            processed_articles = []
            for i, article in enumerate(articles[:4]):
                try:
                    article_analysis = self._analyze_article(article, symbol)
                    if article_analysis:
                        processed_articles.append({
                            'title': article['title'],
                            'summary': article['description'],
                            'url': article['url'],
                            'published_at': article['publishedAt'],
                            'analysis': article_analysis
                        })
                        print(f"Processed article {i+1}")
                except Exception as e:
                    print(f"Error processing article {i+1}: {str(e)}")
                    continue

            result = {
                'summary_analysis': summary_analysis,
                'articles': processed_articles
            }

            print(f"Returning {len(processed_articles)} processed articles")
            if summary_analysis:
                print("Including summary analysis")

            return result

        except Exception as e:
            print(f"Error in fetch_relevant_news: {str(e)}")
            traceback.print_exc()
            return {'summary_analysis': None, 'articles': []}

    def _generate_summary(self, symbol: str, articles: list) -> Dict[str, Any]:
        """Generate summary analysis for articles."""
        try:
            summary_prompt = (
                f"Analyze these recent news articles about {symbol}:\n"
                + "\n".join([f"Article {i+1}:\nTitle: {a['title']}\nSummary: {a['description']}"
                            for i, a in enumerate(articles)])
                + "\n\nProvide exactly 3 main points that matter most for investors, considering:"
                + "\n1. Direct stock impact & market reaction"
                + "\n2. Historical context or similar past events"
                + "\n3. Broader implications for the sector/market"
                + "\n\nFormat: JSON with structure:"
                + '{\n    "key_points": [\n        {"point": "Main insight", "impact": "Detailed explanation"}\n    ]\n}'
            )

            response = requests.post(
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

            if response.status_code == 200:
                return json.loads(response.json()['choices'][0]['message']['content'])
            print(f"DeepSeek API error: {response.status_code}")
            return None

        except Exception as e:
            print(f"Error in summary generation: {str(e)}")
            return None

    def _analyze_article(self, article: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Analyze individual article for relevance and impact."""
        if not article.get('title') or not article.get('description'):
            return None

        try:
            # Always try DeepSeek analysis first
            if self.deepseek_api_key:
                prompt = (
                    f"Analyze this news article about {symbol} stock:\n"
                    f"Title: {article['title']}\n"
                    f"Content: {article['description']}\n\n"
                    "Provide analysis in this format:\n"
                    "1. Market relevance: Explain specifically how this news affects the stock's business, operations, or market position\n"
                    "2. Potential impact: Analyze if this is positive/negative/neutral for the stock price and explain why\n"
                    "3. Confidence: Rate 0-100 how confident you are in this analysis\n"
                    "4. Historical context: Mention any similar past events or patterns\n\n"
                    "Be specific about the connection between the news and the stock. Focus on direct business implications.\n\n"
                    "Format: JSON with keys 'market_relevance', 'potential_impact', 'confidence', 'historical_context'"
                )

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

            # Fallback to enhanced simple analysis
            return self._simple_analysis(article['title'], article['description'])

        except Exception as e:
            print(f"Error analyzing article: {str(e)}")
            return self._simple_analysis(article['title'], article['description'])

    def _simple_analysis(self, title: str, description: str) -> Dict[str, Any]:
        """Enhanced fallback simple analysis when DeepSeek is unavailable."""
        text = (title + ' ' + description).lower()

        # Enhanced keyword analysis
        business_terms = {
            'revenue': ['revenue', 'sales', 'earnings'],
            'operations': ['production', 'operations', 'expansion'],
            'market': ['market share', 'competition', 'industry'],
            'product': ['product', 'service', 'launch'],
            'financial': ['profit', 'margin', 'cost']
        }

        impact_terms = {
            'positive': ['surge', 'gain', 'rise', 'growth', 'profit', 'success', 'beat', 'exceed'],
            'negative': ['fall', 'drop', 'decline', 'loss', 'risk', 'down', 'miss', 'below']
        }

        # Analyze business aspects
        business_aspects = []
        for aspect, terms in business_terms.items():
            if any(term in text for term in terms):
                business_aspects.append(aspect)

        # Analyze sentiment
        sentiment = {'positive': 0, 'negative': 0}
        for impact, terms in impact_terms.items():
            sentiment[impact] = sum(1 for term in terms if term in text)

        # Generate relevance explanation
        if business_aspects:
            relevance = f"News impacts company's {', '.join(business_aspects)}"
        else:
            relevance = "General market news that may affect the stock price"

        # Determine impact
        total = sum(sentiment.values())
        if total == 0:
            return {
                'market_relevance': relevance,
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
            'market_relevance': relevance,
            'potential_impact': impact,
            'confidence': confidence,
            'historical_context': None
        }