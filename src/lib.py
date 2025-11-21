from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import quote

from fastmcp import Context, FastMCP
from src.fetch_json import fetch_json

BASE_URL = os.getenv("HYPERACT_API_BASE_URL", "https://hyperact.co.uk/api/mcp")
POSTS_ENDPOINT = f"{BASE_URL}/posts"
POST_ENDPOINT_TEMPLATE = f"{BASE_URL}/post/{{slug}}"
ARTICLES_RESOURCE_URI = "hyperact://articles"
ARTICLES_RESOURCE_TEMPLATE_URI = "hyperact://articles/{limit}"
ARTICLES_RESOURCE_DESCRIPTION = "List available Hyperact articles with metadata."
ARTICLE_RESOURCE_URI = "hyperact://article/{slug}"
ARTICLE_RESOURCE_DESCRIPTION = "Get a Hyperact article."

mcp = FastMCP(
    "hyperact-mcp",
    instructions=(
        "Find relevant Hyperact articles for a given subject. "
        "Use the hyperact://articles resource to browse metadata and the "
        "search_hyperact_articles tool to retrieve matches."
    ),
)


def load_catalogue() -> dict[str, Any]:
    return fetch_json(POSTS_ENDPOINT)


def load_post(slug: str) -> dict[str, Any]:
    safe_slug = quote(slug)
    return fetch_json(POST_ENDPOINT_TEMPLATE.format(slug=safe_slug))


def score_post(subject: str, post: dict[str, Any]) -> float:
    subject = subject.strip()
    if not subject:
        return 0

    subject_lower = subject.lower()
    tokens = [token for token in re.findall(r"[a-z0-9']+", subject_lower) if token]
    title = str(post.get("title", "")).lower()
    summary = str(post.get("summary", "")).lower()
    tags = " ".join(post.get("tags", [])).lower()
    combined = " ".join((title, summary, tags))

    score = 0.0
    if subject_lower in combined:
        score += 5.0

    for token in tokens:
        token_score = 0.0
        if token in title:
            token_score += 2.5
        if token in summary:
            token_score += 1.5
        if token in tags:
            token_score += 3.0
        if token_score == 0 and token in combined:
            token_score += 0.5
        score += token_score

    return score


def build_article_list(limit: int | None = None) -> list[dict[str, Any]]:
    catalogue = load_catalogue()
    posts = []
    for slug, meta in catalogue.items():
        posts.append(
            {
                "slug": slug,
                "title": meta.get("title"),
                "summary": meta.get("summary"),
                "tags": meta.get("tags", []),
                "readingTime": meta.get("readingTime"),
                "author": meta.get("author"),
                "date": meta.get("date"),
                "path": meta.get("path"),
                "image": meta.get("image"),
                "bgColor": meta.get("bgColor"),
            }
        )

    posts.sort(key=lambda post: post.get("date") or 0, reverse=True)
    if limit is None or limit <= 0:
        return posts
    return posts[:limit]


async def read_resource_json(uri: str, ctx: Context) -> Any:
    """Read a registered resource and parse JSON content."""
    raw = await ctx.read_resource(uri)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        return json.loads(raw)
    # Some resource implementations may already return structured objects
    return raw


async def load_catalogue_from_resource(
    ctx: Context, limit: int | None = None
) -> list[dict[str, Any]]:
    uri = (
        ARTICLES_RESOURCE_URI
        if limit is None
        else ARTICLES_RESOURCE_TEMPLATE_URI.format(limit=limit)
    )
    data = await read_resource_json(uri, ctx)
    if not isinstance(data, list):
        raise TypeError("Article catalogue resource returned unexpected data.")
    return data


async def load_post_from_resource(slug: str, ctx: Context) -> dict[str, Any]:
    uri = ARTICLE_RESOURCE_URI.format(slug=quote(slug))
    data = await read_resource_json(uri, ctx)
    if not isinstance(data, dict):
        raise TypeError("Article resource returned unexpected data.")
    return data
