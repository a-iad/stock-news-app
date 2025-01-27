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
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"

        if not self.news_api_key:
            print("WARNING: NEWS_API_KEY not found in environment")
        if not self.deepseek_api_key:
            print("WARNING: DEEPSEEK_API_KEY not found in environment")

    def _call_deepseek_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to DeepSeek."""
        try:
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

            response = requests.post(
                self.deepseek_url,
                headers=headers,
                json=payload,
                timeout=60  # Increased timeout
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                return analysis
            else:
                print(f"DeepSeek API error: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print("DeepSeek API timeout - trying with a shorter prompt")
            # Retry with shorter prompt
            short_prompt = prompt[:500] + "...\nProvide brief analysis."
            try:
                response = requests.post(
                    self.deepseek_url,
                    headers=headers,
                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": short_prompt}]},
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
            except:
                pass
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
            prompt = (
                f"Analyze this news article about {symbol} ({company_name if company_name else 'company'}):\n"
                f"Title: {article['title']}\n"
                f"Content: {article['description']}\n\n"
                "Provide a concise analysis:\n"
                "1. Key points and impact on company\n"
                "2. Potential effect on stock price\n"
                "3. Market significance"
            )

            analysis = self._call_deepseek_api(prompt)

            if analysis:
                return {
                    'article_summary': article['title'],
                    'significance': analysis,
                    'market_impact': self._determine_market_impact(analysis),
                    'impact_explanation': analysis
                }

            return {
                'article_summary': article['title'],
                'significance': "Technical difficulties in analyzing article",
                'market_impact': "Neutral",
                'impact_explanation': "Unable to analyze at this time"
            }

        except Exception as e:
            print(f"Article analysis failed: {str(e)}")
            return {
                'article_summary': article['title'],
                'significance': "Error in article analysis",
                'market_impact': "Neutral",
                'impact_explanation': "Analysis error occurred"
            }

    def _determine_market_impact(self, analysis: str) -> str:
        """Determine market impact from analysis text."""
        analysis_lower = analysis.lower()
        if 'highly positive' in analysis_lower or 'strong positive' in analysis_lower:
            return 'Very Positive'
        elif 'positive' in analysis_lower or 'increase' in analysis_lower:
            return 'Somewhat Positive'
        elif 'highly negative' in analysis_lower or 'strong negative' in analysis_lower:
            return 'Very Negative'
        elif 'negative' in analysis_lower or 'decrease' in analysis_lower:
            return 'Somewhat Negative'
        return 'Neutral'

    def fetch_relevant_news(self, symbol: str, company_name: str = None) -> Dict[str, Any]:
        """Fetch and analyze news for a stock."""
        try:
            print(f"\nFetching news for {symbol}")

            if not self.news_api_key:
                return {'articles': []}

            # Prepare search query
            query = f"({symbol} OR {company_name}) AND (stock OR market OR trading OR earnings)"

            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 5,
                'from': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            }

            response = requests.get(self.news_api_url, params=params, timeout=30)
            if response.status_code != 200:
                print(f"News API error: {response.status_code}")
                return {'articles': []}

            articles = response.json().get('articles', [])
            if not articles:
                return {'articles': []}

            processed_articles = []
            for article in articles[:3]:  # Process top 3 articles
                analysis = self._analyze_article(article, symbol, company_name)
                if analysis:
                    processed_articles.append({
                        'title': article['title'],
                        'url': article['url'],
                        'published_at': article['publishedAt'],
                        'analysis': analysis
                    })

            return {'articles': processed_articles}

        except Exception as e:
            print(f"Error in fetch_relevant_news: {str(e)}")
            traceback.print_exc()
            return {'articles': []}