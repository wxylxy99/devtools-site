#!/usr/bin/env bash
# deploy.sh — 采集 → 生成教程 → 提交 GitHub → 触发 Cloudflare Pages 自动部署
# 用法: ./scripts/deploy.sh

set -euo pipefail

SITE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SITE_DIR"

echo "=== DevUtils.uk Deploy ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Step 1: Run collector
echo "[1/4] Running tutorials collector..."
python3 scripts/collect_tutorials.py

# Step 2: Generate tutorial pages
echo ""
echo "[2/4] Generating tutorial HTML pages..."
python3 scripts/generate_tutorials.py

# Step 3: Git commit
echo ""
echo "[3/4] Git commit & push..."
git add tutorials/ _data.json 2>/dev/null || true

if git diff --cached --quiet; then
  echo "  → No changes to commit"
else
  git commit -m "tutorials: auto-update $(date -u '+%Y-%m-%d %H:%M')"
  git push origin main
  echo "  ✓ Pushed to GitHub"
fi

# Step 4: Cloudflare Pages deploy (via wrangler)
# Note: This is automatic if GitHub integration is set up in Cloudflare dashboard
# The GitHub push will trigger Pages automatically
echo ""
echo "[4/4] Cloudflare Pages..."
echo "  → GitHub integration will auto-deploy (no manual wrangler needed)"
echo ""
echo "=== Deploy Complete ==="
