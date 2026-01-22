#!/bin/bash

# Скрипт для автоматического деплоя на Plesk
# Использование: ./deploy.sh

set -e  # Остановить при ошибке

echo "🚀 Starting deployment..."

# Переход в директорию проекта
cd "$(dirname "$0")"

# Получить последние изменения из Git
echo "📥 Pulling latest changes from Git..."
git pull origin main

# Активировать виртуальное окружение
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Обновить зависимости
echo "📦 Installing dependencies..."
pip install -r requirements.txt --upgrade

# Применить миграции базы данных
echo "🗄️ Running database migrations..."
alembic upgrade head

# Перезапустить приложение
echo "🔄 Restarting application..."

# Проверяем, используется ли systemd сервис
if [ -f "/etc/systemd/system/qazaq-backend.service" ]; then
    echo "Using systemd service..."
    sudo systemctl restart qazaq-backend
    sudo systemctl status qazaq-backend --no-pager
else
    # Для Passenger - создаем файл restart.txt
    echo "Using Passenger..."
    mkdir -p tmp
    touch tmp/restart.txt
fi

echo "✅ Deployment completed successfully!"
echo "📊 Check logs: tail -f /var/www/vhosts/yourdomain.com/logs/error_log"
