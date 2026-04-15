#!/usr/bin/env python3
"""
generate_blog.py — AI 生成 SEO 博客文章
用法: python3 generate_blog.py [--force] [--limit N]
"""

import json, re, sys, os, base64, subprocess, urllib.request
from datetime import datetime

REPO = "wxylxy99/devtools-site"
BLOG_DIR = "blog"
POSTS_FILE = f"{BLOG_DIR}/_posts.json"

# 工具 → 博客文章关键词映射（可扩展）
TOOL_BLOG_KEYWORDS = {
    "color-converter": {
        "title": "Color Converter: HEX, RGB, HSL Online Free Tool",
        "description": "Convert colors between HEX, RGB, HSL, and CMYK formats instantly. Free online color converter with live preview and copy-to-clipboard.",
        "keywords": "color converter, hex to rgb, rgb to hex, hsl converter, color picker, color code converter",
        "slug": "color-converter",
        "tool": "Color Converter",
        "sections": [
            ("Why Color Conversion Matters for Developers", "Web developers frequently need to convert colors between HEX, RGB, and HSL formats when working with CSS, design tools, and color pickers. ..."),
            ("Supported Color Formats", ""),
            ("How to Use the Color Converter", ""),
            ("Common Color Conversion Formulas", ""),
            ("Best Practices for Color Handling", ""),
        ]
    },
    "regex-tester": {
        "title": "Regex Tester: Test Regular Expressions Online Free",
        "description": "Test and debug regular expressions in real-time. Supports JavaScript, Python, and PCRE syntax with instant match highlighting and group extraction.",
        "keywords": "regex tester, regular expression tester, online regex, regex debugger, regex match",
        "slug": "regex-tester",
        "tool": "Regex Tester",
        "sections": [
            ("What is a Regex Tester and Why Do You Need One?", "Regular expressions (regex) are patterns used to match character combinations in text. ..."),
            ("Regex Syntax Quick Reference", ""),
            ("How to Test Regex Online", ""),
            ("Common Regex Patterns with Examples", ""),
            ("Regex Best Practices", ""),
        ]
    },
    "url-encoder-decoder": {
        "title": "URL Encoder / Decoder: Encode Decode URLs Online Free",
        "description": "Encode and decode URLs instantly. Safely transmit special characters over the web with percent-encoding (URL encoding) explained.",
        "keywords": "url encoder, url decoder, percent encoding, encode url, urlencode, urldecode",
        "slug": "url-encoder-decoder",
        "tool": "URL Encoder / Decoder",
        "sections": [
            ("Understanding URL Encoding", "URLs can only be sent over the Internet using the ASCII character set. ..."),
            ("When Do You Need URL Encoding?", ""),
            ("How to Encode and Decode URLs", ""),
            ("Reserved Characters in URLs", ""),
            ("URL Encoding in Different Programming Languages", ""),
        ]
    },
}

POSTS_FILE = f"{BLOG_DIR}/_posts.json"


