#!/usr/bin/env python3
"""
generate_tutorials.py
读取 tutorials/_data.json，将新条目通过 AI 改写成中文教程 HTML 页面。
支持调用 OpenAI / Anthropic / OpenRouter 兼容 API。
"""

from __future__ import annotations
import json
import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

# ─── Config ──────────────────────────────────────────────────────────────

SITE_ROOT = Path(__file__).parent.parent.resolve()
POSTS_DIR = SITE_ROOT / "tutorials" / "_posts"
DATA_FILE = SITE_ROOT / "tutorials" / "_data.json"
TEMPLATE_FILE = SITE_ROOT / "tutorials" / "_post_template.html"

# LLM Provider: set OPENAI_API_KEY / ANTHROPIC_API_KEY / OPENROUTER_API_KEY
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | anthropic | openrouter
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")  # for openrouter/custom

# How many posts to generate per run (avoid hitting rate limits)
MAX_GENERATE_PER_RUN = 3

# ─── Template ─────────────────────────────────────────────────────────────

TUTORIAL_TEMPLATE = Path(__file__).parent / "_post_template.html"
if not TUTORIAL_TEMPLATE.exists():
    TUTORIAL_TEMPLATE = None

# ─── LLM Client ────────────────────────────────────────────────────────────

import urllib.request
import urllib.error


def call_llm(system: str, user: str) -> Optional[str]:
    """Call LLM API and return the response text."""

    if LLM_PROVIDER == "anthropic":
        payload = {
            "model": LLM_MODEL or "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": LLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        url = "https://api.anthropic.com/v1/messages"
    elif LLM_PROVIDER == "openrouter":
        payload = {
            "model": LLM_MODEL or "openai/gpt-4o-mini",
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "content-type": "application/json",
        }
        url = f"{LLM_BASE_URL}/chat/completions"
    else:  # openai
        payload = {
            "model": LLM_MODEL or "gpt-4o-mini",
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "content-type": "application/json",
        }
        url = f"{LLM_BASE_URL}/chat/completions"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode("utf-8"))
        if LLM_PROVIDER == "anthropic":
            return resp["content"][0]["text"]
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [LLM error] {e}", file=sys.stderr)
        return ""


# ─── Rewrite Prompt ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior technical writer specializing in AI tools tutorials.
You write in Chinese (Simplified) with a clear, practical, no-fluff style.
Format: Return ONLY a JSON object with this exact structure:
{
  "title": "Chinese title here",
  "summary": "2-3 sentence summary for the card",
  "readTime": "X min",
  "sections": [
    {
      "heading": "Section heading",
      "body": "Section body in Chinese, use code blocks for commands"
    }
  ],
  "tags": ["tag1", "tag2", "tag3", "tag4"]
}
Do NOT wrap the JSON in markdown code fences. Return only the JSON."""

USER_PROMPT_TEMPLATE = """Rewrite this GitHub project/AI tool into a practical Chinese tutorial page.

Project: {name}
Description: {description}
Stars: {stars}
URL: {url}
Tags: {tags}
Tags to include: {tags_str}

Focus areas: {focus}

Write a practical tutorial covering:
1. What this tool does and why use it (1 paragraph)
2. Installation / Deployment steps (with commands)
3. Basic configuration
4. Common use cases
5. Troubleshooting tips

