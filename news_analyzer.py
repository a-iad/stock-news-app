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
        """Deep analysis of individual articles using DeepSeek AI."""
        if not article.get('title') or not article.get('description'):
            return None

        try:
            if self.deepseek_api_key:
                prompt = (
                    f"You are a senior Wall Street analyst producing a detailed research note about this news regarding {symbol} ({company_name if company_name else 'unknown company'}).\n\n"
                    f"NEWS ARTICLE:\nHeadline: {article['title']}\nContent: {article['description']}\n\n"
                    "Provide an institutional-quality analysis in JSON format with these components:\n\n"
                    "1. article_summary: A concise yet information-rich summary that captures:\n"
                    "   - The core news/announcement\n"
                    "   - Key metrics and numbers mentioned\n"
                    "   - Any comparative data points\n"
                    "   - Market reaction if mentioned\n"
                    "Max 3-4 sentences, but pack them with specific details.\n\n"
                    "2. deep_analysis: A thorough examination (minimum 4 paragraphs) that covers:\n"
                    "   - Immediate Business Impact: How does this affect revenue, margins, market share, or competitive position?\n" 
                    "   - Strategic Implications: What does this reveal about the company's strategy, execution, or market position?\n"
                    "   - Competitive Analysis: How does this change their standing vs competitors? What advantages/disadvantages emerge?\n"
                    "   - Market Context: How does this fit into broader industry trends or market dynamics?\n"
                    "   - Forward-Looking View: What are the longer-term implications? What should investors watch for next?\n"
                    "Be specific, use numbers where possible, and make meaningful connections.\n\n"
                    "3. market_impact: One of:\n"
                    "   - Very Positive: Strong positive reassessment of business outlook likely\n"
                    "   - Somewhat Positive: Incrementally positive but questions remain\n"
                    "   - Ambivalent: Mixed implications or unclear impact\n"
                    "   - Somewhat Negative: Concerning implications but not catastrophic\n"
                    "   - Very Negative: Significant negative reassessment warranted\n\n"
                    "4. trading_thesis: A specific explanation of:\n"
                    "   - Why the chosen market impact rating is justified\n"
                    "   - What metrics or developments could change this view\n"
                    "   - Key risks to this interpretation\n"
                    "   - Timeline for when impact should become visible in results\n\n"
                    "Example high-quality response:\n"
                    "{\n"
                    '  "article_summary": "Apple reported Q4 iPhone revenue of $69.7B (+15% YoY), with particularly strong growth in China (+22% YoY) and India (+40% YoY). ASPs increased 7% to $931 driven by Pro model mix, while margins expanded 180bps to 42.1%. Management guided to double-digit growth continuing in Q1 on strong demand and easing supply constraints.",\n'
                    '  "deep_analysis": "This quarter marks a decisive shift in Apple\'s growth trajectory and competitive positioning. The 15% iPhone revenue growth significantly outpaced expectations of 8-10%, with the mix shift toward Pro models (estimated 65% of units vs 58% last year) demonstrating Apple\'s pricing power and brand strength even in a challenging consumer environment.\n\nThe China performance is particularly noteworthy given macro concerns and Huawei\'s resurgence. The 22% growth suggests Apple\'s premium positioning and ecosystem strategy are resonating strongly, with management noting customer satisfaction scores reaching new highs. The 40% India growth, while off a smaller base, validates Apple\'s investment in local manufacturing and retail presence.\n\nMargin expansion of 180bps to 42.1% reflects both the favorable mix and improving supply chain efficiency. This level of profitability is unprecedented in consumer hardware and creates substantial resources for R&D investment in emerging areas like AR/VR and AI, where Apple\'s vertical integration could provide significant advantages.\n\nLooking forward, the strong Q1 guide suggests the 15 Pro/Pro Max supply constraints are easing while demand remains robust. The increasing Pro mix and growing services attachment rate (now 71% of active devices) points to sustained margin strength. Watch for expanding India manufacturing capacity and potential AI-driven features in iOS 18 as additional growth drivers.",\n'
                    '  "market_impact": "Very Positive",\n'
                    '  "trading_thesis": "The combination of accelerating growth, expanding margins, and strong emerging market performance justifies a positive re-rating of Apple\'s multiple. The Pro model mix shift suggests pricing power remains strong despite macro concerns, while India momentum adds a new growth vector. Key metrics to watch include Pro model lead times, China market share data, and iOS 18 features/adoption. Primary risk is high bar set for iPhone 16 cycle. Impact should be visible in sustained ASP growth starting next quarter, with full benefits to margin profile evident by mid-2024."\n'
                    "}\n\n"
                    "Your analysis should match this level of depth and specificity. Focus on connecting dots between news, business impact, and stock implications. Avoid generic statements - provide concrete insights an investor could act on."
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
                    timeout=30
                )

                if response.status_code == 200:
                    # Rename fields to match frontend expectations
                    analysis = json.loads(response.json()['choices'][0]['message']['content'])
                    return {
                        'article_summary': analysis['article_summary'],
                        'significance': analysis['deep_analysis'],
                        'market_impact': analysis['market_impact'],
                        'impact_explanation': analysis['trading_thesis']
                    }

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