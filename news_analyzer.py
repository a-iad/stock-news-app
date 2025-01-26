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

    def _analyze_article(self, article: Dict[str, Any], symbol: str, company_name: str) -> Dict[str, Any]:
        """Analyze individual article for relevance and impact."""
        if not article.get('title') or not article.get('description'):
            return None

        try:
            if self.deepseek_api_key:
                prompt = (
                    f"As an expert financial analyst, provide a comprehensive analysis of this news about {symbol} ({company_name if company_name else 'unknown company'}):\n"
                    f"Title: {article['title']}\n"
                    f"Content: {article['description']}\n\n"
                    "Provide a detailed analysis in JSON format with these components:\n\n"
                    "1. article_summary: A detailed yet concise summary focusing on key business implications and market impact. "
                    "Highlight specific numbers, business metrics, or strategic changes mentioned. "
                    "3-4 sentences maximum.\n\n"
                    "2. significance: A thorough analysis (4-6 sentences) that explains:\n"
                    "   - Direct business impact on revenue, margins, or market share\n"
                    "   - Strategic implications for competitive position\n"
                    "   - Effect on growth trajectory or business model\n"
                    "   - Connection to broader market trends or industry shifts\n"
                    "   - Long-term implications for the company's strategic position\n"
                    "Include specific metrics, competitor comparisons, and market context where relevant.\n\n"
                    "3. market_impact: One of these values based on comprehensive analysis:\n"
                    "   - 'Very Positive': Strong upward pressure with clear long-term benefits\n"
                    "   - 'Somewhat Positive': Moderate upward influence with some uncertainties\n"
                    "   - 'Ambivalent': Mixed implications or unclear long-term impact\n"
                    "   - 'Somewhat Negative': Moderate concerns with potential mitigating factors\n"
                    "   - 'Very Negative': Significant challenges with lasting implications\n\n"
                    "4. impact_explanation: A detailed explanation connecting the news to likely stock movement, including:\n"
                    "   - Effect on key business metrics\n"
                    "   - Comparison to market expectations\n"
                    "   - Potential investor reaction\n"
                    "   - Timeline for impact\n\n"
                    "Example format:\n"
                    "{\n"
                    '  "article_summary": "Microsoft reported exceptional Q4 cloud revenue growth of 30% YoY to $25B, significantly outpacing market expectations of 25%. Azure gained 3% market share against AWS while expanding operating margins by 200bps through improved infrastructure efficiency. The company also announced three major enterprise client wins from AWS.",\n'
                    '  "significance": "This acceleration in cloud growth is particularly significant as it reverses three quarters of gradual slowdown and demonstrates Microsoft\'s ability to win major enterprise contracts from AWS. The simultaneous margin expansion, despite aggressive pricing, indicates their infrastructure investments are paying off through improved efficiency. The 3% market share gain represents approximately $4B in annual recurring revenue, strengthening their position as a strong challenger to AWS. Looking ahead, this could signal a shift in enterprise cloud preferences, especially given Microsoft\'s stronger position in AI and enterprise software integration.",\n'
                    '  "market_impact": "Very Positive",\n'
                    '  "impact_explanation": "The combination of accelerating growth, margin expansion, and market share gains challenges the bear thesis that cloud growth was structurally slowing. The 200bps margin improvement suggests sustainable profit acceleration, while enterprise wins indicate strong competitive positioning. Expect positive estimate revisions and potential multiple expansion as the market prices in faster growth."\n'
                    "}\n\n"
                    "Focus on specific business implications, quantitative metrics, and clear cause-effect relationships. Avoid general statements and provide concrete, actionable insights."
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

            # Fallback to simple analysis
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