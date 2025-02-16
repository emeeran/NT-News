# News Aggregator

A Streamlit-based news aggregator that integrates multiple news APIs and offers an enhanced user experience.

## Features
- **API Integration:** Supports Currents, NewsAPI, GNews, and The Guardian.
- **Keyword & Topic Search:** Filter news by keyword and topic.
- **Provider Selection:** Choose an API provider from a dropdown.
- **Auto Refresh:** Enable auto-refresh to update news periodically.
- **Pagination:** View results in paginated sections for better readability.
- **Download News:** Export aggregated results as a JSON file.
- **Performance Optimizations:** Uses a global requests session and concurrent fetching for faster performance.
- **Environment Configuration:** Securely manage API keys using a `.env` file.

## Setup & Installation
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root with your API keys.
3. Run the application:
   ```
   streamlit run app.py
   ```

## License
MIT License
