from duckduckgo_search import DDGS
import json

def search():
    with DDGS() as ddgs:
        results = [r for r in ddgs.news("Bigg Boss TV show", max_results=3)]
        print(json.dumps(results, indent=2))

search()
