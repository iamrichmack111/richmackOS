from __future__ import annotations

import os


DEFAULT_OLLAMA_HOST = "http://richmack.local:11434"


def ollama_host() -> str:
    """
    Return the global RichmackOS Ollama server.

    Priority:
      1. RICHMACK_OLLAMA_HOST
      2. OLLAMA_HOST
      3. RichmackOS default
    """

    value = (
        os.environ.get("RICHMACK_OLLAMA_HOST")
        or os.environ.get("OLLAMA_HOST")
        or DEFAULT_OLLAMA_HOST
    )

    value = value.strip().rstrip("/")

    if not value:
        return DEFAULT_OLLAMA_HOST

    if not value.startswith(
        (
            "http://",
            "https://",
        )
    ):
        value = (
            "http://"
            + value
        )

    return value.rstrip("/")


def ollama_endpoint(
    path: str,
) -> str:
    cleaned = (
        "/"
        + path.lstrip("/")
    )

    return (
        ollama_host()
        + cleaned
    )


def chat_url() -> str:
    return ollama_endpoint(
        "/api/chat"
    )


def generate_url() -> str:
    return ollama_endpoint(
        "/api/generate"
    )


def tags_url() -> str:
    return ollama_endpoint(
        "/api/tags"
    )


def embed_url() -> str:
    return ollama_endpoint(
        "/api/embed"
    )


def embeddings_url() -> str:
    return ollama_endpoint(
        "/api/embeddings"
    )
