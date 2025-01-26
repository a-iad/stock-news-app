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

    def _call_deepseek_api(self, prompt: str) -> Dict[str, Any]:
        """Make an API call to DeepSeek with detailed logging."""
        try:
            print("\nCalling DeepSeek API...")
            if not self.deepseek_api_key:
                print("ERROR: DEEPSEEK_API_KEY not found")
                return None

            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }

            response = requests.post(
                self.deepseek_url,
                headers=headers,
                json=data,
                timeout=30
            )

            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and result['choices']:
                    return json.loads(result['choices'][0]['message']['content'])

            print(f"API Error: {response.text}")
            return None

        except Exception as e:
            print(f"DeepSeek API error: {str(e)}")
            traceback.print_exc()
            return None

    def _analyze_article(self, article: Dict[str, Any], symbol: str, company_name: str) -> Dict[str, Any]:
        """Analyze article using DeepSeek AI focusing on stock impact."""
        if not article.get('title') or not article.get('description'):
            return None

        try:
            if self.deepseek_api_key:
                prompt = (
                    f"Analyze this news about {symbol} ({company_name if company_name else 'unknown company'}):\n\n"
                    f"TITLE: {article['title']}\n"
                    f"CONTENT: {article['description']}\n\n"
                    "Provide two things:\n"
                    "1. A clear, factual summary of the key points and numbers\n"
                    "2. A detailed paragraph analyzing how this could affect the stock price, including:\n"
                    "   - Specific business metrics impacted\n"
                    "   - Comparison to market expectations\n"
                    "   - Competitive implications\n"
                    "   - Timeline for impact\n\n"
                    "Format response as JSON:\n"
                    "{\n"
                    '  "article_summary": "Factual summary with key points and numbers",\n'
                    '  "significance": "Detailed analysis of stock price impact",\n'
                    '  "market_impact": "Very Positive|Somewhat Positive|Ambivalent|Somewhat Negative|Very Negative",\n'
                    '  "impact_explanation": "Brief justification of market impact rating"\n'
                    "}"
                )

                analysis = self._call_deepseek_api(prompt)
                if analysis:
                    return analysis

            print("Falling back to simple analysis")
            return self._simple_analysis(article['title'], article['description'])

        except Exception as e:
            print(f"Error analyzing article: {str(e)}")
            return self._simple_analysis(article['title'], article['description'])

    def _simple_analysis(self, title: str, description: str) -> Dict[str, Any]:
        """Enhanced fallback simple analysis."""
        try:
            # Extract key information
            combined_text = f"{title}. {description}"

            # Generate a basic summary (first sentence of title + key details from description)
            summary_sentences = []
            if title:
                summary_sentences.append(title.split('.')[0])
            if description:
                desc_sentences = description.split('.')
                if len(desc_sentences) > 1:
                    summary_sentences.append(desc_sentences[1].strip())

            article_summary = '. '.join(summary_sentences)

            # Analyze impact based on key phrases
            impact_phrases = {
                'Very Positive': ['surge', 'breakthrough', 'exceeds expectations', 'record high'],
                'Somewhat Positive': ['increase', 'growth', 'improvement', 'gains'],
                'Somewhat Negative': ['decline', 'below expectations', 'challenges'],
                'Very Negative': ['plunge', 'crisis', 'major setback', 'significant loss']
            }

            # Determine impact level
            impact_scores = {level: 0 for level in impact_phrases.keys()}
            text_lower = combined_text.lower()

            for level, phrases in impact_phrases.items():
                for phrase in phrases:
                    if phrase.lower() in text_lower:
                        impact_scores[level] += 1

            # Select impact level
            if max(impact_scores.values()) == 0:
                market_impact = "Ambivalent"
                impact_explanation = "News has mixed or unclear implications for the company's performance"
            else:
                market_impact = max(impact_scores.items(), key=lambda x: x[1])[0]
                impact_explanation = f"Multiple indicators suggest {market_impact.lower()} impact on company value"

            # Generate significance explanation
            significance = f"This news potentially affects the company's market position and business operations. {impact_explanation}."

            return {
                'article_summary': article_summary,
                'significance': significance,
                'market_impact': market_impact,
                'impact_explanation': impact_explanation
            }

        except Exception as e:
            print(f"Error in simple analysis: {str(e)}")
            return {
                'article_summary': title,
                'significance': "Unable to analyze specific impact",
                'market_impact': "Ambivalent",
                'impact_explanation': "Insufficient information for detailed analysis"
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

            # Fetch news articles
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

            # Process individual articles
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

            result = {
                'articles': processed_articles
            }

            print(f"Returning {len(processed_articles)} processed articles")
            return result

        except Exception as e:
            print(f"Error in fetch_relevant_news: {str(e)}")
            traceback.print_exc()
            return {'articles': []}