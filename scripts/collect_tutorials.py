#!/usr/bin/env python3
"""
tutorials_collector.py
每天自动采集 AI 相关教程内容：
1. GitHub Trending（Python/Go/JavaScript AI 项目）
2. 目标工具官方文档/Blog
3. Hacker News / Reddit 热帖
4. YouTube 教程字幕（可选）
5. 生成/更新 tutorials/_data.json
6. 生成新 HTML 教程页面
"""

from __future__ import annotations
import json
import re
import os
import sys
import time
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ─── Config ────────────────────────────────────────────────────────────────

SITE_ROOT = Path(__file__).parent.parent.resolve()
POSTS_DIR = SITE_ROOT / "tutorials" / "_posts"
DATA_FILE = SITE_ROOT / "tutorials" / "_data.json"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

AI_KEYWORDS = [
    "llm", "ai", "gpt", "claude", "openai", "local-llm", "rag",
    "agent", "ollama", "openwebui", "vllm", "langchain", "litellm",
    "anthropic", "openrouter", "mistral", "qwen", "deepseek",
    "agentic", "copilot", "code assistant", "embedding",
]

CURATED_TOOLS = [
    {
        "name": "OpenWebUI",
        "repo": "open-webui/open-webui",
        "docs_url": "https://docs.openwebui.com",
        "tutorial_focus": ["部署", "配置", "集成", "Docker"],
        "icon": "🐳",
        "tags": ["OpenWebUI", "Docker", "Ollama"],
    },
    {
        "name": "Ollama",
        "repo": "ollama/ollama",
        "docs_url": "https://github.com/ollama/ollama",
        "tutorial_focus": ["GPU", "部署", "API", "模型管理"],
        "icon": "🖥️",
        "tags": ["Ollama", "GPU", "API"],
    },
    {
        "name": "OpenHands",
        "repo": "All-Hands-AI/OpenHands",
        "docs_url": "https://openhands.github.io",
        "tutorial_focus": ["部署", "Agent开发", "工具注册"],
        "icon": "🤖",
        "tags": ["OpenHands", "AI Agent", "Docker"],
    },
    {
        "name": "LiteLLM",
        "repo": "BerriAI/litellm",
        "docs_url": "https://docs.litellm.ai",
        "tutorial_focus": ["API", "代理", "成本控制"],
        "icon": "💡",
        "tags": ["LiteLLM", "API", "代理"],
    },
    {
        "name": "vLLM",
        "repo": "vllm-project/vllm",
        "docs_url": "https://docs.vllm.ai",
        "tutorial_focus": ["部署", "GPU", "推理加速"],
        "icon": "🚀",
        "tags": ["vLLM", "GPU", "推理"],
    },
    {
        "name": "Hermes Agent",
        "repo": "hermes-agent/hermes-agent",
        "docs_url": "https://github.com/hermes-agent/hermes-agent",
        "tutorial_focus": ["配置", "使用教程", "插件开发", "Telegram"],
        "icon": "⚡",
        "tags": ["Hermes", "Agent", "Telegram", "Cron"],
    },
]

# ─── HTTP Helper ──────────────────────────────────────────────────────────

def fetch(url: str, headers: Optional[dict] = None, timeout: int = 15) -> Optional[str]:
    headers = headers or {}
    headers.setdefault("User-Agent", "Mozilla/5.0 tutorials-collector/1.0")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [fetch error] {url}: {e}", file=sys.stderr)
        return None


def fetch_json(url: str, headers: Optional[dict] = None) -> Optional[dict]:
    headers = dict(headers or {})
    headers["Accept"] = "application/vnd.github+json"
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    data = fetch(url, headers=headers)
    if data:
        try:
            return json.loads(data)
        except Exception:
            pass
    return None


# ─── GitHub Trending ───────────────────────────────────────────────────────

