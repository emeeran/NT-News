import os
from dotenv import load_dotenv  # <-- new import
import requests

load_dotenv()  # <-- new line to load .env file


def fetch_news(api_key):
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {"apiKey": api_key}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def display_news(news_data):
    news = news_data.get("news", [])
    if not news:
        print("No news found.")
    for article in news:
        print("-" * 40)
        print("Title:", article.get("title"))
        print("Description:", article.get("description"))
        print("URL:", article.get("url"))
        print("-" * 40)


def main():
    # Retrieve API key from environment variable, no fallback
    api_key = os.getenv("CURRENTS_API_KEY")
    if not api_key:
        print(
            "Please set your Currents API key in the code or as an environment variable (CURRENTS_API_KEY)."
        )
        return

    try:
        news_data = fetch_news(api_key)
        display_news(news_data)
    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    main()
