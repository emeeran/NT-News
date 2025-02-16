import os, json, requests, streamlit as st, concurrent.futures, threading, logging
from dotenv import load_dotenv
from typing import Any, Dict, List
from config import TIMEOUT, PAGE_SIZE  # use centralized config
from requests.adapters import HTTPAdapter, Retry  # <-- new import

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global session with retry enabled
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Fallback for st_autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
except ModuleNotFoundError:

    def st_autorefresh(*args, **kwargs):
        return None


# Fallback for ScriptRunContext
try:
    from streamlit.runtime.scriptrunner.script_run_context import (
        get_script_run_ctx,
        add_script_run_ctx,
    )
except ModuleNotFoundError:

    def get_script_run_ctx() -> None:
        return None

    def add_script_run_ctx(thread: threading.Thread, ctx: Any) -> None:
        pass


def run_with_ctx(fn: Any, *args: Any, **kwargs: Any) -> Any:
    ctx = get_script_run_ctx()
    thread = threading.current_thread()
    add_script_run_ctx(thread, ctx)
    return fn(*args, **kwargs)


def make_request(
    url: str, params: Dict[str, str], error_msg: str = "API error"
) -> Dict[str, Any]:
    try:
        r = session.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ReadTimeout:
        st.error(f"{error_msg}: request timed out.")
        logger.error(f"{error_msg}: request timed out for URL: {url}")
    except requests.exceptions.HTTPError as err:
        st.error(f"{error_msg}: {err}")
        logger.error(f"{error_msg}: {err} for URL: {url}")
    return {}


