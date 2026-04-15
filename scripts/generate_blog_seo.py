#!/usr/bin/env python3
"""
DevUtils SEO Blog 自动生成脚本
每天生成一篇 SEO 博客文章并推送至 GitHub
用法: python3 generate_blog_seo.py [topic_index]
"""
import urllib.request
import subprocess
import json
import re
import base64
import os
import sys
from datetime import datetime

REPO = "wxylxy99/devtools-site"
TODAY = datetime.now().strftime("%Y-%m-%d")

SEO_TOPICS = [
    ("jwt-token-decoder",
     "JWT Token Decoder Online — 免费在线验证解析 JWT",
     "JWT (JSON Web Token) 是现代 Web 开发中最常用的身份认证方案之一。本文详细介绍 JWT 的结构（Header、Payload、Signature）、验证方法和常见安全坑点，帮助开发者快速调试和排查认证问题。",
     ["JWT", "Auth", "Web"], "中级"),
    ("uuid-generator-v4",
     "UUID v4 生成器 — 免费在线批量创建唯一标识符",
     "UUID（通用唯一标识符）是软件开发中广泛使用的 128 位标识符，UUIDv4 通过随机数生成，几乎可以保证全球唯一。本文介绍 UUID 的各版本区别、生成方法和在数据库设计中的应用。",
     ["UUID", "Generator", "Backend"], "初级"),
    ("cron-expression-validator",
     "Cron Expression 校验器 — 在线验证 Crontab 表达式",
     "Cron 表达式是 Linux/Unix 系统中定时任务的配置语法。本文详细介绍标准 5 段式 Cron 的格式、常用示例以及各平台的差异，帮助运维和后端开发者正确配置定时任务。",
     ["Cron", "DevOps", "Linux"], "中级"),
    ("rsa-key-generator",
     "RSA 密钥对生成器 — 免费在线生成公钥私钥",
     "RSA 是最常用的非对称加密算法，广泛用于 SSH、SSL/TLS 证书和数字签名。本文介绍 RSA 密钥的原理、生成方法以及在实际项目中的使用场景和安全管理建议。",
     ["RSA", "Security", "Crypto"], "中级"),
    ("yaml-validator-formatter",
     "YAML 格式校验器 — 在线验证 YAML 语法正确性",
     "YAML（YAML Ain't Markup Language）是一种人类可读的数据序列化格式，广泛用于 Docker Compose、Kubernetes 和 CI/CD 配置文件。本文介绍 YAML 的基本语法、常见错误和在线校验工具使用方法。",
     ["YAML", "DevOps", "Config"], "初级"),
    ("sql-formatter-online",
     "SQL 在线格式化工具 — 美化压缩 SQL 语句",
     "SQL 格式化对于团队协作和代码审查至关重要。本文介绍 SQL 美化的原则、常用格式化规则以及在线工具的使用方法，帮助写出整洁易读的 SQL 代码。",
     ["SQL", "Database", "Formatter"], "初级"),
    ("html-entity-encoder",
     "HTML 实体编码解码 — 在线转换 HTML 特殊字符",
     "HTML 实体编码用于在网页中安全显示特殊字符（如 < > & \" '），防止 XSS 攻击和渲染异常。本文介绍 HTML 实体编码规则和在线编解码工具的使用方法。",
     ["HTML", "Web", "Encoder"], "初级"),
    ("jwt-debugger-online",
     "JWT Debugger — 在线实时调试 JWT Token",
     "JWT Debugger 让你无需代码即可解析、验证和调试 JWT Token，支持查看 Header、Payload、签名验证结果，是后端和前端开发者排查认证问题的利器。",
     ["JWT", "Debug", "Web"], "初级"),
    ("regex-cheatsheet-developer",
     "正则表达式速查表 — 开发必备常用正则大全",
     "正则表达式是开发者处理字符串的瑞士军刀。本文整理了最常用的正则表达式模式，涵盖邮箱、手机号、URL、IP、日期等常见场景，附带代码示例，方便快速查询和使用。",
     ["Regex", "DevTools", "Cheatsheet"], "初级"),
    ("hash-generator-md5-sha",
     "Hash (MD5/SHA) 在线生成器 — 一键计算字符串哈希",
     "MD5、SHA-1、SHA-256 等哈希算法在密码存储和数据完整性校验中广泛使用。本文介绍各哈希算法的特点、安全注意事项和在线生成器的使用方法。",
     ["Hash", "Security", "Crypto"], "初级"),
    ("jwt-vs-session-auth",
     "JWT vs Session — Web 认证方案对比分析",
     "选择 JWT 还是 Session-Cookie 是 Web 开发中的经典问题。本文从实现复杂度、安全性、扩展性和适用场景四个维度全面对比两种认证方案，帮助架构师做出正确选择。",
     ["JWT", "Auth", "Security"], "中级"),
    ("json-schema-validator",
     "JSON Schema 验证器 — 在线校验 JSON 数据结构",
     "JSON Schema 是一个用于描述和验证 JSON 数据结构的强大工具。本文介绍 JSON Schema 的基本语法、常用关键字以及在线验证工具的使用方法。",
     ["JSON", "Schema", "Validation"], "中级"),
    ("xml-formatter-online",
     "XML 格式化工具 — 在线美化压缩 XML",
     "XML 仍然是许多遗留系统和 SOAP Web 服务的数据格式。本文介绍 XML 格式化规则、命名空间处理以及在线美化压缩工具的使用方法。",
     ["XML", "Formatter", "Web"], "初级"),
    ("markdown-editor-preview",
     "Markdown 编辑器 — 免费在线预览写作",
     "Markdown 因其简洁语法被广泛用于文档、博客和技术写作。本文介绍 Markdown 基本语法、速查表和在线编辑器使用方法，帮助快速写出格式规范的文档。",
     ["Markdown", "Editor", "Writing"], "初级"),
    ("unicode-converter-emoji",
     "Unicode 转换器 — Emoji/中日韩文字编码互转",
     "Unicode 是计算机处理人类书写文字的统一编码标准。本文介绍 Unicode 编码原理、常用转义序列以及在线转换工具的使用方法。",
     ["Unicode", "Encoding", "Web"], "初级"),
    ("jwt-claims-explained",
     "JWT Claims 详解 — 带你读懂 Token 里的每个字段",
     "JWT 的 Payload 中包含了声明（Claims），理解这些字段对于正确使用 JWT 至关重要。本文详细介绍标准声明（iss, sub, aud, exp, nbf, iat, jti）和自定义声明的用法。",
     ["JWT", "Auth", "Security"], "高级"),
    ("curl-command-builder",
     "Curl 命令在线构建器 — 可视化生成 HTTP 请求",
     "curl 是最常用的命令行 HTTP 客户端，但复杂请求的参数容易写错。本文介绍 curl 命令的各选项含义和在线构建工具的使用方法，快速生成正确的 curl 命令。",
     ["HTTP", "API", "DevTools"], "初级"),
    ("webhook-tester-online",
     "Webhook 在线测试器 — 接收调试 HTTP 回调请求",
     "Webhook 是现代微服务间事件通知的主流方式。本文介绍 Webhook 的工作原理、常用场景和在线测试工具的使用方法，方便接收和调试 HTTP 回调请求。",
     ["Webhook", "HTTP", "API"], "中级"),
]