def get_github_trending(days: int = 7, limit: int = 20) -> list[dict]:
    """Fetch recent GitHub repos from trending pages (Python/Go/JS)."""
    languages = ["python", "go", "javascript"]
    results = []

    for lang in languages:
        pushed_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        # Build query and encode each part separately
        query_parts = [
            ("q", f"stars:%3E100+pushed:%3E{pushed_date}"),
        ]
        url = f"https://api.github.com/search/repositories?q=stars:%3E100+pushed:%3E{pushed_date}&l={lang}&sort=stars&order=desc&per_page={limit}"
        data = fetch_json(url)
        if not data or "items" not in data:
            continue

        for repo in data["items"]:
            desc = (repo.get("description") or "").lower()
            if any(kw in desc for kw in AI_KEYWORDS):
                results.append({
                    "name": repo["full_name"],
                    "title": repo["name"],
                    "description": repo.get("description", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "url": repo["html_url"],
                    "source": "GitHub Trending",
                    "sourceIcon": "⭐",
                    "icon": _icon_for_repo(repo["name"]),
                    "tags": _tags_for_desc(desc),
                    "stars_str": _format_stars(repo.get("stargazers_count", 0)),
                    "date": repo.get("pushed_at", "")[:10],
                })

    return results


def get_curated_repos() -> list[dict]:
    """Fetch README and recent activity for curated tools."""
    results = []
    for tool in CURATED_TOOLS:
        # Get repo metadata
        data = fetch_json(f"https://api.github.com/repos/{tool['repo']}")
        if not data:
            continue

        desc = (data.get("description") or "").lower()
        results.append({
            "name": tool["name"],
            "title": tool["name"],
            "description": data.get("description") or "",
            "stars": data.get("stargazers_count", 0),
            "url": data.get("html_url"),
            "source": tool["name"] + " GitHub",
            "sourceIcon": tool["icon"],
            "icon": tool["icon"],
            "tags": tool["tags"],
            "stars_str": _format_stars(data.get("stargazers_count", 0)),
            "date": data.get("pushed_at", "")[:10],
            "docs_url": tool["docs_url"],
            "focus": tool["tutorial_focus"],
        })
        time.sleep(0.3)  # Rate limit
    return results


# ─── Hacker News ───────────────────────────────────────────────────────────

def get_hackernews_ai(limit: int = 10) -> list[dict]:
    """Get top AI-related Hacker News posts."""
    # Get top story IDs
    ids_data = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids_data:
        return []

    results = []
    count = 0
    for story_id in ids_data[:100]:  # Check top 100
        if count >= limit:
            break
        story = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not story:
            continue
        title = (story.get("title") or "").lower()
        if any(kw in title for kw in AI_KEYWORDS):
            results.append({
                "title": story.get("title", ""),
                "description": story.get("text", "")[:300] if story.get("text") else "",
                "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "source": "Hacker News",
                "sourceIcon": "📰",
                "stars_str": f"{story.get('score', 0)} pts",
                "date": datetime.fromtimestamp(story.get("time", 0)).strftime("%Y-%m-%d") if story.get("time") else "",
                "icon": "📰",
                "tags": _tags_for_desc(title),
            })
            count += 1
        time.sleep(0.1)
    return results


# ─── Helpers ───────────────────────────────────────────────────────────────

def _icon_for_repo(name: str) -> str:
    name = name.lower()
    if "ollama" in name: return "🖥️"
    if "openwebui" in name: return "🐳"
    if "openhands" in name: return "🤖"
    if "litellm" in name: return "💡"
    if "vllm" in name: return "🚀"
    if "langchain" in name: return "⛓️"
    if "hermes" in name: return "⚡"
    return "📦"


def _tags_for_desc(desc: str) -> list[str]:
    tags = []
    mapping = {
        "docker": "Docker", "container": "Docker",
        "gpu": "GPU", "cuda": "GPU", "nvidia": "GPU",
        "api": "API", "rest": "API", "grpc": "API",
        "llm": "LLM", "gpt": "LLM", "claude": "LLM",
        "python": "Python", "javascript": "JavaScript", "go": "Go",
        "deploy": "部署", "install": "部署", "setup": "部署",
        "agent": "AI Agent", "rag": "RAG",
        "ollama": "Ollama", "openwebui": "OpenWebUI",
    }
    for kw, tag in mapping.items():
        if kw in desc and tag not in tags:
            tags.append(tag)
    return tags[:4]


def _format_stars(n: int) -> str:
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def slugify(title: str) -> str:
    """Convert title to URL slug."""
    s = re.sub(r'[^\w\s-]', '', title.lower())
    s = re.sub(r'[\s_]+', '-', s)
    return s[:80]


def compute_dedup_key(post: dict) -> str:
    """Stable hash for deduplication."""
    return hashlib.md5(
        (post.get("url", "") + post.get("title", "")).encode()
    ).hexdigest()[:12]


# ─── Load existing data ────────────────────────────────────────────────────

def load_existing_data() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {"stats": {"total": 0, "sources": 0, "days": 0}, "posts": []}


# ─── Merge & deduplicate ────────────────────────────────────────────────────

def merge_posts(existing: list[dict], new_raw: list[dict]) -> list[dict]:
    seen_keys = {compute_dedup_key(p) for p in existing}
    merged = list(existing)

    for post in new_raw:
        key = compute_dedup_key(post)
        if key not in seen_keys:
            seen_keys.add(key)
            merged.insert(0, post)  # Newest first

    # Keep max 50 posts
    return merged[:50]


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print(f"[{datetime.now().isoformat()}] Starting tutorials collection...")
    existing = load_existing_data()
    all_new: list[dict] = []

    # 1. Curated repos
    print("  → Fetching curated repos...")
    curated = get_curated_repos()
    all_new.extend(curated)
    print(f"    Found {len(curated)} curated repos")

    # 2. GitHub Trending
    print("  → Fetching GitHub Trending...")
    trending = get_github_trending(days=7, limit=30)
    all_new.extend(trending)
    print(f"    Found {len(trending)} trending AI repos")

    # 3. Hacker News
    print("  → Fetching Hacker News...")
    hn = get_hackernews_ai(limit=10)
    all_new.extend(hn)
    print(f"    Found {len(hn)} HN posts")

    # Merge
    merged_posts = merge_posts(existing.get("posts", []), all_new)

    # Stats
    sources = set(p.get("source", "") for p in merged_posts)
    first_date = min((p["date"] for p in merged_posts if p.get("date")), default="")
    last_date = max((p["date"] for p in merged_posts if p.get("date")), default="")
    if first_date and last_date:
        try:
            days = (datetime.fromisoformat(last_date) - datetime.fromisoformat(first_date)).days + 1
        except Exception:
            days = 1
    else:
        days = 1

    # Update data.json
    new_data = {
        "stats": {
            "total": len(merged_posts),
            "sources": len(sources),
            "days": days,
        },
        "lastUpdated": datetime.now().isoformat(),
        "posts": merged_posts,
    }

    DATA_FILE.write_text(json.dumps(new_data, ensure_ascii=False, indent=2))
    print(f"\n✓ Updated {DATA_FILE}")
    print(f"  Total posts: {len(merged_posts)}")
    print(f"  Sources: {len(sources)}")
    print(f"  New this run: {len(all_new)}")

    return new_data


if __name__ == "__main__":
    main()