Return the JSON only."""


# ─── HTML Generator ────────────────────────────────────────────────────────

def generate_tutorial_html(post: dict, rewritten: Optional[dict] = None) -> str:
    """Generate a tutorial HTML page from a post dict."""

    tags = rewritten.get("tags", post.get("tags", [])) if rewritten else post.get("tags", [])
    sections = rewritten.get("sections", []) if rewritten else []
    read_time = rewritten.get("readTime", "10 min") if rewritten else "10 min"

    toc_items = ""
    for i, sec in enumerate(sections, 1):
        anchor = sec["heading"].lower().replace(" ", "-")
        toc_items += f'<li><a href="#{anchor}">{sec["heading"]}</a></li>\n'

    sections_html = ""
    for sec in sections:
        anchor = sec["heading"].lower().replace(" ", "-")
        body = sec["body"]
        # Convert inline code `xxx` to <code class="cmd">
        body = re.sub(r"`([^`]+)`", r'<code class="cmd">\1</code>', body)
        # Convert ``` code blocks
        body = re.sub(r'```(\\w+)?\\n(.*?)\\n```', r'<div class="code-block"><pre>\2</pre></div>', body, flags=re.DOTALL)
        sections_html += f'<h2 id="{anchor}">{sec["heading"]}</h2>\n<p>{body}</p>\n'

    # Related cards (placeholder — references other tutorial slugs)
    related_html = ""
    other_slugs = ["ollama-gpu-setup", "hermes-agent-quickstart", "openhands-deployment"]
    for slug in other_slugs:
        related_html += f'''          <a href="/tutorials/{slug}" class="related-card">
            <h4>→ View Tutorial</h4>
            <p>{slug.replace("-", " ").title()}</p>
          </a>\n'''

    slug = post.get("slug", slugify(post.get("title", "")))
    title = rewritten.get("title", post.get("title", "")) if rewritten else post.get("title", "")
    summary = rewritten.get("summary", post.get("description", "")) if rewritten else post.get("description", "")
    date = post.get("date", datetime.now().strftime("%Y-%m-%d"))
    stars = post.get("stars_str", "")
    source = post.get("source", "")
    icon = post.get("icon", "📦")
    source_icon = post.get("sourceIcon", "📄")

    html = f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — DevUtils Tutorials</title>
<meta name="description" content="{summary[:160]}">
<link rel="canonical" href="https://devutils.uk/tutorials/{slug}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8715339444167250" crossorigin="anonymous"></script>
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
html{{scroll-behavior:smooth;-webkit-font-smoothing:antialiased}}
html.dark{{
  --bg:#0d0d10;--surface-1:#131316;--surface-2:#1a1a1f;--surface-3:#222228;
  --border-subtle:rgba(255,255,255,0.06);--border-standard:rgba(255,255,255,0.10);
  --border-strong:rgba(255,255,255,0.16);--text-primary:#f0f0f5;
  --text-secondary:#9090a0;--text-muted:#55556a;--accent:#6366f1;
  --accent-hover:#818cf8;--accent-dim:rgba(99,102,241,0.12);--header-bg:rgba(13,13,16,0.92);
}}
html.light{{
  --bg:#f8f8fa;--surface-1:#ffffff;--surface-2:#f2f2f6;--surface-3:#e8e8ee;
  --border-subtle:rgba(0,0,0,0.06);--border-standard:rgba(0,0,0,0.10);
  --border-strong:rgba(0,0,0,0.16);--text-primary:#111118;
  --text-secondary:#55556a;--text-muted:#9090a0;--accent:#4f46e5;
  --accent-hover:#6366f1;--accent-dim:rgba(79,70,229,0.08);--header-bg:rgba(248,248,250,0.92);
}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text-secondary);line-height:1.7;font-size:16px}}
h1,h2,h3,h4{{color:var(--text-primary);line-height:1.25}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{color:var(--accent-hover);text-decoration:underline}}
::-webkit-scrollbar{{width:6px}}::-webkit-scrollbar-track{{background:var(--bg)}}::-webkit-scrollbar-thumb{{background:var(--border-strong);border-radius:3px}}

header{{position:sticky;top:0;z-index:100;background:var(--header-bg);border-bottom:1px solid var(--border-subtle);backdrop-filter:blur(12px)}}
.nav-inner{{max-width:860px;margin:0 auto;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between}}
.nav-logo{{font-weight:600;color:var(--text-primary);display:flex;align-items:center;gap:8px}}
.nav-links{{display:flex;gap:6px}}
.nav-link{{padding:6px 12px;border-radius:8px;font-size:14px;font-weight:500;color:var(--text-secondary);transition:all .15s}}
.nav-link:hover,.nav-link.active{{color:var(--text-primary);background:var(--surface-2)}}
.theme-toggle{{width:36px;height:36px;border-radius:8px;border:1px solid var(--border-standard);background:var(--surface-1);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;transition:all .15s}}

.article-wrap{{max-width:860px;margin:0 auto;padding:48px 24px 80px}}
.article-header{{margin-bottom:40px}}
.article-meta{{display:flex;gap:16px;align-items:center;margin-bottom:20px;font-size:13px;color:var(--text-muted);flex-wrap:wrap}}
.article-badge{{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:100px;background:var(--accent-dim);color:var(--accent);font-size:12px;font-weight:500}}
.article-title{{font-size:clamp(26px,4vw,38px);font-weight:700;margin-bottom:16px;letter-spacing:-0.02em}}
.article-summary{{font-size:18px;color:var(--text-muted);line-height:1.6;margin-bottom:20px}}
.article-tags{{display:flex;gap:6px;flex-wrap:wrap}}
.tag{{padding:4px 12px;border-radius:100px;font-size:12px;font-weight:500;background:var(--accent-dim);color:var(--accent)}}

.toc{{background:var(--surface-1);border:1px solid var(--border-subtle);border-radius:12px;padding:20px 24px;margin-bottom:40px}}
.toc-title{{font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:12px}}
.toc ol{{list-style:none;counter-reset:toc;padding:0}}
.toc li{{counter-increment:toc;margin-bottom:8px;display:flex}}
.toc li::before{{content:counter(toc);min-width:24px;color:var(--text-muted);font-size:13px}}
.toc a{{font-size:14px;color:var(--text-secondary)}}
.toc a:hover{{color:var(--accent)}}

.article-content h2{{font-size:24px;font-weight:600;margin:40px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border-subtle)}}
.article-content h3{{font-size:18px;font-weight:600;margin:28px 0 12px}}
.article-content p{{margin-bottom:16px;font-size:15px}}
.article-content ul,.article-content ol{{margin:0 0 16px 24px}}
.article-content li{{margin-bottom:8px;font-size:15px}}
.article-content strong{{color:var(--text-primary);font-weight:600}}
.article-content a{{color:var(--accent);text-decoration:underline;text-underline-offset:3px}}
.code-block{{background:var(--surface-2);border:1px solid var(--border-standard);border-radius:12px;padding:20px 24px;margin:20px 0;overflow-x:auto}}
.code-block pre{{margin:0;font-family:'JetBrains Mono',monospace;font-size:14px;line-height:1.6;color:var(--text-primary)}}
.cmd{{font-family:'JetBrains Mono',monospace;font-size:13px;background:var(--surface-3);padding:2px 8px;border-radius:4px;color:var(--accent)}}

.related{{margin-top:60px;padding-top:32px;border-top:1px solid var(--border-subtle)}}
.related h3{{font-size:18px;margin-bottom:16px}}
.related-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
.related-card{{display:block;padding:16px;border-radius:12px;border:1px solid var(--border-subtle);background:var(--surface-1);transition:all .15s;text-decoration:none}}
.related-card:hover{{border-color:var(--border-standard);transform:translateY(-1px);text-decoration:none}}
.related-card h4{{font-size:14px;margin-bottom:4px;color:var(--text-primary)}}
.related-card p{{font-size:12px;color:var(--text-muted)}}

.source-footer{{margin-top:40px;padding:20px;border-radius:12px;background:var(--surface-1);border:1px solid var(--border-subtle);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;font-size:13px;color:var(--text-muted)}}

footer{{max-width:860px;margin:0 auto 40px;padding:24px 0;border-top:1px solid var(--border-subtle);text-align:center;font-size:13px;color:var(--text-muted)}}
</style>
</head>
<body>

<header>
  <nav class="nav-inner">
    <a href="/tutorials" class="nav-logo" style="text-decoration:none">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect width="24" height="24" rx="6" fill="var(--accent)"/><path d="M7 8h10M7 12h7M7 16h5" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>
      DevUtils
    </a>
    <div class="nav-links">
      <a href="/" class="nav-link">Tools</a>
      <a href="/tutorials" class="nav-link active">Tutorials</a>
      <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">◐</button>
    </div>
  </nav>
</header>

<article class="article-wrap">
  <div class="article-header">
    <div class="article-meta">
      <span class="article-badge">{icon} {source}</span>
      <span>📅 {date}</span>
      <span>⏱️ {read_time} read</span>
      {f'<span>⭐ {stars}</span>' if stars else ''}
    </div>
    <h1 class="article-title">{title}</h1>
    <p class="article-summary">{summary}</p>
    <div class="article-tags">
      {''.join(f'<span class="tag">{t}</span>' for t in tags[:5])}
    </div>
  </div>

  <nav class="toc">
    <div class="toc-title">📋 Table of Contents</div>
    <ol>
      {toc_items or '<li><a href="#overview">概述</a></li>'}
    </ol>
  </nav>

  <div class="article-content">
    {sections_html or f'<h2 id="overview">概述</h2><p>{summary}</p>'}
  </div>

  <div class="related">
    <h3>Related Tutorials</h3>
    <div class="related-grid">
      {related_html or ''}
    </div>
  </div>

  <div class="source-footer">
    <span>📄 原文来源：<a href="{post.get("url", "#")}" target="_blank">{source}</a></span>
    <span>🔄 最后更新：{date} · <a href="/tutorials">← Back to Tutorials</a></span>
  </div>
</article>

<footer>
  <a href="/">DevUtils.uk</a> — Free developer tools & AI tutorials
</footer>

<script>
function toggleTheme() {{
  const next = document.documentElement.className === 'dark' ? 'light' : 'dark';
  document.documentElement.className = next;
  localStorage.setItem('theme', next);
}}
(function() {{
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.className = saved;
}})();
</script>
</body>
</html>'''

    return html


def slugify(title: str) -> str:
    s = re.sub(r'[^\w\s-]', '', title.lower())
    s = re.sub(r'[\s_]+', '-', s)
    return s[:80]


# ─── Main ─────────────────────────────────────────────────────────────────

def main():
    if not DATA_FILE.exists():
        print("No _data.json found. Run collect_tutorials.py first.")
        return

    data = json.loads(DATA_FILE.read_text())
    posts = data.get("posts", [])

    generated = 0
    for post in posts:
        slug = post.get("slug") or slugify(post.get("title", ""))
        post["slug"] = slug
        out_file = POSTS_DIR / f"{slug}.html"

        # Skip if already exists and has content
        if out_file.exists() and out_file.stat().st_size > 1000:
            print(f"  ⏭️  Skipping {slug} (already exists)")
            continue

        print(f"\n  → Generating: {post.get('title', slug)[:60]}")

        # Call LLM for rewrite (if API key available)
        rewritten = None
        if LLM_API_KEY:
            try:
                focus = ", ".join(post.get("focus", post.get("tags", []))[:4])
                tags_str = ", ".join(post.get("tags", [])[:5])
                user_msg = USER_PROMPT_TEMPLATE.format(
                    name=post.get("name", post.get("title", "")),
                    description=post.get("description", ""),
                    stars=post.get("stars_str", ""),
                    url=post.get("url", ""),
                    tags=", ".join(post.get("tags", [])),
                    tags_str=tags_str,
                    focus=focus,
                )
                raw = call_llm(SYSTEM_PROMPT, user_msg)
                if raw:
                    # Strip markdown code fences if present
                    raw = re.sub(r'^```json\\s*', '', raw.strip())
                    raw = re.sub(r'\\s*```$', '', raw.strip())
                    rewritten = json.loads(raw)
                    print(f"    ✓ LLM rewrite done")
            except Exception as e:
                print(f"    ⚠ LLM rewrite failed: {e}")
                rewritten = None
            time.sleep(1)
        else:
            print(f"    ℹ No LLM_API_KEY — generating from template")

        html = generate_tutorial_html(post, rewritten)
        out_file.write_text(html, encoding="utf-8")
        print(f"    ✓ Saved: {out_file.relative_to(SITE_ROOT)}")
        generated += 1

        if generated >= MAX_GENERATE_PER_RUN:
            print(f"\n⚠ Reached max {MAX_GENERATE_PER_RUN} posts per run. Re-run to continue.")
            break

    print(f"\n✓ Done. Generated {generated} new tutorial pages.")


if __name__ == "__main__":
    main()
