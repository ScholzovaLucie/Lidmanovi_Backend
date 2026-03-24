#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/luciescholzova/PycharmProjects/LidmanoviProject"
CRON_FILE="$PROJECT_DIR/deploy/cron/import_frontend_translations.cron"
TMP_FILE="$(mktemp)"

# Keep existing entries, remove old import_frontend_translations job, then append fresh one.
crontab -l 2>/dev/null | grep -v 'cron_import_frontend_translations.sh' > "$TMP_FILE" || true
cat "$CRON_FILE" >> "$TMP_FILE"
crontab "$TMP_FILE"
rm -f "$TMP_FILE"

echo "Cron installed/updated:"
crontab -l | grep 'cron_import_frontend_translations.sh' || true
