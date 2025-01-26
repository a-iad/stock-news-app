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
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"  # Fixed URL
        print("NewsAnalyzer initialized")
        if not self.news_api_key:
            print("WARNING: NEWS_API_KEY not found in environment")
        if not self.deepseek_api_key:
            print("WARNING: DEEPSEEK_API_KEY not found in environment")

    def _call_deepseek_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to DeepSeek."""
        try:
            print(f"\nSending to DeepSeek API: {prompt[:100]}...")
            print("Checking API key:", "Available" if self.deepseek_api_key else "Missing")

            if not self.deepseek_api_key:
                print("ERROR: No DeepSeek API key found")
                return None

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [{
                    "role": "user",
                    "content": prompt
                }],
                "max_tokens": 600,
                "temperature": 0.7
            }

            print("Request URL:", self.deepseek_url)
            print("Request payload:", json.dumps(payload))

            response = requests.post(
                self.deepseek_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            print(f"DeepSeek response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("Successfully parsed response JSON")
                return result['choices'][0]['message']['content']
            else:
                print(f"DeepSeek API error: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"DeepSeek API connection error: {str(e)}")
            return None
        except Exception as e:
            print(f"DeepSeek API error: {str(e)}")
            traceback.print_exc()
            return None

    def _analyze_article(self, article: Dict[str, Any], symbol: str, company_name: str) -> Dict[str, Any]:
        """Analyze article content using DeepSeek."""
        if not article.get('title') or not article.get('description'):
            return None

        try:
            if self.deepseek_api_key:
                prompt = (
                    f"Article: {article['title']}\n{article['description']}\n\n"
                    "Analyze this article and provide:\n"
                    "1. A detailed explanation of its potential market impact\n"
                    "2. Key business metrics and market expectations affected\n"
                    "3. Specific implications for stock performance\n\n"
                    "Provide a thorough analysis with clear reasoning."
                )

                analysis = self._call_deepseek_api(prompt)
                if analysis:
                    return {
                        'article_summary': article['title'],
                        'significance': analysis,
                        'market_impact': 'Very Positive' if 'exceed' in analysis.lower() or 'growth' in analysis.lower()
                                  else 'Somewhat Positive' if 'increase' in analysis.lower() or 'improvement' in analysis.lower()
                                  else 'Very Negative' if 'miss' in analysis.lower() or 'decline' in analysis.lower()
                                  else 'Somewhat Negative' if 'below' in analysis.lower() or 'risk' in analysis.lower()
                                  else 'Ambivalent',
                        'impact_explanation': analysis
                    }

            return {
                'article_summary': article['title'],
                'significance': "Article analysis currently unavailable",
                'market_impact': "Ambivalent",
                'impact_explanation': "Unable to analyze specific impact"
            }

        except Exception as e:
            print(f"Article analysis failed: {str(e)}")
            return {
                'article_summary': article['title'],
                'significance': "Error in article analysis",
                'market_impact': "Ambivalent",
                'impact_explanation': "Analysis error occurred"
            }

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

            response = requests.get(self.news_api_url, params=params)
            if response.status_code != 200:
                print(f"News API error: Status {response.status_code}")
                print(f"Response: {response.text}")
                return {'articles': []}

            articles = response.json().get('articles', [])
            if not articles:
                print("No articles found")
                return {'articles': []}

            print(f"Found {len(articles)} articles")
            processed_articles = []

            for i, article in enumerate(articles[:4]):
                try:
                    article_analysis = self._analyze_article(article, symbol, company_name)
                    if article_analysis:
                        processed_articles.append({
                            'title': article['title'],
                            'article_summary': article_analysis.get('article_summary', ''),
                            'url': article['url'],
                            'published_at': article['publishedAt'],
                            'analysis': article_analysis
                        })
                        print(f"Processed article {i+1}")
                except Exception as e:
                    print(f"Error processing article {i+1}: {str(e)}")
                    continue

            return {'articles': processed_articles}

        except Exception as e:
            print(f"Error in fetch_relevant_news: {str(e)}")
            traceback.print_exc()
            return {'articles': []}