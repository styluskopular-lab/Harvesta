import os
from pathlib import Path

import streamlit as st
from streamlit import config as st_config


def get_api_url() -> str:
    backend_api_url = os.getenv("BACKEND_API_URL")
    if not backend_api_url:
        secret_files = st_config.get_option("secrets.files")
        if any(Path(path).exists() for path in secret_files):
            backend_api_url = st.secrets.get(
                "BACKEND_API_URL", "http://localhost:8000"
            )
        else:
            backend_api_url = "http://localhost:8000"

    return f"{backend_api_url.rstrip('/')}/api/v1"
