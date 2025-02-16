import os
from datetime import datetime
import requests
import streamlit as st
import concurrent.futures
from dotenv import load_dotenv
from typing import Dict, List, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure once at startup
load_dotenv()
st.set_page_config(page_title="NT News", layout="wide")

# Global constants
TIMEOUT = 10
PAGE_SIZE = 25

# Configure session with connection pooling and retries
SESSION = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
SESSION.mount(
    "https://",
    HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=retry_strategy),
)

# Configure logging silently
import logging

logging.getLogger("root").setLevel(logging.WARNING)
for logger in ["streamlit", "urllib3"]:
    logging.getLogger(logger).setLevel(logging.WARNING)


@st.cache_data(show_spinner=False, ttl=300)
def make_request(url: str, params: Dict, error_msg: str = "API error") -> Dict:
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as err:
        st.error(f"{error_msg}: {err}")
        return {}


@st.cache_data(show_spinner=False, ttl=300)
def fetch_news(source: str, query: str = "") -> List[Dict]:
    api_key = os.getenv(f"{source.upper()}_API_KEY")
    if not api_key:
        return []

    sources = {
        "NEWS": {
            "url": (
                "https://newsapi.org/v2/top-headlines"
                if not query
                else "https://newsapi.org/v2/everything"
            ),
            "params": {
                "apiKey": api_key,
                "language": "en",
                "pageSize": PAGE_SIZE,
                **({"q": query} if query else {"country": "us"}),
            },
            "results_key": "articles",
        },
        "GUARDIAN": {
            "url": "https://content.guardianapis.com/search",
            "params": {
                "api-key": api_key,
                "q": query or "*",
                "show-fields": "trailText",
            },
            "results_key": "response.results",
        },
    }

    if source not in sources:
        return []

    config = sources[source]
    data = make_request(config["url"], config["params"])

    for key in config["results_key"].split("."):
        data = data.get(key, [])

    return normalize_articles(data, source)


@st.cache_data(show_spinner=False, ttl=300)
def normalize_articles(articles: List[Dict], source: str) -> List[Dict]:
    normalized = []
    for art in articles:
        try:
            if source == "NEWS":
                content = {
                    "title": art.get("title", ""),
                    "author": art.get("source", {}).get("name", source),
                    "published": art.get("publishedAt", "Unknown Date"),
                    "description": art.get("description", ""),
                    "url": art.get("url", ""),
                }
            elif source == "GUARDIAN":
                content = {
                    "title": art.get("webTitle", ""),
                    "author": "The Guardian",
                    "published": art.get("webPublicationDate", "Unknown Date"),
                    "description": art.get("fields", {}).get("trailText", ""),
                    "url": art.get("webUrl", ""),
                }
            else:
                continue

            dt = datetime.strptime(content["published"], "%Y-%m-%dT%H:%M:%S%z")
            content["published"] = dt.strftime("%Y-%m-%d")
            normalized.append(content)
        except:
            continue

    return normalized


def display_articles(articles: List[Dict]) -> None:
    for art in articles:
        st.markdown(
            f"""
            <div style="width:100%; padding:15px; border:1px solid #ddd; border-radius:5px; margin:10px 0;">
                <h3 style="margin-bottom:0.2em;">{art['title']}</h3>
                <p style="font-size:0.9em; color:#555; margin:0.2em 0;">
                    {art['author']} • {art['published']}
                </p>
                <p style="margin:0.5em 0;">{art['description']}</p>
                <a style="text-decoration:none; font-weight:bold; color:#1a73e8;"
                   href="{art['url']}" target="_blank">Read more</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    # Initialize session state
    if "form_submitted" not in st.session_state:
        st.session_state["form_submitted"] = False
        st.session_state["keyword"] = ""
        st.session_state["articles"] = None

    st.markdown(
        '<h1 style="text-align:center;color:teal">NT News</h1>', unsafe_allow_html=True
    )

    with st.sidebar.form("search", clear_on_submit=True):  # Add clear_on_submit
        kw = st.text_input(
            "Keyword",
            value=(
                ""
                if st.session_state.get("form_submitted", False)
                else st.session_state.get("keyword", "")
            ),
            key=f"kw_{st.session_state.get('form_submitted', False)}",  # Dynamic key
        )

        topic = st.selectbox(
            "Topic",
            [
                "All",
                "Technology",
                "Artificial intelligence",
                "Business",
                "Entertainment",
                "Science",
            ],
            index=0,
        )
        provider = st.selectbox("Provider", ["All", "News", "Guardian"], index=0)

        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Search")
        with col2:
            clear = st.form_submit_button("Clear")

    if clear:
        st.session_state["form_submitted"] = True
        st.session_state["keyword"] = ""
        st.session_state["articles"] = fetch_news("NEWS")
        st.rerun()

    if submitted:
        st.session_state["form_submitted"] = False
        st.session_state["keyword"] = kw

    query = f"{kw} {topic}" if topic != "All" else kw

    if submitted and query:
        with st.spinner("Fetching news..."):
            if provider == "All":
                results = []
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {
                        executor.submit(fetch_news, src, query.strip()): src
                        for src in ["NEWS", "GUARDIAN"]
                    }
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            results.extend(future.result())
                        except Exception:
                            continue
            else:
                results = fetch_news(provider.upper(), query.strip())

            if results:
                st.session_state["articles"] = sorted(
                    results, key=lambda x: x["published"], reverse=True
                )
                st.session_state["kw"] = kw
            else:
                st.warning(
                    "No results found. Try different keywords or another provider."
                )

    # Use consistent dictionary-style access
    articles = st.session_state["articles"] or fetch_news("NEWS")
    if articles:
        st.subheader("Today's Top News" if not query else f"Results for: {query}")
        display_articles(articles)


if __name__ == "__main__":
    main()
