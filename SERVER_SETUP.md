# Инструкция по развертыванию на сервере

## Шаг 1: Подключение к серверу и переход в директорию проекта

```bash
cd /root/Flo/Flo
```

## Шаг 2: Сохранение локальных изменений (если есть)

Если на сервере есть локальные изменения, которые конфликтуют с GitHub:

```bash
# Вариант 1: Сохранить изменения в stash
git stash

# Вариант 2: Отменить все локальные изменения (ОСТОРОЖНО!)
git reset --hard HEAD
```

## Шаг 3: Получение последних изменений из GitHub

```bash
git pull origin main
```

## Шаг 4: Очистка базы данных (если были проблемы с миграциями)

Если контейнер `flo_app` постоянно перезапускается из-за ошибок миграций:

```bash
# Остановить все контейнеры
docker-compose down

# Удалить volume с данными PostgreSQL (ОСТОРОЖНО: удалит все данные!)
docker volume rm flo_postgres_data

# Или если volume называется по-другому, найти его:
docker volume ls | grep postgres

# Удалить найденный volume:
docker volume rm <имя_volume>
```

## Шаг 5: Пересборка Docker образа приложения

```bash
# Пересобрать образ с новым кодом
docker-compose build app

# Или пересобрать все сервисы
docker-compose build
```

## Шаг 6: Запуск всех сервисов

```bash
# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

## Шаг 7: Проверка логов

```bash
# Проверить логи приложения
docker-compose logs app --tail 50

# Проверить логи всех сервисов
docker-compose logs --tail 50

# Следить за логами в реальном времени
docker-compose logs -f app
```

## Шаг 8: Проверка работоспособности

```bash
# Проверить health endpoint
curl http://localhost:8000/health

# Проверить статус контейнеров
docker-compose ps

# Все контейнеры должны быть в статусе "Up" и "healthy"
```

## Шаг 9: Если контейнер все еще перезапускается

### Проверка ошибок миграций:

```bash
# Проверить текущую версию миграций в базе
docker-compose exec postgres psql -U flo_user -d flo_db -c "SELECT * FROM alembic_version;"
```

### Полная очистка и перезапуск:

```bash
# 1. Остановить все
docker-compose down

# 2. Удалить volume с базой данных
docker volume rm flo_postgres_data

# 3. Пересобрать образ
docker-compose build app

# 4. Запустить заново
docker-compose up -d

# 5. Проверить логи
docker-compose logs app --tail 100
```

## Шаг 10: Настройка webhook для Telegram бота (если нужно)

Если используете webhook вместо polling:

```bash
# Убедитесь, что в .env файле указан правильный WEBHOOK_URL
# Например: WEBHOOK_URL=https://yourdomain.com

# Установить webhook (выполнить внутри контейнера или локально с установленным python-telegram-bot)
docker-compose exec app python -c "
from telegram import Bot
import os
bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
bot.set_webhook(url=f\"{os.environ['WEBHOOK_URL']}/telegram/webhook\")
print('Webhook установлен')
"
```

## Проверка переменных окружения

Убедитесь, что файл `.env` содержит все необходимые переменные:

```bash
cat .env
```

Должны быть указаны:
- `TELEGRAM_BOT_TOKEN` - токен бота
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - настройки БД
- `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` - настройки YooKassa
- `WEBHOOK_URL` - URL для webhook (если используется)
- `WEBHOOK_SECRET` - секрет для webhook (если используется)

## Типичные проблемы и решения

### Проблема: Контейнер `flo_app` постоянно перезапускается

**Решение:**
1. Проверьте логи: `docker-compose logs app --tail 100`
2. Если ошибка миграций - очистите базу данных (см. Шаг 4)
3. Если ошибка подключения к БД - проверьте, что контейнер `flo_postgres` запущен и healthy

### Проблема: Ошибка "type paymentstatus already exists"

**Решение:**
- Это исправлено в новой версии миграции
- Выполните Шаг 4 (очистка БД) и перезапустите

### Проблема: Ошибка "cannot import name 'fileconfig'"

**Решение:**
- Это исправлено в `alembic/env.py`
- Убедитесь, что выполнили `git pull` и пересобрали образ

### Проблема: Бот не отвечает

**Решение:**
1. Проверьте, что контейнер `flo_app` работает: `docker-compose ps`
2. Проверьте логи: `docker-compose logs app`
3. Проверьте токен бота в `.env`
4. Если используете webhook - проверьте, что он установлен правильно

## Команды для быстрого перезапуска

```bash
# Быстрый перезапуск приложения
docker-compose restart app

# Полный перезапуск всех сервисов
docker-compose restart

# Пересборка и перезапуск
docker-compose up -d --build app
```

## Мониторинг

```bash
# Статус всех контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи в реальном времени
docker-compose logs -f
```

