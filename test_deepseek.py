import os
from news_analyzer import NewsAnalyzer

def test_deepseek():
    analyzer = NewsAnalyzer()
    test_article = {
        'title': 'Test Article',
        'description': 'This is a test article about market conditions.',
        'url': 'http://test.com',
        'publishedAt': '2025-01-26T12:00:00Z'
    }
    
    result = analyzer._analyze_article(test_article, 'TEST', 'Test Company')
    print("\nAnalysis Result:", result)
    return result is not None

if __name__ == "__main__":
    success = test_deepseek()
    print("\nTest result:", "Success" if success else "Failed")
