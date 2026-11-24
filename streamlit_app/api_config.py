import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import httpx
import streamlit as st
from streamlit import config as st_config

DEFAULT_BACKEND_API_URL = "https://harvesta-xbni.onrender.com/api/v1"


def normalize_backend_api_url(url: str) -> str:
    url = url.strip()
    if not url:
        url = DEFAULT_BACKEND_API_URL
    if "://" not in url:
        url = f"https://{url}"

    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Backend API URL must be a valid HTTP(S) URL.")
    if parsed.query or parsed.fragment:
        raise ValueError("Backend API URL cannot include a query or fragment.")

    return urlunsplit(("https", parsed.netloc, parsed.path.rstrip("/"), "", ""))


def normalize_api_url(url: str) -> str:
    normalized_url = normalize_backend_api_url(url)
    if normalized_url.endswith("/api/v1"):
        return normalized_url
    return f"{normalized_url}/api/v1"


def get_api_url() -> str:
    backend_api_url = os.getenv("BACKEND_API_URL")
    if not backend_api_url:
        secret_files = st_config.get_option("secrets.files")
        if any(Path(path).exists() for path in secret_files):
            backend_api_url = st.secrets.get(
                "BACKEND_API_URL", DEFAULT_BACKEND_API_URL
            )
        else:
            backend_api_url = DEFAULT_BACKEND_API_URL

    return normalize_api_url(backend_api_url)


def sidebar_api_url() -> str:
    with st.sidebar.expander("Developer Settings"):
        backend_api_url = st.text_input(
            "Backend API URL",
            value=get_api_url(),
            key="developer_api_url",
        )
    return normalize_api_url(backend_api_url)


def api_post(url: str, **kwargs) -> httpx.Response:
    return httpx.post(
        normalize_backend_api_url(url),
        follow_redirects=True,
        **kwargs,
    )
