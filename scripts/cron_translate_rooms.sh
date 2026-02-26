#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/luciescholzova/PycharmProjects/LidmanoviProject"
cd "$PROJECT_DIR"

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$TIMESTAMP] translate_rooms cron started"

# Uses local/manual dictionary (no external API cost/limits).
docker compose exec -T backend python manage.py translate_rooms --target en --engine manual

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$TIMESTAMP] translate_rooms cron finished"
