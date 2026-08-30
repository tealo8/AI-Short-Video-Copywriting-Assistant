#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose down
echo "已停止并移除全部容器"