@st.cache_data(show_spinner=False)
def fetch_currents_news(query: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("CURRENTS_API_KEY")
    if not api_key:
        return []
    url = "https://api.currentsapi.services/v1/search"
    params = {"apiKey": api_key, "language": "en", "keywords": query}
    return make_request(url, params, "Currents API error").get("news", [])


@st.cache_data(show_spinner=False)
def fetch_newsapi_news(query: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []
    url = "https://newsapi.org/v2/everything"
    params = {"apiKey": api_key, "q": query, "language": "en"}
    articles = make_request(url, params, "NewsAPI error").get("articles", [])
    return [
        {
            "title": a.get("title"),
            "author": a.get("source", {}).get("name", "Unknown Source"),
            "published": a.get("publishedAt", "Unknown Date"),
            "description": a.get("description", ""),
            "url": a.get("url"),
        }
        for a in articles
    ]


@st.cache_data(show_spinner=False)
def fetch_gnews_news(query: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        return []
    url = "https://gnews.io/api/v4/search"
    params = {"token": api_key, "q": query, "lang": "en", "max": 10}
    articles = make_request(url, params, "GNews API error").get("articles", [])
    return [
        {
            "title": a.get("title"),
            "author": a.get("source", "Unknown Source"),
            "published": a.get("publishedAt", "Unknown Date"),
            "description": a.get("description", ""),
            "url": a.get("url"),
        }
        for a in articles
    ]


@st.cache_data(show_spinner=False)
def fetch_guardian_news(query: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("GUARDIAN_API_KEY")
    if not api_key:
        return []
    url = "https://content.guardianapis.com/search"
    params = {"api-key": api_key, "q": query, "show-fields": "trailText"}
    results = (
        make_request(url, params, "The Guardian API error")
        .get("response", {})
        .get("results", [])
    )
    return [
        {
            "title": art.get("webTitle"),
            "author": "The Guardian",
            "published": art.get("webPublicationDate", "Unknown Date"),
            "description": art.get("fields", {}).get("trailText", ""),
            "url": art.get("webUrl"),
        }
        for art in results
    ]


def fetch_all_news(query: str) -> Dict[str, List[Dict[str, Any]]]:
    fetchers = {
        "Currents News": fetch_currents_news,
        "NewsAPI Results": fetch_newsapi_news,
        "GNews Results": fetch_gnews_news,
        "The Guardian Results": fetch_guardian_news,
    }
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            name: executor.submit(run_with_ctx, fn, query)
            for name, fn in fetchers.items()
        }
        return {
            name: fut.result() if fut.done() else [] for name, fut in futures.items()
        }


def format_article(art: Dict[str, Any]) -> str:
    return f"""
    <div style="width:100%; padding:10px; border:1px solid #ddd; border-radius:5px;">
        <h3 style="margin-bottom:0.2em;">{art.get('title')}</h3>
        <p style="font-size:0.9em; color:#555; margin:0.2em 0;">
            {art.get('author', 'Unknown Source')} &bull; {art.get('published', 'Unknown Date')}
        </p>
        <p style="margin:0.5em 0;">{art.get('description') or ''}</p>
        <a style="text-decoration:none; font-weight:bold; color:#1a73e8;" href="{art.get('url')}" target="_blank">Read more</a>
    </div>
    """


def display_combined_news(
    news: List[Dict[str, Any]], page_size: int = PAGE_SIZE
) -> None:
    key_page = "combined_page"
    if key_page not in st.session_state:
        st.session_state[key_page] = 1
    total = len(news)
    current_page = st.session_state[key_page]
    max_page = (total + page_size - 1) // page_size or 1
    start = (current_page - 1) * page_size
    end = start + page_size
    with st.expander("Combined Results", expanded=True):
        if not news:
            st.info("No combined news found.")
        else:
            for art in news[start:end]:
                st.markdown("---")
                st.markdown(format_article(art), unsafe_allow_html=True)
            col_prev, col_page, col_next = st.columns(3)
            with col_prev:
                if st.button("Previous", key=f"{key_page}_prev") and current_page > 1:
                    st.session_state[key_page] -= 1
            with col_next:
                if (
                    st.button("Next", key=f"{key_page}_next")
                    and current_page < max_page
                ):
                    st.session_state[key_page] += 1
            with col_page:
                st.markdown(f"Page {current_page} of {max_page}")
        st.markdown("---")


def main() -> None:
    st.set_page_config(page_title="NT News", layout="wide")
    st.markdown(
        """
        <style>
        .center-title { text-align: center; color: teal; font-size: 3em; font-weight: bold; margin-bottom: 0; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="center-title">NT News</div>', unsafe_allow_html=True)
    with st.sidebar.form("news_form"):
        kw = st.text_input("Keyword")
        topic = st.selectbox(
            "Topic",
            ["All", "Technology", "Business", "Entertainment", "History", "Science"],
        )
        provider = st.selectbox(
            "API Provider", ["All", "Currents", "NewsAPI", "GNews", "The Guardian"]
        )
        auto_refresh = st.checkbox("Enable Auto Refresh")
        refresh_interval = (
            st.number_input("Refresh interval (seconds)", min_value=5, value=10, step=1)
            if auto_refresh
            else 0
        )
        submit = st.form_submit_button("Search")
    if auto_refresh:
        st_autorefresh(interval=refresh_interval * 1000, limit=100, key="auto_refresh")

    query = f"{kw} {topic}" if topic != "All" else kw
    if not query.strip():
        if "combined_news" in st.session_state:
            display_combined_news(st.session_state["combined_news"])
        return

    if submit:
        with st.spinner("Fetching news..."):
            if provider == "All":
                results = fetch_all_news(query)
                combined = []
                for name, articles in results.items():
                    logger.info(f"{name} returned {len(articles)} articles.")
                    combined.extend(articles)
                combined = sorted(
                    combined, key=lambda a: a.get("published", ""), reverse=True
                )
            elif provider == "Currents":
                combined = fetch_currents_news(query)
            elif provider == "NewsAPI":
                combined = fetch_newsapi_news(query)
            elif provider == "GNews":
                combined = fetch_gnews_news(query)
            elif provider == "The Guardian":
                combined = fetch_guardian_news(query)
        # Debug: log total combined articles count
        logger.info(f"Total combined articles: {len(combined)}")
        if not combined:
            st.warning("No news articles returned. Check your query and API keys.")
        st.session_state["combined_news"] = combined
        st.subheader(f"Results for: {query}")
        st.download_button(
            "Download Results (JSON)",
            data=json.dumps(combined, indent=2),
            file_name="news_results.json",
            mime="application/json",
        )
    if "combined_news" in st.session_state:
        display_combined_news(st.session_state["combined_news"])


if __name__ == "__main__":
    main()
