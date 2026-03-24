#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/luciescholzova/PycharmProjects/LidmanoviProject"
cd "$PROJECT_DIR"

LOCALES_DIR="${LOCALES_DIR:-/app/tmp/locales}"
SOURCE_LANG="${SOURCE_LANG:-cs}"
OVERWRITE="${OVERWRITE:-0}"
IF_EMPTY="${IF_EMPTY:-0}"

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$TIMESTAMP] import_frontend_translations cron started"

CMD=(docker compose exec -T backend python manage.py import_frontend_translations --locales-dir "$LOCALES_DIR" --source-lang "$SOURCE_LANG")
if [[ "$OVERWRITE" == "1" ]]; then
  CMD+=(--overwrite)
fi
if [[ "$IF_EMPTY" == "1" ]]; then
  CMD+=(--if-empty)
fi

"${CMD[@]}"

TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
echo "[$TIMESTAMP] import_frontend_translations cron finished"