def gh_api(path, method="GET", data=None):
    """通过 gh CLI 调用 GitHub API"""
    cmd = ["gh", "api", f"repos/{REPO}/contents/{path}", "--method", method]
    if data:
        for k, v in data.items():
            cmd += ["--field", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def get_sha(path):
    result = gh_api(path)
    try:
        return json.loads(result.stdout).get("sha", "")
    except:
        return ""


def get_content(path):
    sha = get_sha(path)
    if not sha:
        return None
    result = gh_api(path)
    try:
        raw = json.loads(result.stdout).get("content", "")
        return base64.b64decode(raw + "==").decode("utf-8")
    except:
        return None


def get_existing_slugs():
    """获取已存在的 blog post slugs"""
    slugs = set()
    result = subprocess.run(
        ["gh", "api", f"repos/{REPO}/contents/{BLOG_DIR}", "--jq", ".[].name"],
        capture_output=True, text=True
    )
    for name in result.stdout.strip().split("\n"):
        name = name.strip()
        if name.endswith(".html") and name != "index.html":
            slugs.add(name.replace(".html", ""))
    return slugs


def get_posts_data():
    """获取 _posts.json 数据"""
    content = get_content(POSTS_FILE)
    if content:
        try:
            return json.loads(content)
        except:
            pass
    return {"posts": [], "lastUpdated": ""}


def generate_html(slug, keyword_data):
    """生成完整的 SEO 博客 HTML"""
    title = keyword_data["title"]
    description = keyword_data["description"]
    keywords = keyword_data["keywords"]
    tool = keyword_data["tool"]
    slug_val = keyword_data["slug"]
    today = datetime.now().strftime("%Y-%m-%d")

    article_body = generate_article_body(keyword_data)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <link rel="canonical" href="https://devutils.uk/blog/{slug_val}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-tertiary: #1a1a25;
            --text-primary: #e4e4e7;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --accent: #6366f1;
            --accent-hover: #818cf8;
            --border: #27272a;
            --code-bg: #16161d;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
            font-size: 16px;
        }}
        a {{ color: var(--accent); text-decoration: none; transition: color 0.2s; }}
        a:hover {{ color: var(--accent-hover); text-decoration: underline; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 0 20px; }}
        header {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 16px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .header-inner {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .logo {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #fff;
        }}
        .logo span {{ color: var(--accent); }}
        nav ul {{
            display: flex;
            list-style: none;
            gap: 24px;
        }}
        nav a {{ color: var(--text-secondary); font-size: 0.95rem; }}
        nav a:hover {{ color: var(--text-primary); text-decoration: none; }}
        .breadcrumb {{
            padding: 16px 0;
            font-size: 0.875rem;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }}
        .breadcrumb a {{ color: var(--text-secondary); }}
        main {{ padding-bottom: 60px; }}
        article h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 16px;
            line-height: 1.3;
            background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .article-meta {{
            display: flex;
            gap: 20px;
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
        }}
        .article-meta span {{ display: flex; align-items: center; gap: 6px; }}
        .article-content {{ font-size: 1.05rem; }}
        article h2 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-top: 40px;
            margin-bottom: 16px;
            color: var(--text-primary);
        }}
        article h3 {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-top: 28px;
            margin-bottom: 12px;
            color: var(--text-primary);
        }}
        article p {{ margin-bottom: 20px; color: var(--text-secondary); }}
        article ul, article ol {{ margin-bottom: 20px; padding-left: 24px; color: var(--text-secondary); }}
        article li {{ margin-bottom: 8px; }}
        pre {{
            background: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
            margin-bottom: 24px;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
        }}
        code {{
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            background: var(--bg-tertiary);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.875em;
            color: #79c0ff;
        }}
        pre code {{ background: none; padding: 0; color: #e6edf3; }}
        .tool-callout {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            border-radius: 8px;
            padding: 20px;
            margin: 24px 0;
        }}
        .tool-callout h4 {{ margin-bottom: 8px; color: var(--accent); }}
        .tool-callout p {{ margin-bottom: 0; font-size: 0.95rem; }}
        .tool-callout a {{ font-weight: 600; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 24px 0;
            font-size: 0.95rem;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: var(--text-primary); font-weight: 600; background: var(--bg-secondary); }}
        footer {{
            border-top: 1px solid var(--border);
            padding: 24px 0;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}
        @media (max-width: 640px) {{
            article h1 {{ font-size: 1.6rem; }}
            article h2 {{ font-size: 1.3rem; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container header-inner">
            <a href="/" class="logo">Dev<span>Utils</span></a>
            <nav>
                <ul>
                    <li><a href="/">Tools</a></li>
                    <li><a href="/blog/">Blog</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <div class="container">
        <div class="breadcrumb">
            <a href="/">DevUtils</a> <span>&rsaquo;</span>
            <a href="/blog/">Blog</a> <span>&rsaquo;</span>
            {tool}
        </div>

        <main>
            <article>
                <h1>{title}</h1>
                <div class="article-meta">
                    <span>&#128197; {today}</span>
                    <span>&#128214; {tool}</span>
                    <span>&#128337; 5 min read</span>
                </div>

                <div class="article-content">
{article_body}
                </div>
            </article>
        </main>
    </div>

    <footer>
        <div class="container">
            <p>&copy; {datetime.now().year} DevUtils &mdash; <a href="/">Free Developer Tools</a></p>
        </div>
    </footer>
</body>
</html>"""


def generate_article_body(keyword_data):
    """根据工具生成文章正文（简化版，实际可接 AI API）"""
    slug = keyword_data["slug"]

    bodies = {
        "color-converter": """
<p>Converting between color formats is a daily task for web developers and designers. Whether you're working with CSS custom properties, adjusting brand colors in Figma, or debugging UI rendering issues — having a reliable color converter saves time and prevents frustration.</p>

<h2>Supported Color Formats</h2>
<p>Our free online color converter handles all standard web color formats:</p>
<ul>
    <li><strong>HEX</strong> — 6-digit hex code (e.g., <code>#6366f1</code>) used in CSS and design tools</li>
    <li><strong>RGB</strong> — Red/Green/Blue values (e.g., <code>rgb(99, 102, 241)</code>) for digital displays</li>
    <li><strong>HSL</strong> — Hue/Saturation/Lightness (e.g., <code>hsl(239, 84%, 67%)</code>) for intuitive color adjustments</li>
    <li><strong>HSB/Hue</strong> — Hue/Saturation/Brightness used in Figma and Adobe tools</li>
</ul>

<h2>How to Convert Colors</h2>
<p>Enter any color value in any format and get instant conversions across all formats:</p>
<div class="tool-callout">
    <h4>&#9889; Try the Color Converter</h4>
    <p>Use our free <a href="/#color">Color Converter tool</a> — enter a HEX code like <code>#6366f1</code> and see RGB, HSL, and HSB values instantly.</p>
</div>

<h2>Common Conversion Formulas</h2>
<p>Understanding how color conversion works helps when debugging. Here are the key formulas:</p>

<h3>HEX to RGB</h3>
<pre><code>// #6366f1 → rgb(99, 102, 241)
const hexToRgb = (hex) => {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgb(${{r}}, ${{g}}, ${{b}})`;
};</code></pre>

<h3>RGB to HSL</h3>
<pre><code>const rgbToHsl = (r, g, b) => {{
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;

  if (max === min) {{
    h = s = 0;
  }} else {{
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {{
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }}
  }}
  return `hsl(${{Math.round(h * 360)}}, ${{Math.round(s * 100)}}%, ${{Math.round(l * 100)}}%)`;
}};</code></pre>

<h2>Best Practices for Color Handling</h2>
<ul>
    <li><strong>Use HEX for production CSS</strong> — smallest file size, widely supported</li>
    <li><strong>Use HSL for color manipulation</strong> — adjusting lightness/saturation feels natural</li>
    <li><strong>Consider alpha with RGBA/HSLA</strong> — for overlays and transparency</li>
    <li><strong>Test in both light and dark modes</strong> — some colors look drastically different</li>
</ul>

<div class="tool-callout">
    <h4>&#9889; Color Converter Tool</h4>
    <p>Convert between HEX, RGB, HSL, and HSB formats instantly with live preview. <a href="/#color">Open the free tool &rarr;</a></p>
</div>
""",

        "regex-tester": """
<p>Regular expressions (regex) are one of the most powerful tools in a developer's toolkit — but they're also notoriously difficult to write and debug without immediate feedback. A good regex tester with real-time validation can cut hours of frustration down to minutes.</p>

<h2>What is Regex Testing?</h2>
<p>Regex testing validates whether your regular expression pattern matches the intended text. It shows exactly which characters match, which capture groups are extracted, and flags syntax errors in your pattern before you deploy it to production.</p>

<div class="tool-callout">
    <h4>&#9889; Try the Regex Tester</h4>
    <p>Test your regular expressions in real-time with our <a href="/#regex">free Regex Tester tool</a>. Supports match highlighting, group extraction, and common pattern library.</p>
</div>

<h2>Regex Syntax Quick Reference</h2>
<table>
    <tr><th>Pattern</th><th>Meaning</th><th>Example</th></tr>
    <tr><td><code>.</code></td><td>Any character</td><td><code>a.c</code> matches "abc"</td></tr>
    <tr><td><code>^</code></td><td>Start of string</td><td><code>^hello</code> matches "hello world"</td></tr>
    <tr><td><code>$</code></td><td>End of string</td><td><code>world$</code> matches "hello world"</td></tr>
    <tr><td><code>*</code></td><td>0 or more</td><td><code>ab*c</code> matches "ac", "abc"</td></tr>
    <tr><td><code>+</code></td><td>1 or more</td><td><code>ab+c</code> matches "abc" not "ac"</td></tr>
    <tr><td><code>?</code></td><td>0 or 1</td><td><code>colou?r</code> matches "color", "colour"</td></tr>
    <tr><td><code>[abc]</code></td><td>Character class</td><td><code>[aeiou]</code> matches vowels</td></tr>
    <tr><td><code>[a-z]</code></td><td>Range</td><td><code>[0-9]</code> matches digits</td></tr>
    <tr><td><code>\\d</code></td><td>Digit</td><td><code>\\d{{3}}</code> matches "123"</td></tr>
    <tr><td><code>\\w</code></td><td>Word character</td><td><code>\\w+</code> matches words</td></tr>
    <tr><td><code>()</code></td><td>Capture group</td><td><code>(\\d+)px</code> captures digits</td></tr>
    <tr><td><code>|</code></td><td>Alternation</td><td><code>cat|dog</code> matches either</td></tr>
</table>

<h2>Common Regex Patterns</h2>

<h3>Email Validation</h3>
<pre><code>^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$</code></pre>

<h3>URL Matching</h3>
<pre><code>https?:\\/\\/[\\w\\-]+(\\.[\\w\\-]+)+[\\/#?]?.*$</code></pre>

<h3>Phone Number (US)</h3>
<pre><code>\\(?\\d{{3}}\\)?[-.\\s]?\\d{{3}}[-.\\s]?\\d{{4}}</code></pre>

<h3>IPv4 Address</h3>
<pre><code>^(?:(?:25[0-5]|2[0-4]\\d|[01]?\\d\\d?)\\.){{3}}(?:25[0-5]|2[0-4]\\d|[01]?\\d\\d?)$</code></pre>

<h2>Regex Best Practices</h2>
<ul>
    <li><strong>Start simple</strong> — build patterns incrementally and test at each step</li>
    <li><strong>Use capture groups wisely</strong> — only capture what you need; non-capturing groups <code>(?:...)</code> are faster</li>
    <li><strong>Avoid greedy quantifiers when possible</strong> — use <code>.*?</code> instead of <code>.*</code> for non-greedy matching</li>
    <li><strong>Test edge cases</strong> — empty strings, very long strings, special characters</li>
    <li><strong>Comment your patterns</strong> — use <code>(?#comment)</code> or break complex patterns into named groups</li>
</ul>

<div class="tool-callout">
    <h4>&#9889; Regex Tester Tool</h4>
    <p>Debug and test your regex patterns in real-time. <a href="/#regex">Try it free &rarr;</a></p>
</div>
""",

        "url-encoder-decoder": """
<p>URL encoding (also called percent-encoding) is essential for transmitting data over the web safely. Every time you submit a form, paste a URL with special characters, or send data via query parameters — URL encoding is working behind the scenes.</p>

<h2>Understanding URL Encoding</h2>
<p>The HTTP protocol only allows a limited set of characters in URLs: letters, digits, hyphens, underscores, tildes, and periods. All other characters must be encoded using percent-encoding, which converts each byte to a <code>%XX</code> format where <code>XX</code> is the hexadecimal ASCII code of the character.</p>

<div class="tool-callout">
    <h4>&#9889; Try the URL Encoder/Decoder</h4>
    <p>Encode or decode any URL instantly with our <a href="/#url">free URL Encoder/Decoder tool</a>. Handles special characters, spaces, Unicode, and full URLs.</p>
</div>

<h2>When Do You Need URL Encoding?</h2>
<ul>
    <li><strong>Query parameters</strong> — spaces and special chars in search queries (<code>?q=hello world</code> → <code>?q=hello%20world</code>)</li>
    <li><strong>Path parameters</strong> — file names with spaces or non-ASCII characters</li>
    <li><strong>Form submissions</strong> — <code>application/x-www-form-urlencoded</code> format</li>
    <li><strong>API requests</strong> — embedding JSON or special characters in query strings</li>
    <li><strong>Bookmarklets</strong> — JavaScript URLs with encoded parameters</li>
</ul>

<h2>Key Characters Reference</h2>
<table>
    <tr><th>Character</th><th>Encoded</th><th>Use Case</th></tr>
    <tr><td><code> </code> (space)</td><td><code>%20</code></td><td>Most common encoding in URLs</td></tr>
    <tr><td><code>#</code></td><td><code>%23</code></td><td>Fragment identifier — do NOT encode in path</td></tr>
    <tr><td><code>&</code></td><td><code>%26</code></td><td>Query param separator — encode in values</td></tr>
    <tr><td><code>=</code></td><td><code>%3D</code></td><td>Key-value assignment — encode in values</td></tr>
    <tr><td><code>/</code></td><td><code>%2F</code></td><td>Path separator — encode in path segments</td></tr>
    <tr><td><code>?</code></td><td><code>%3F</code></td><td>Query string start — encode in path</td></tr>
    <tr><td><code>+</code></td><td><code>%2B</code></td><td>Reserved — often used for space in query values</td></tr>
    <tr><td><code>世</code> (Unicode)</td><td><code>%E4%B8%96</code></td><td>Multi-byte UTF-8 encoded as multiple %XX pairs</td></tr>
</table>

<h2>URL Encoding in Different Languages</h2>

<h3>JavaScript</h3>
<pre><code>// Encode
encodeURIComponent("hello world");  // "hello%20world"
encodeURI("https://example.com/a b");  // "https://example.com/a%20b"

// Decode
decodeURIComponent("hello%20world");  // "hello world"</code></pre>

<h3>Python</h3>
<pre><code>from urllib.parse import quote, urlencode, unquote

# Encode
quote("hello world")          # "hello%20world"
quote("hello world", safe="")  # force encode spaces

# Query dict
urlencode({{"name": "Alice", "city": "New York"}})
# "name=Alice&city=New%20York"

# Decode
unquote("hello%20world")      # "hello world"</code></pre>

<h3>URL Safe Encoding</h3>
<pre><code>// encodeURI does NOT encode: A-Za-z0-9-_.~
// Use encodeURIComponent for individual values (aggressive)
// Use encodeURI for full URLs (preserves structural chars)</code></pre>

<h2>Common Mistakes to Avoid</h2>
<ul>
    <li><strong>Don't double-encode</strong> — encode before sending, decode on receipt. Encoding twice produces <code>%2520</code> instead of <code>%20</code></li>
    <li><strong>Don't encode full URLs with <code>encodeURIComponent</code></code></li>
    <li>— use <code>encodeURI</code> instead, which preserves <code>:/?#[]@!$&amp;'()*+,;=</code></li>
    <li><strong>Encode path segments separately</strong> — each path segment should be encoded independently</li>
    <li><strong>Handle Unicode properly</strong> — always UTF-8 encode before percent-encoding</li>
</ul>

<div class="tool-callout">
    <h4>&#9889; URL Encoder / Decoder</h4>
    <p>Encode and decode URLs with full Unicode support. <a href="/#url">Use the free tool &rarr;</a></p>
</div>
""",
    }

    return bodies.get(slug, "<p>Article content coming soon.</p>")


def push_file(path, content, message):
    """通过 gh api 推送文件"""
    sha = get_sha(path)
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    cmd = [
        "gh", "api", f"repos/{REPO}/contents/{path}",
        "--method", "PUT",
        "--field", f"message={message}",
        "--field", f"content={content_b64}",
    ]
    if sha:
        cmd += ["--field", f"sha={sha}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def update_posts_json(new_post):
    """更新 _posts.json"""
    posts = get_posts_data()
    slugs = {p["slug"] for p in posts.get("posts", [])}
    if new_post["slug"] in slugs:
        return False
    posts["posts"].insert(0, new_post)
    posts["lastUpdated"] = datetime.now().isoformat()
    content = json.dumps(posts, ensure_ascii=False, indent=2)
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    sha = get_sha(POSTS_FILE)
    cmd = [
        "gh", "api", f"repos/{REPO}/contents/{POSTS_FILE}",
        "--method", "PUT",
        "--field", f"message=auto: add blog post {new_post['slug']} [blog-gen]",
        "--field", f"content={content_b64}",
    ]
    if sha:
        cmd += ["--field", f"sha={sha}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    force = "--force" in sys.argv
    limit = 1
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])

    existing = get_existing_slugs()
    posts_data = get_posts_data()
    posts_slugs = {p["slug"] for p in posts_data.get("posts", [])}
    all_missing = [s for s in TOOL_BLOG_KEYWORDS if s not in existing and s not in posts_slugs]

    if not all_missing:
        print("✅ All blog posts already exist. Nothing to generate.")
        return

    to_generate = all_missing[:limit]
    today = datetime.now().strftime("%Y-%m-%d")

    for slug in to_generate:
        kw = TOOL_BLOG_KEYWORDS[slug]
        print(f"Generating blog post: {slug}")

        html = generate_html(slug, kw)
        file_path = f"{BLOG_DIR}/{slug}.html"
        ok = push_file(
            file_path,
            html,
            f"auto: add blog post {slug} [{today}]"
        )

        new_post = {
            "slug": slug,
            "title": kw["title"],
            "description": kw["description"],
            "date": today,
            "tags": [kw["tool"]],
            "readTime": "5 min",
            "url": f"/blog/{slug}.html",
            "tool": kw["tool"],
        }
        posts_ok = update_posts_json(new_post)

        if ok and posts_ok:
            print(f"  ✅ {slug}.html + _posts.json updated")
        else:
            print(f"  ❌ Failed to push {slug}")


if __name__ == "__main__":
    main()
