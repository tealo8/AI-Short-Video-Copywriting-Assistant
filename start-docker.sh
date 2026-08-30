#!/usr/bin/env bash
# AI 内容工场 Docker 一键部署（macOS / Linux）
set -e
cd "$(dirname "$0")"
echo "============================================================"
echo "   AI 内容工场 · Docker 一键部署"
echo "============================================================"
docker compose up -d --build
echo "[完成] 前端: http://localhost   后端API: http://localhost:8000/docs"
