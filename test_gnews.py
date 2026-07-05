from gnews import GNews
google_news = GNews(max_results=3, language='en')
news = google_news.get_news('big boss')
print("--- GNews Results ---")
for n in news:
    print("-", n['title'])
