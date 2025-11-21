from __future__ import annotations

from typing import Any

from src.lib import (
    ARTICLE_RESOURCE_DESCRIPTION,
    ARTICLE_RESOURCE_URI,
    ARTICLES_RESOURCE_DESCRIPTION,
    ARTICLES_RESOURCE_TEMPLATE_URI,
    ARTICLES_RESOURCE_URI,
    build_article_list,
    load_post,
    mcp,
)


@mcp.resource(
    ARTICLES_RESOURCE_URI,
    description=ARTICLES_RESOURCE_DESCRIPTION,
)
def list_hyperact_articles() -> list[dict[str, Any]]:
    """
    Resource: List available Hyperact articles with metadata.
    """

    return build_article_list()


@mcp.resource(
    ARTICLES_RESOURCE_TEMPLATE_URI,
    name="list_hyperact_articles",
    description=f"{ARTICLES_RESOURCE_DESCRIPTION} Set limit to trim results.",
)
def list_hyperact_articles_limited(limit: int) -> list[dict[str, Any]]:
    """
    Resource template: list Hyperact articles, allowing an explicit limit.
    """

    return build_article_list(limit)


@mcp.resource(
    ARTICLE_RESOURCE_URI,
    description=ARTICLE_RESOURCE_DESCRIPTION,
)
def get_hyperact_article(slug: str) -> dict[str, Any]:
    """
    Resource: Get a Hyperact article with slug.
    """

    return load_post(slug)
