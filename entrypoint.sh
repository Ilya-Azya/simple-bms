#!/bin/sh

set -e

echo "🔄 Применяем миграции..."
python manage.py migrate --noinput

echo "⚙️ Собираем статические файлы..."
python manage.py collectstatic --noinput

echo "🚀 Запускаем сервер..."
python manage.py runserver 0.0.0.0:8000
