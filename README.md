# News Aggregator

A Streamlit-based news aggregator that integrates multiple news APIs and offers an enhanced user experience.

## Features
- **API Integration:** Supports Currents, NewsAPI, GNews, and The Guardian.
- **Keyword & Topic Search:** Filter news by keyword and topic.
- **Provider Selection:** Choose an API provider from a dropdown.
- **Auto Refresh:** Enable auto-refresh to update news periodically.
- **Pagination:** View results in paginated sections for better readability.
- **Download News:** Export aggregated results as a JSON file.
- **Performance Optimizations:** Uses a global requests session, concurrent fetching, and caching.
- **Enhanced Logging & Type Hints:** Improved error tracking via logging and static type annotations.
- **Centralized Configuration:** Manage constants and configuration in `config.py`.

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

## Enhancements & Testing
- **Logging:** Check logs for API call errors and performance metrics.
- **Type Safety:** Run static analysis with mypy.
- **Unit Testing:** Consider adding tests (e.g., using pytest) for API functions and helper methods.

## License
MIT License
