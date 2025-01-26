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
                    f"As a financial analyst, analyze this news about {symbol} stock. Be concise and focused on business impact:\n"
                    f"Title: {article['title']}\n"
                    f"Content: {article['description']}\n\n"
                    "Format response as JSON with these fields:\n"
                    "1. relevance_summary: A 1-2 sentence explanation of how this directly affects the company's business/stock\n"
                    "2. potential_impact: One of ['Positive', 'Negative', 'Neutral'] based on likely stock price effect\n"
                    "3. impact_reason: A brief explanation of why you chose this impact direction\n"
                    "4. confidence: A number 0-100 indicating analysis confidence\n\n"
                    "Example format:\n"
                    "{\n"
                    '  "relevance_summary": "Microsoft\'s cloud revenue grew 30% YoY, showing strong enterprise adoption and market share gains against AWS",\n'
                    '  "potential_impact": "Positive",\n'
                    '  "impact_reason": "Accelerating cloud growth signals expanding margins and recurring revenue",\n'
                    '  "confidence": 85\n'
                    "}\n\n"
                    "Focus on specific business metrics, competitive position, or market opportunities. Avoid generic statements."
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
        """Enhanced fallback simple analysis."""
        text = (title + ' ' + description).lower()

        # Define key business metrics and their associated terms
        metrics = {
            'revenue': ['revenue', 'sales', 'earnings', 'profit'],
            'market_share': ['market share', 'market position', 'market leader'],
            'product': ['launch', 'release', 'new product', 'innovation'],
            'competition': ['competitor', 'competition', 'market leader'],
            'costs': ['cost', 'expense', 'margin', 'efficiency']
        }

        # Find the most relevant business aspect
        found_metrics = []
        for metric, terms in metrics.items():
            if any(term in text for term in terms):
                found_metrics.append(metric)

        # Generate a specific summary based on found metrics
        if found_metrics:
            primary_metric = found_metrics[0]
            summary_templates = {
                'revenue': "News discusses company's financial performance and revenue trends",
                'market_share': "Article covers changes in company's market position and competitive standing",
                'product': "Updates on product developments and potential market reception",
                'competition': "News about competitive dynamics and market positioning",
                'costs': "Information about company's cost structure and operational efficiency"
            }
            relevance_summary = summary_templates.get(primary_metric, "General business update with potential stock impact")
        else:
            relevance_summary = "General market news that may affect trading sentiment"

        # Analyze sentiment for impact direction
        positive_terms = ['growth', 'increase', 'beat', 'exceed', 'gain', 'success', 'improve']
        negative_terms = ['decline', 'drop', 'miss', 'below', 'risk', 'concern', 'problem']

        positive_count = sum(1 for term in positive_terms if term in text)
        negative_count = sum(1 for term in negative_terms if term in text)

        if positive_count > negative_count:
            impact = "Positive"
            impact_reason = "News contains mostly positive business indicators"
        elif negative_count > positive_count:
            impact = "Negative"
            impact_reason = "News highlights potential business challenges"
        else:
            impact = "Neutral"
            impact_reason = "Mixed or unclear business implications"

        return {
            'relevance_summary': relevance_summary,
            'potential_impact': impact,
            'impact_reason': impact_reason,
            'confidence': 60
        }