import sys
import os

# ВАЖНО: Измените путь на ваш реальный путь на сервере
INTERP = "/var/www/vhosts/qazaq.kz/api.qazaq.kz/venv/bin/python3"
PROJECT_PATH = "/var/www/vhosts/qazaq.kz/api.qazaq.kz"

# Переключаемся на интерпретатор из venv
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Добавляем путь к проекту в sys.path
sys.path.insert(0, PROJECT_PATH)

# Загружаем переменные окружения из .env
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_PATH, '.env'))

# Импортируем FastAPI приложение
from app.main import app as application

# Passenger будет использовать переменную 'application'