def gh_api(path, method="GET", fields=None):
    """Call GitHub API"""
    cmd = ["gh", "api", f"repos/{REPO}/contents/{path}"]
    if method == "GET":
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    elif method == "PUT":
        cmd.extend(["--method", "PUT", "--field", f"message={fields['message']}",
                    "--field", f"content={fields['content']}"])
        if fields.get("sha"):
            cmd.extend(["--field", f"sha={fields['sha']}"])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
    elif method == "DELETE":
        cmd.extend(["--method", "DELETE", "--field", f"message={fields['message']}",
                    "--field", f"sha={fields['sha']}"])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {"success": result.returncode == 0}


def slugify(title):
    s = re.sub(r'[^\w\s-]', '', title.lower())
    return re.sub(r'[\s_]+', '-', s)[:60]


def read_json_file(path):
    data = gh_api(path)
    if not data or "content" not in data:
        return None, None
    raw = data["content"]
    decoded = base64.b64decode(raw + "==").decode("utf-8")
    return json.loads(decoded), data.get("sha", "")


def write_json_file(path, data, message):
    content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    existing = gh_api(path)
    fields = {"message": message, "content": content}
    if existing and existing.get("sha"):
        fields["sha"] = existing["sha"]
    return gh_api(path, "PUT", fields)


