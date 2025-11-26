# Быстрый старт FL0 Hack Bot

## Предварительные требования

1. Docker и Docker Compose установлены
2. Telegram Bot Token от [@BotFather](https://t.me/BotFather)
3. Аккаунт в [YooKassa](https://yookassa.ru/) с Shop ID и Secret Key

## Шаги запуска

### 1. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
# Database
POSTGRES_USER=fl0_user
POSTGRES_PASSWORD=fl0_password
POSTGRES_DB=fl0_db
DATABASE_URL=postgresql://fl0_user:fl0_password@postgres:5432/fl0_db

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram (обязательно)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# YooKassa (обязательно)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# Webhook (для production)
WEBHOOK_URL=https://your-domain.com
WEBHOOK_SECRET=your_webhook_secret
```

### 2. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит все необходимые сервисы:
- PostgreSQL (порт 5432)
- Redis (порт 6379)
- Приложение (порт 8000)
- Nginx (порты 80/443)

### 3. Проверка работы

Проверьте статус контейнеров:

```bash
docker-compose ps
```

Проверьте логи:

```bash
docker-compose logs app
```

Проверьте health endpoint:

```bash
curl http://localhost:8000/health
```

### 4. Тестирование бота

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Отправьте номер телефона в формате `+7XXXXXXXXXX`
4. Следуйте инструкциям для оплаты

## Настройка webhook'ов (для production)

### Telegram Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/webhook/telegram"
```

### YooKassa Webhook

Настройте в личном кабинете YooKassa:
- URL: `https://your-domain.com/webhook/yookassa`
- События: `payment.succeeded`

## Локальная разработка

### Без Docker

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Запустите PostgreSQL и Redis (через Docker или локально):
```bash
docker-compose up -d postgres redis
```

3. Настройте `.env` с локальными URL:
```bash
DATABASE_URL=postgresql://fl0_user:fl0_password@localhost:5432/fl0_db
REDIS_URL=redis://localhost:6379/0
```

4. Примените миграции:
```bash
alembic upgrade head
```

5. Запустите приложение:
```bash
python -m src.presentation.bot.main
```

## Отладка

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только приложение
docker-compose logs -f app

# Только база данных
docker-compose logs -f postgres
```

### Подключение к базе данных

```bash
docker-compose exec postgres psql -U fl0_user -d fl0_db
```

### Подключение к Redis

```bash
docker-compose exec redis redis-cli
```

## Остановка

```bash
docker-compose down
```

Для удаления всех данных (включая базу):

```bash
docker-compose down -v
```

## Troubleshooting

### Проблема: Бот не отвечает

- Проверьте `TELEGRAM_BOT_TOKEN` в `.env`
- Проверьте логи: `docker-compose logs app`
- Убедитесь, что бот запущен: `docker-compose ps`

### Проблема: Ошибки подключения к БД

- Убедитесь, что PostgreSQL запущен: `docker-compose ps postgres`
- Проверьте `DATABASE_URL` в `.env`
- Проверьте логи: `docker-compose logs postgres`

### Проблема: Миграции не применяются

- Проверьте подключение к БД
- Запустите миграции вручную: `docker-compose exec app alembic upgrade head`

### Проблема: Платежи не проходят

- Проверьте `YOOKASSA_SHOP_ID` и `YOOKASSA_SECRET_KEY`
- Убедитесь, что webhook URL настроен правильно
- Проверьте логи: `docker-compose logs app`

