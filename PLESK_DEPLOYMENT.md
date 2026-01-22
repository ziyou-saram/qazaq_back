# Деплой FastAPI на Plesk

## Предварительные требования

- Plesk Obsidian 18.0.45 или выше
- Python 3.12 (установлен через Plesk Extensions)
- PostgreSQL (можно установить через Plesk)
- SSH доступ к серверу
- Домен или поддомен (например, `api.yourdomain.com`)

---

## Шаг 1: Подготовка Plesk

### 1.1 Установка Python 3.12

1. Войдите в Plesk панель
2. Перейдите в **Extensions** → **My Extensions**
3. Найдите и установите **Python** extension
4. После установки, перейдите в **Tools & Settings** → **Updates**
5. Убедитесь, что Python 3.12 доступен

### 1.2 Создание базы данных PostgreSQL

1. Перейдите в **Databases** → **Add Database**
2. Создайте базу данных:
   - Database name: `qazaq`
   - Database user: `qazaq`
   - Password: (создайте надежный пароль)
3. Запомните данные подключения

### 1.3 Создание домена/поддомена

1. Перейдите в **Domains** → **Add Domain** (или **Add Subdomain**)
2. Создайте домен: `api.yourdomain.com`
3. Выберите **Document root**: `/var/www/vhosts/yourdomain.com/api.yourdomain.com`

---

## Шаг 2: Загрузка кода на сервер

### Вариант A: Через Git (Рекомендуется)

1. Подключитесь по SSH:
   ```bash
   ssh your-user@your-server-ip
   ```

2. Перейдите в директорию домена:
   ```bash
   cd /var/www/vhosts/yourdomain.com/api.yourdomain.com
   ```

3. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/qazaq-platform.git .
   cd backend
   ```

### Вариант B: Через FTP/SFTP

1. Используйте FileZilla или другой FTP клиент
2. Подключитесь к серверу
3. Загрузите все файлы из папки `backend` в `/var/www/vhosts/yourdomain.com/api.yourdomain.com/`

---

## Шаг 3: Настройка Python окружения

### 3.1 Создание виртуального окружения

```bash
cd /var/www/vhosts/yourdomain.com/api.yourdomain.com

# Создание venv
python3.12 -m venv venv

# Активация
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

### 3.2 Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## Шаг 4: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
nano .env
```

Добавьте следующие переменные:

```bash
# Database
DATABASE_URL=postgresql://qazaq:YOUR_DB_PASSWORD@localhost:5432/qazaq

# JWT
SECRET_KEY=your-super-secret-key-min-32-chars-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=qazaq
AWS_REGION=eu-north-1

# App
PROJECT_NAME=Qazaq Platform
VERSION=1.0.0
ENVIRONMENT=production
UPLOAD_DIR=/var/www/vhosts/qazaq.kz/api.qazaq.kz/uploads
```

Сохраните файл (Ctrl+X, Y, Enter)

---

## Шаг 5: Инициализация базы данных

```bash
# Применить миграции
alembic upgrade head

# Создать начальные данные (admin, категории)
python -c "from app.db.init_db import init_db; init_db()"

# Опционально: добавить тестовый контент
python -c "from app.db.seed_content import seed_content; seed_content()"
```

---

## Шаг 6: Настройка Passenger (WSGI сервер в Plesk)

### 6.1 Создание файла `passenger_wsgi.py`

В корне проекта создайте файл:

```bash
nano passenger_wsgi.py
```

Добавьте следующий код:

```python
import sys
import os

# Путь к вашему проекту
INTERP = "/var/www/vhosts/yourdomain.com/api.yourdomain.com/venv/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Добавляем путь к проекту
sys.path.insert(0, '/var/www/vhosts/yourdomain.com/api.yourdomain.com')

# Импортируем приложение
from app.main import app as application
```

### 6.2 Настройка в Plesk панели

1. Перейдите в **Domains** → выберите ваш домен `api.yourdomain.com`
2. Нажмите **Apache & nginx Settings**
3. Включите **Python** support
4. Укажите:
   - **Application root**: `/var/www/vhosts/yourdomain.com/api.yourdomain.com`
   - **Application URL**: `/` (или `/api` если хотите)
   - **Application startup file**: `passenger_wsgi.py`
   - **Python version**: 3.12

5. В секции **Additional directives for HTTP** добавьте:
   ```
   PassengerPython /var/www/vhosts/yourdomain.com/api.yourdomain.com/venv/bin/python3
   ```

6. Нажмите **OK**

---

## Шаг 7: Настройка Nginx (альтернатива Passenger)

Если Passenger не работает, используйте Nginx + Gunicorn:

### 7.1 Установка Gunicorn

```bash
pip install gunicorn
```

### 7.2 Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/qazaq-backend.service
```

