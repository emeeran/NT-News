import os, json, requests, streamlit as st, concurrent.futures, threading, warnings, logging
from dotenv import load_dotenv
from typing import Dict, List, Any

# Configure logging and suppress specific warnings
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")
warnings.filterwarnings("ignore", message=".*Thread.*")
logging.getLogger("root").setLevel(logging.WARNING)
try:
    logging.getLogger("streamlit.runtime.scriptrunner.script_run_context").disabled = (
        True
    )
except Exception:
    pass

load_dotenv()

session = requests.Session()

try:
    from streamlit_autorefresh import st_autorefresh
except ModuleNotFoundError:

    def st_autorefresh(*args, **kwargs):
        return None


try:
    from streamlit.runtime.scriptrunner.script_run_context import (
        get_script_run_ctx,
        add_script_run_ctx,
    )
except ModuleNotFoundError:

    class DummyScriptRunCtx:
        pass

    def get_script_run_ctx():
        return DummyScriptRunCtx()

    def add_script_run_ctx(thread, ctx):
        pass


TIMEOUT = 10
PAGE_SIZE = 25

# Removed unused run_with_ctx


# Optimize make_request() to reuse session connections.
def make_request(url, params, error_msg="API error"):
    try:
        r = session.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ReadTimeout:
        st.error(f"{error_msg}: request timed out.")
    except requests.exceptions.HTTPError as err:
        st.error(f"{error_msg}: {err}")
    return {}


@st.cache_data(show_spinner=False)
def fetch_currents_news(query):
    api_key = os.getenv("CURRENTS_API_KEY")
    if not api_key:
        return []
    url = "https://api.currentsapi.services/v1/search"
    params = {"apiKey": api_key, "language": "en", "keywords": query}
    return make_request(url, params, "Currents API error").get("news", [])


@st.cache_data(show_spinner=False)
def fetch_newsapi_news(query):
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
def fetch_gnews_news(query):
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
def fetch_guardian_news(query):
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


@st.cache_data(show_spinner=False)
def fetch_global_top_news(query: str = "") -> List[Dict[str, Any]]:
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return []
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": api_key,
        "language": "en",
        "pageSize": PAGE_SIZE,
        "country": "us",
    }
    if query.strip():
        params["q"] = query
    articles = make_request(url, params, "Global Top News error").get("articles", [])
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


def fetch_all_news(query):
    fetchers = {
        "Currents News": fetch_currents_news,
        "NewsAPI Results": fetch_newsapi_news,
        "GNews Results": fetch_gnews_news,
        "The Guardian Results": fetch_guardian_news,
    }
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {name: executor.submit(fn, query) for name, fn in fetchers.items()}
        return {name: fut.result() for name, fut in futures.items()}


# New pagination in each news section
def display_news_section(title, news, page_size=PAGE_SIZE):
    key_page = f"{title}_page"
    if key_page not in st.session_state:
        st.session_state[key_page] = 1
    total = len(news)
    current_page = st.session_state[key_page]
    max_page = (total + page_size - 1) // page_size or 1
    start = (current_page - 1) * page_size
    end = start + page_size
    # Change expanded=False to expanded=True so results remain visible after pagination.
    with st.expander(title, expanded=True):
        if not news:
            st.info(f"No results found for {title}.")
        else:
            for art in news[start:end]:
                from datetime import datetime

                published_str = art.get("published", "Unknown Date")
                try:
                    dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%S%z")
                    simple_date = dt.strftime("%Y-%m-%d")
                except:
                    simple_date = published_str

                st.markdown(
                    f"""
                    <div style="width:100%; padding:10px; border:1px solid #ddd; border-radius:5px;">
                        <h3 style="margin-bottom:0.2em;">{art.get('title')}</h3>
                        <p style="font-size:0.9em; color:#555; margin:0.2em 0;">
                            {art.get('author', 'Unknown Source')} &bull; {simple_date}
                        </p>
                        <p style="margin:0.5em 0;">{art.get('description') or ''}</p>
                        <a style="text-decoration:none; font-weight:bold; color:#1a73e8;" href="{art.get('url')}" target="_blank">Read more</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            col_prev, col_page, col_next = st.columns(3)
            with col_prev:
                if st.button("Previous", key=f"{title}_prev") and current_page > 1:
                    st.session_state[key_page] -= 1
            with col_next:
                if st.button("Next", key=f"{title}_next") and current_page < max_page:
                    st.session_state[key_page] += 1
            with col_page:
                st.markdown(f"Page {current_page} of {max_page}")
        st.markdown("---")


# New function to display combined results with global pagination.
def display_combined_news(news, page_size=PAGE_SIZE):
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
                from datetime import datetime

                published_str = art.get("published", "Unknown Date")
                try:
                    dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%S%z")
                    simple_date = dt.strftime("%Y-%m-%d")
                except:
                    simple_date = published_str

                st.markdown(
                    f"""
                    <div style="width:100%; padding:10px; border:1px solid #ddd; border-radius:5px;">
                        <h3 style="margin-bottom:0.2em;">{art.get('title')}</h3>
                        <p style="font-size:0.9em; color:#555; margin:0.2em 0;">
                            {art.get('author', 'Unknown Source')} &bull; {simple_date}
                        </p>
                        <p style="margin:0.5em 0;">{art.get('description') or ''}</p>
                        <a style="text-decoration:none; font-weight:bold; color:#1a73e8;"
                           href="{art.get('url')}" target="_blank">
                           Read more
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
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


def main():
    st.set_page_config(page_title="NT News", layout="wide")
    st.markdown(
        """
        <style>
        .center-title {
            text-align: center;
            color: teal;
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="center-title">NT News</div>', unsafe_allow_html=True)

    # Initialize form default values
    if "form_values" not in st.session_state:
        st.session_state.form_values = {
            "kw": "",
            "topic": "All",
            "provider": "All",
            "auto_refresh": False,
            "refresh_interval": 10,
        }

    with st.sidebar.form("news_form"):
        kw = st.text_input("Keyword", value=st.session_state.form_values["kw"])
        topic = st.selectbox(
            "Topic",
            [
                "All",
                "Technology",
                "Artificial intelligence ",
                "Business",
                "Entertainment",
                "History",
                "Science",
            ],
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
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Search")
        with col2:
            clear = st.form_submit_button("Clear")
            if clear:
                # Reset form values
                st.session_state.form_values = {
                    "kw": "",
                    "topic": "All",
                    "provider": "All",
                    "auto_refresh": False,
                    "refresh_interval": 10,
                }
                # Restore global top news
                st.session_state["combined_news"] = fetch_global_top_news()
                st.rerun()
    if auto_refresh:
        st_autorefresh(interval=refresh_interval * 1000, limit=100, key="auto_refresh")
    if "combined_news" not in st.session_state:
        st.session_state["combined_news"] = fetch_global_top_news()
        if st.session_state["combined_news"]:
            st.subheader("Today's Top News")
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
                for articles in results.values():
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
            if not combined:
                if provider != "All" and not os.getenv(
                    f"{provider.upper().replace(' ', '_')}_API_KEY"
                ):
                    st.error(
                        f"Missing API key for {provider}. Please check your .env file."
                    )
                else:
                    st.warning(
                        f"No results found for '{query}' from {provider}. Try different keywords or another provider."
                    )
        st.session_state["combined_news"] = combined
        if combined:
            st.subheader(f"Results for: {query}")
    if "combined_news" in st.session_state:
        display_combined_news(st.session_state["combined_news"])


if __name__ == "__main__":
    main()
