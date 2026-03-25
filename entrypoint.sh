#!/bin/sh
set -e

cd /app

# Create logs directory if it doesn't exist
mkdir -p logs

python manage.py migrate

if [ "${INIT_IMPORT_FRONTEND_TRANSLATIONS:-0}" = "1" ]; then
  if [ -z "${FRONTEND_LOCALES_DIR:-}" ]; then
    echo "INIT_IMPORT_FRONTEND_TRANSLATIONS=1 but FRONTEND_LOCALES_DIR is not set. Skipping."
  elif [ ! -d "${FRONTEND_LOCALES_DIR}" ]; then
    echo "Locales directory '${FRONTEND_LOCALES_DIR}' does not exist. Skipping import."
  else
    if [ "${INIT_IMPORT_OVERWRITE:-1}" = "1" ] && [ "${INIT_IMPORT_ONLY_IF_EMPTY:-1}" = "1" ]; then
      python manage.py import_frontend_translations \
        --locales-dir "${FRONTEND_LOCALES_DIR}" \
        --source-lang "${FRONTEND_SOURCE_LANG:-cs}" \
        --overwrite \
        --if-empty
    elif [ "${INIT_IMPORT_OVERWRITE:-1}" = "1" ]; then
      python manage.py import_frontend_translations \
        --locales-dir "${FRONTEND_LOCALES_DIR}" \
        --source-lang "${FRONTEND_SOURCE_LANG:-cs}" \
        --overwrite
    elif [ "${INIT_IMPORT_ONLY_IF_EMPTY:-1}" = "1" ]; then
      python manage.py import_frontend_translations \
        --locales-dir "${FRONTEND_LOCALES_DIR}" \
        --source-lang "${FRONTEND_SOURCE_LANG:-cs}" \
        --if-empty
    else
      python manage.py import_frontend_translations \
        --locales-dir "${FRONTEND_LOCALES_DIR}" \
        --source-lang "${FRONTEND_SOURCE_LANG:-cs}"
    fi
  fi
fi

if [ "${INIT_SYNC_PHOTOS_FROM_MEDIA:-0}" = "1" ]; then
  if [ "${INIT_SYNC_PHOTOS_ONLY_IF_EMPTY:-0}" = "1" ]; then
    python manage.py sync_photos_from_media --photos-dir "${MEDIA_PHOTOS_DIR:-/app/media/editorial/photos}" --if-empty
  else
    python manage.py sync_photos_from_media --photos-dir "${MEDIA_PHOTOS_DIR:-/app/media/editorial/photos}"
  fi
fi

exec "$@"
