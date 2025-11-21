from __future__ import annotations

from typing import Any

from src.lib import load_catalogue, load_post, mcp, score_post


@mcp.tool()
async def search_hyperact_articles(
    subject: str,
    limit: int = 5,
    include_content_snippet: bool = False,
) -> list[dict[str, Any]]:
    """
    Find Hyperact articles related to the given subject.

    Args:
        subject: The topic or keywords to search for.
        limit: Maximum number of results to return (default 5).
        include_content_snippet: If true, include a short snippet from the article body.
    """

    if not subject.strip():
        raise ValueError("Please provide a subject to search for.")

    catalogue = load_catalogue()
    scored_posts: list[tuple[float, str, dict[str, Any]]] = []

    for slug, meta in catalogue.items():
        scored_posts.append((score_post(subject, meta), slug, meta))

    scored_posts.sort(key=lambda item: item[0], reverse=True)
    results: list[dict[str, Any]] = []

    for score, slug, meta in scored_posts:
        if score <= 0:
            continue

        result: dict[str, Any] = {
            "score": round(score, 2),
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

        if include_content_snippet:
            post = load_post(slug)
            content = str(post.get("content", "")).strip()
            snippet = content[:280]
            result["contentSnippet"] = snippet + (
                "..." if len(content) > len(snippet) else ""
            )

        results.append(result)
        if len(results) >= limit:
            break

    if not results and scored_posts:
        for score, slug, meta in scored_posts[:limit]:
            results.append(
                {
                    "score": round(score, 2),
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

    return results
