import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

async def test_search():
    async with httpx.AsyncClient() as client:
        # Improved behavior with correct spelling
        res2 = await client.get("https://newsapi.org/v2/everything", params={
            "q": '"bigg boss"', "pageSize": 3, "language": "en", "sortBy": "relevancy", "apiKey": API_KEY
        })
        print("\n--- IMPROVED (q=\"bigg boss\", sortBy=relevancy) ---")
        for a in res2.json().get("articles", []):
            print("-", a.get("title"))

asyncio.run(test_search())