Добавьте:

```ini
[Unit]
Description=Qazaq Platform Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/yourdomain.com/api.yourdomain.com
Environment="PATH=/var/www/vhosts/yourdomain.com/api.yourdomain.com/venv/bin"
ExecStart=/var/www/vhosts/yourdomain.com/api.yourdomain.com/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

### 7.3 Запуск сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl start qazaq-backend
sudo systemctl enable qazaq-backend
sudo systemctl status qazaq-backend
```

### 7.4 Настройка Nginx в Plesk

1. Перейдите в **Apache & nginx Settings** для вашего домена
2. В секции **Additional nginx directives** добавьте:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

3. Нажмите **OK**

---

## Шаг 8: Настройка SSL (HTTPS)

1. В Plesk перейдите в **SSL/TLS Certificates**
2. Выберите **Let's Encrypt**
3. Нажмите **Install** для вашего домена
4. Включите **Redirect from HTTP to HTTPS**

---

## Шаг 9: Проверка работы

### 9.1 Проверка API

Откройте в браузере:
- `https://api.yourdomain.com/docs` - должна открыться Swagger документация
- `https://api.yourdomain.com/public/categories` - должен вернуть JSON с категориями

### 9.2 Проверка логов

```bash
# Логи Passenger
tail -f /var/www/vhosts/yourdomain.com/logs/error_log

# Логи Gunicorn (если используете)
sudo journalctl -u qazaq-backend -f
```

---

## Шаг 10: Автоматическое обновление (CI/CD)

### Создание скрипта обновления

```bash
nano /var/www/vhosts/yourdomain.com/api.yourdomain.com/deploy.sh
```

Добавьте:

```bash
#!/bin/bash

cd /var/www/vhosts/yourdomain.com/api.yourdomain.com

# Получить последние изменения
git pull origin main

# Активировать venv
source venv/bin/activate

# Обновить зависимости
pip install -r requirements.txt

# Применить миграции
alembic upgrade head

# Перезапустить сервис
if [ -f "/etc/systemd/system/qazaq-backend.service" ]; then
    sudo systemctl restart qazaq-backend
else
    # Для Passenger
    touch tmp/restart.txt
fi

echo "Deployment completed!"
```

Сделайте скрипт исполняемым:

```bash
chmod +x deploy.sh
```

Теперь для обновления просто запускайте:

```bash
./deploy.sh
```

---

## Troubleshooting

### Проблема: 502 Bad Gateway

**Решение:**
```bash
# Проверьте статус сервиса
sudo systemctl status qazaq-backend

# Проверьте логи
sudo journalctl -u qazaq-backend -n 50
```

### Проблема: Permission denied

**Решение:**
```bash
# Установите правильные права
sudo chown -R www-data:www-data /var/www/vhosts/yourdomain.com/api.yourdomain.com
sudo chmod -R 755 /var/www/vhosts/yourdomain.com/api.yourdomain.com
```

### Проблема: Database connection error

**Решение:**
- Проверьте `DATABASE_URL` в `.env`
- Убедитесь что PostgreSQL запущен: `sudo systemctl status postgresql`
- Проверьте права доступа к базе данных

### Проблема: S3 upload не работает

**Решение:**
- Проверьте AWS credentials в `.env`
- Убедитесь что bucket policy настроен правильно
- Проверьте логи на ошибки от AWS

---

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Логи приложения
tail -f /var/www/vhosts/yourdomain.com/logs/error_log

# Логи systemd сервиса
sudo journalctl -u qazaq-backend -f
```

### Резервное копирование базы данных

```bash
# Создать бэкап
pg_dump -U qazaq qazaq > backup_$(date +%Y%m%d).sql

# Восстановить из бэкапа
psql -U qazaq qazaq < backup_20260122.sql
```

### Автоматический бэкап (cron)

```bash
crontab -e
```

Добавьте:
```
0 2 * * * pg_dump -U qazaq qazaq > /var/backups/qazaq_$(date +\%Y\%m\%d).sql
```

---

## Чеклист после деплоя

- [ ] API доступен по HTTPS
- [ ] Swagger документация работает (`/docs`)
- [ ] База данных инициализирована
- [ ] Admin пользователь создан
- [ ] S3 загрузка работает
- [ ] CORS настроен правильно
- [ ] SSL сертификат установлен
- [ ] Логи доступны и читаемы
- [ ] Резервное копирование настроено
- [ ] Обновлен URL API на фронтенде

---

Готово! Ваш бэкенд теперь работает на Plesk 🚀
