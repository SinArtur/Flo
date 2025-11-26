# Инструкция по развертыванию на сервере

## Обновление проекта на сервере через Git

### Быстрое обновление (рекомендуется)

Если на сервере нет локальных изменений, которые нужно сохранить:

```bash
# 1. Перейти в директорию проекта
cd /root/FL0/FL0

# 2. Получить последние изменения из GitHub
git fetch origin

# 3. Переключиться на ветку main (если не на ней)
git checkout main

# 4. Обновить код до последней версии
git pull origin main

# 5. Пересобрать Docker образ с новым кодом
docker-compose build app

# 6. Перезапустить контейнеры
docker-compose up -d

# 7. Проверить логи на наличие ошибок
docker-compose logs app --tail 50
```

### Обновление с сохранением локальных изменений

Если на сервере есть локальные изменения, которые нужно сохранить:

```bash
# 1. Перейти в директорию проекта
cd /root/FL0/FL0

# 2. Сохранить локальные изменения во временное хранилище
git stash

# 3. Получить последние изменения из GitHub
git pull origin main

# 4. Применить сохраненные изменения обратно (если нужно)
git stash pop

# 5. Если есть конфликты, разрешите их вручную
# Затем пересоберите и перезапустите:
docker-compose build app
docker-compose up -d
```

### Обновление с отменой локальных изменений

**ВНИМАНИЕ:** Это удалит все локальные изменения на сервере!

```bash
# 1. Перейти в директорию проекта
cd /root/FL0/FL0

# 2. Отменить все локальные изменения
git reset --hard HEAD

# 3. Очистить неотслеживаемые файлы (опционально)
git clean -fd

# 4. Получить последние изменения из GitHub
git pull origin main

# 5. Пересобрать и перезапустить
docker-compose build app
docker-compose up -d
```

### Проверка статуса перед обновлением

Перед обновлением полезно проверить текущее состояние:

```bash
# Проверить статус git репозитория
git status

# Посмотреть последние коммиты
git log --oneline -10

# Посмотреть, какие изменения будут получены
git fetch origin
git log HEAD..origin/main --oneline
```

## Настройка API платежной системы (YooKassa)

### Шаг 1: Получение учетных данных YooKassa

1. Зарегистрируйтесь на [YooKassa](https://yookassa.ru/)
2. Перейдите в личный кабинет → Настройки → API
3. Скопируйте следующие данные:
   - **Shop ID** (ID магазина)
   - **Secret Key** (Секретный ключ)

### Шаг 2: Настройка переменных окружения на сервере

Подключитесь к серверу и отредактируйте файл `.env`:

```bash
# Перейти в директорию проекта
cd /root/FL0/FL0

# Открыть файл .env для редактирования
nano .env
# или
vi .env
```

Добавьте или обновите следующие переменные:

```env
# YooKassa Payment Gateway
YOOKASSA_SHOP_ID=ваш_shop_id_здесь
YOOKASSA_SECRET_KEY=ваш_secret_key_здесь

# Webhook URL для платежей (должен быть доступен из интернета)
WEBHOOK_URL=https://ваш_домен.com
WEBHOOK_SECRET=ваш_секретный_ключ_для_вебхуков
```

**Важно:**
- `YOOKASSA_SHOP_ID` и `YOOKASSA_SECRET_KEY` - обязательные параметры
- `WEBHOOK_URL` - должен быть публично доступным HTTPS URL
- `WEBHOOK_SECRET` - используйте случайную строку для безопасности

### Шаг 3: Настройка Webhook в личном кабинете YooKassa

1. Войдите в личный кабинет YooKassa
2. Перейдите в **Настройки** → **HTTP-уведомления**
3. Добавьте URL для webhook:
   ```
   https://ваш_домен.com/webhook/yookassa
   ```
4. Выберите события для уведомлений:
   - ✅ `payment.succeeded` - платеж успешно завершен
   - ✅ `payment.canceled` - платеж отменен
   - ✅ `refund.succeeded` - возврат успешно выполнен

### Шаг 4: Проверка конфигурации

После настройки переменных окружения:

```bash
# Перезапустить контейнеры для применения новых переменных
docker-compose down
docker-compose up -d

# Проверить логи на наличие ошибок
docker-compose logs app --tail 50

# Проверить, что переменные окружения загружены правильно
docker-compose exec app env | grep YOOKASSA
```

Должны отобразиться:
- `YOOKASSA_SHOP_ID=ваш_shop_id`
- `YOOKASSA_SECRET_KEY=ваш_secret_key`

### Шаг 5: Тестирование платежной системы

#### Тестовый режим YooKassa

YooKassa предоставляет тестовые карты для проверки:

**Успешный платеж:**
- Номер карты: `5555 5555 5555 4444`
- Срок действия: любая будущая дата (например, `12/25`)
- CVC: любой трехзначный код (например, `123`)

**Отклоненный платеж:**
- Номер карты: `5555 5555 5555 4477`

#### Проверка работы webhook

1. Создайте тестовый платеж через бота
2. Проверьте логи webhook:
   ```bash
   docker-compose logs app | grep -i yookassa
   ```
3. Проверьте статус платежа в личном кабинете YooKassa

### Шаг 6: Переход в боевой режим

После успешного тестирования:

1. В личном кабинете YooKassa переключитесь с **Тестового** на **Боевой** режим
2. Убедитесь, что используете боевые `YOOKASSA_SHOP_ID` и `YOOKASSA_SECRET_KEY`
3. Обновите переменные окружения на сервере
4. Перезапустите контейнеры:
   ```bash
   docker-compose restart app
   ```

## Шаг 1: Подключение к серверу и переход в директорию проекта

```bash
cd /root/FL0/FL0
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

Если контейнер `fl0_app` постоянно перезапускается из-за ошибок миграций:

```bash
# Остановить все контейнеры
docker-compose down

# Удалить volume с данными PostgreSQL (ОСТОРОЖНО: удалит все данные!)
docker volume rm fl0_postgres_data

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
docker-compose exec postgres psql -U fl0_user -d fl0_db -c "SELECT * FROM alembic_version;"
```

### Полная очистка и перезапуск:

```bash
# 1. Остановить все
docker-compose down

# 2. Удалить volume с базой данных
docker volume rm fl0_postgres_data

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

### Проблема: Контейнер `fl0_app` постоянно перезапускается

**Решение:**
1. Проверьте логи: `docker-compose logs app --tail 100`
2. Если ошибка миграций - очистите базу данных (см. Шаг 4)
3. Если ошибка подключения к БД - проверьте, что контейнер `fl0_postgres` запущен и healthy

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
1. Проверьте, что контейнер `fl0_app` работает: `docker-compose ps`
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