def generate_article(slug, title, description, tags, difficulty):
    readable = title.split("—")[0].strip()
    content_html = f"""      <h2>什么是 {readable}？</h2>
      <p>{description}</p>

      <h2>为什么开发者需要这个工具？</h2>
      <p>在日常开发中，我们经常需要处理各种数据格式转换、验证和生成任务。使用在线工具可以省去搭建本地环境的麻烦，快速得到结果，尤其适合调试和临时需求。</p>
      <p>DevUtils 提供免费、无需注册、即开即用的在线工具，帮助开发者提升效率。</p>

      <div class="tip">
        <strong>💡 提示：</strong> 收藏本页，下次需要时直接访问，无需重复搜索。
      </div>

      <h2>使用方法</h2>
      <p>直接访问 DevUtils 相应工具页面，输入你的数据，即可获得格式化的结果。所有工具都支持实时预览和批量处理。</p>

      <h2>常见使用场景</h2>
      <ul>
        <li>调试 API 响应数据</li>
        <li>快速验证数据格式是否正确</li>
        <li>团队协作时代码格式化统一</li>
        <li>本地开发时快速生成测试数据</li>
      </ul>

      <h2>相关工具推荐</h2>
      <ul>
        <li><a href="/">JSON Formatter</a> — 格式化、验证、压缩 JSON</li>
        <li><a href="/">Base64 Encoder/Decoder</a> — Base64 编解码</li>
        <li><a href="/">Timestamp Converter</a> — Unix 时间戳转换</li>
      </ul>

      <div class="ad-container">
        <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6731042234472710" data-ad-slot="" data-ad-format="auto" data-full-width-responsive="true"></ins>
      </div>

      <h2>进阶技巧</h2>
      <p>熟练使用这些工具可以大幅提升开发效率。建议关注 DevUtils 的更新，我们会持续添加新的开发者工具。</p>"""

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — DevUtils</title>
<meta name="description" content="{description[:120]}">
<meta name="keywords" content="{", ".join(tags)}">
<link rel="canonical" href="https://devutils.uk/blog/{slug}">
<meta property="og:title" content="{title} — DevUtils">
<meta property="og:description" content="{description[:120]}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://devutils.uk/blog/{slug}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6731042234472710" crossorigin="anonymous"></script>
<style>
:root {{ --bg:#0a0a0f;--surface:#12121a;--surface2:#1a1a25;--text:#e4e4e7;--text2:#a1a1aa;--text3:#71717a;--accent:#6366f1;--border:#27272a; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--text); line-height:1.7; font-size:16px; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ color:#818cf8; }}
.container {{ max-width:800px; margin:0 auto; padding:0 24px; }}
header {{ background:rgba(10,10,15,0.95); border-bottom:1px solid var(--border); padding:14px 0; position:sticky; top:0; z-index:100; backdrop-filter:blur(12px); }}
nav {{ display:flex; justify-content:space-between; align-items:center; }}
.logo {{ font-size:18px; font-weight:700; color:#fff; text-decoration:none; font-family:'JetBrains Mono',monospace; }}
.logo span {{ color:var(--accent); }}
.nav-links {{ display:flex; gap:28px; list-style:none; }}
.nav-links a {{ color:var(--text2); text-decoration:none; font-size:14px; font-weight:500; }}
.nav-links a:hover, .nav-links a.active {{ color:var(--text); }}
.nav-links a.active {{ color:var(--accent); }}
.breadcrumb {{ padding:28px 0 0; font-size:13px; color:var(--text3); }}
.breadcrumb a {{ color:var(--text3); }}
.breadcrumb span {{ margin:0 6px; }}
article {{ padding:32px 0 80px; }}
.article-header {{ margin-bottom:36px; }}
.article-header h1 {{ font-size:clamp(24px,5vw,36px); font-weight:700; line-height:1.25; margin-bottom:14px; color:#fff; }}
.article-meta {{ display:flex; gap:20px; font-size:13px; color:var(--text3); flex-wrap:wrap; align-items:center; }}
.tag {{ background:rgba(99,102,241,0.12); color:var(--accent); padding:3px 12px; border-radius:100px; font-size:12px; font-weight:500; }}
.difficulty {{ color:var(--text3); }}
.ad-container {{ margin:32px 0; padding:20px; background:var(--surface); border-radius:12px; text-align:center; border:1px solid var(--border); min-height:100px; display:flex; align-items:center; justify-content:center; color:var(--text3); font-size:13px; }}
.content {{ font-size:16px; }}
.content h2 {{ font-size:22px; font-weight:600; margin:36px 0 14px; color:#fff; }}
.content h3 {{ font-size:18px; font-weight:600; margin:24px 0 10px; color:#e4e4e7; }}
.content p {{ margin-bottom:18px; color:var(--text2); }}
.content ul, .content ol {{ margin:0 0 18px 24px; color:var(--text2); }}
.content li {{ margin-bottom:8px; }}
.content code {{ font-family:'JetBrains Mono',monospace; background:var(--surface); padding:2px 8px; border-radius:4px; font-size:14px; color:#818cf8; }}
.content pre {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; overflow-x:auto; margin:20px 0; }}
.content pre code {{ background:none; padding:0; color:#e4e4e7; font-size:14px; line-height:1.6; }}
.content table {{ width:100%; border-collapse:collapse; margin:20px 0; font-size:14px; }}
.content table th {{ background:var(--surface); padding:10px 14px; text-align:left; border:1px solid var(--border); color:#fff; font-weight:600; }}
.content table td {{ padding:10px 14px; border:1px solid var(--border); color:var(--text2); }}
.content .tip {{ background:rgba(99,102,241,0.08); border-left:3px solid var(--accent); padding:16px 20px; border-radius:0 8px 8px 0; margin:24px 0; }}
.content .tip strong {{ color:var(--accent); }}
.content .warning {{ background:rgba(234,179,8,0.08); border-left:3px solid #eab308; padding:16px 20px; border-radius:0 8px 8px 0; margin:24px 0; }}
.source-link {{ margin-top:48px; padding-top:24px; border-top:1px solid var(--border); font-size:13px; color:var(--text3); }}
footer {{ border-top:1px solid var(--border); padding:24px 0; text-align:center; font-size:13px; color:var(--text3); }}
@media(max-width:640px){{ .container{{ padding:0 16px; }} }}
</style>
</head>
<body>
<header>
  <div class="container">
    <nav>
      <a href="/" class="logo">DevUtils<span>.uk</span></a>
      <ul class="nav-links">
        <li><a href="/">Tools</a></li>
        <li><a href="/tutorials">Tutorials</a></li>
        <li><a href="/blog/" class="active">Blog</a></li>
      </ul>
    </nav>
  </div>
</header>
<div class="container">
  <div class="breadcrumb">
    <a href="/">DevUtils</a><span>›</span>
    <a href="/blog/">Blog</a><span>›</span>
    {readable}
  </div>
</div>
<article>
  <div class="container">
    <div class="article-header">
      <h1>{readable}</h1>
      <div class="article-meta">
        <span class="difficulty">{difficulty}</span>
        <span>{TODAY}</span>
        {" ".join(f'<span class="tag">{t}</span>' for t in tags)}
      </div>
    </div>
    <div class="ad-container">
      <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6731042234472710" data-ad-slot="" data-ad-format="auto" data-full-width-responsive="true"></ins>
    </div>
    <div class="content">
{content_html}
    </div>
    <div class="source-link">
      本文由 DevUtils 自动生成 · <a href="/blog/">查看更多文章</a>
    </div>
  </div>
</article>
<footer>
  <div class="container">© 2025 DevUtils.uk — Free Developer Tools</div>
</footer>
</body>
</html>'''
    return html


def update_blog_index():
    """
    Rebuild blog/index.html with all posts from _posts.json.
    Fetches the current template, replaces the blog-grid section
    with properly formatted blog-card HTML, and pushes back.
    Returns (success: bool, message: str)
    """
    import urllib.request

    # Read _posts.json
    posts_content = gh_api("blog/_posts.json")
    if not posts_content or "content" not in posts_content:
        return False, "Could not read _posts.json"

    raw = posts_content["content"]
    decoded = base64.b64decode(raw + "==").decode("utf-8")
    posts_data = json.loads(decoded)
    all_posts = posts_data.get("posts", [])

    # Read current blog/index.html template
    idx_data = gh_api("blog/index.html")
    if not idx_data or "content" not in idx_data:
        return False, "Could not read blog/index.html"

    sha = idx_data.get("sha", "")
    template = base64.b64decode(idx_data["content"] + "==").decode("utf-8")

    # Difficulty to label map
    dm = {
        '初级': 'Guide', '中级': 'Tutorial', '高级': 'Advanced',
        'Guide': 'Guide', 'Tutorial': 'Tutorial', 'Advanced': 'Advanced',
        'Reference': 'Reference', 'reference': 'Reference'
    }

    def make_card(p):
        slug = p['slug']
        title = p['title']
        desc = p.get('description', '')[:200]
        rt = p.get('readTime', '5 min').replace(' min', '').replace('min', '').strip()
        diff = p.get('difficulty', p.get('tags', ['Guide'])[0] if p.get('tags') else 'Guide')
        label = dm.get(diff, 'Guide')
        return (
            f'<a href="/blog/{slug}.html" class="blog-card">\n'
            f'                <div class="blog-card-meta">{label} · {rt} min read</div>\n'
            f'                <h2>{title}</h2>\n'
            f'                <p>{desc}</p>\n'
            f'                <span class="read-more">Read more</span>\n'
            f'            </a>'
        )

    cards_html = '\n\n'.join(make_card(p) for p in all_posts)

    # Replace blog-grid section in template
    gs = template.find('<div class="blog-grid">')
    ge = template.find('</div>', gs) + 6
    new_section = '<div class="blog-grid">\n' + cards_html + '\n            </div>'
    new_html = template[:gs] + new_section + template[ge:]

    # Push updated blog/index.html
    content_b64 = base64.b64encode(new_html.encode('utf-8')).decode()
    fields = {
        "message": f"auto: rebuild blog index with {len(all_posts)} posts [{TODAY}]",
        "content": content_b64,
    }
    if sha:
        fields["sha"] = sha

    result = gh_api("blog/index.html", "PUT", fields)
    if "error" in result:
        return False, result["error"]
    return True, f"Updated blog/index.html with {len(all_posts)} posts"


def update_posts_json(post):
    """Add a new post to blog/_posts.json"""
    data, sha = read_json_file("blog/_posts.json")
    if data is None:
        data = {"posts": [], "lastUpdated": TODAY}

    # Dedupe by slug
    existing_slugs = {p["slug"] for p in data["posts"]}
    if post["slug"] not in existing_slugs:
        data["posts"].insert(0, post)
        data["lastUpdated"] = TODAY
        content_b64 = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
        fields = {
            "message": f"auto: add {post['slug']} to blog posts [{TODAY}]",
            "content": content_b64,
        }
        if sha:
            fields["sha"] = sha
        return gh_api("blog/_posts.json", "PUT", fields)
    return {"skipped": True}


def main():
    # Load already-generated tracker
    tracker, tracker_sha = read_json_file("scripts/_generated_posts.json")
    if tracker is None:
        tracker = {"generated": [], "last_updated": TODAY}
    generated_slugs = set(tracker.get("generated", []))

    # Find next topic to generate
    topic = None
    topic_idx = None
    for i, t in enumerate(SEO_TOPICS):
        slug = t[0]
        if slug not in generated_slugs:
            topic = t
            topic_idx = i
            break

    if topic is None:
        print("All topics already generated!")
        # Reset and start from beginning
        tracker["generated"] = []
        generated_slugs = set()
        topic = SEO_TOPICS[0]
        topic_idx = 0

    slug, title, description, tags, difficulty = topic
    print(f"Generating article {topic_idx+1}/{len(SEO_TOPICS)}: {slug}")

    # Generate and push article HTML
    html = generate_article(slug, title, description, tags, difficulty)
    content_b64 = base64.b64encode(html.encode("utf-8")).decode()

    existing = gh_api(f"blog/{slug}.html")
    fields = {
        "message": f"auto: add SEO article {slug} [{TODAY}]",
        "content": content_b64,
    }
    if existing and existing.get("sha"):
        fields["sha"] = existing["sha"]

    result = gh_api(f"blog/{slug}.html", "PUT", fields)
    if "error" in result:
        print(f"Failed to push article: {result['error']}")
        sys.exit(1)
    print(f"✅ Pushed blog/{slug}.html")

    # Mark as generated
    tracker["generated"].append(slug)
    tracker["last_updated"] = TODAY

    # Update tracker file
    write_json_file(
        "scripts/_generated_posts.json",
        tracker,
        f"auto: update generated posts tracker [{TODAY}]"
    )

    # Update _posts.json (not index.html)
    post_meta = {
        "slug": slug,
        "title": title.split("—")[0].strip(),
        "description": description[:120],
        "date": TODAY,
        "tags": tags,
        "readTime": "5 min",
        "url": f"/blog/{slug}.html",
        "tool": title.split("—")[0].strip(),
    }
    result = update_posts_json(post_meta)
    print(f"{'✅' if 'error' not in result else '❌'} Updated _posts.json")

    # Update blog/index.html with all posts (blog-card HTML)
    idx_ok, idx_msg = update_blog_index()
    print(f"{'✅' if idx_ok else '❌'} {idx_msg}")

    print(f"\nDone! Generated: {title.split('—')[0].strip()}")


if __name__ == "__main__":
    main()
