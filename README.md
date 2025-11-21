# Flo Hack Telegram Bot

Telegram-бот, который позиционируется как сервис "хакеров", взломавших приложение Flo. За 50 рублей пользователь может "узнать данные о дате овуляции" любой девушки по номеру ее телефона.

## Архитектура

Проект построен на принципах Clean Architecture:

```
src/
├── core/                    # Бизнес-логика
│   ├── entities/           # Доменные сущности
│   ├── use_cases/          # Use cases
│   └── interfaces/         # Абстракции репозиториев
├── infrastructure/         # Внешние зависимости
│   ├── database/           # SQLAlchemy модели и репозитории
│   ├── payment_gateway/    # Адаптер ЮKassa
│   ├── telegram_bot/       # Обработчики Telegram
│   └── redis/              # Redis клиент
├── presentation/           # Слой представления
│   ├── bot/               # FastAPI приложение
│   └── webhooks/          # Webhook обработчики
└── config/                # Конфигурация
```

## Технологический стек

- **Python 3.11+**
- **FastAPI** - веб-фреймворк
- **python-telegram-bot** - Telegram Bot API
- **PostgreSQL** - база данных
- **SQLAlchemy 2.0** - ORM
- **Alembic** - миграции
- **Redis** - кеширование и rate limiting
- **YooKassa** - платежный шлюз
- **Docker** - контейнеризация

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Flo-hack
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

Обязательные переменные:
- `TELEGRAM_BOT_TOKEN` - токен бота от @BotFather
- `YOOKASSA_SHOP_ID` - ID магазина в ЮKassa
- `YOOKASSA_SECRET_KEY` - секретный ключ ЮKassa
- `WEBHOOK_URL` - URL для webhook'ов (например, `https://your-domain.com`)
- `WEBHOOK_SECRET` - секрет для подписи webhook'ов

### 3. Запуск через Docker Compose

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL на порту 5432
- Redis на порту 6379
- Приложение на порту 8000
- Nginx на портах 80/443

### 4. Применение миграций

Миграции применяются автоматически при запуске контейнера. Если нужно применить вручную:

```bash
docker-compose exec app alembic upgrade head
```

## Разработка

### Локальная разработка

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Запустите PostgreSQL и Redis локально или через Docker:

```bash
docker-compose up -d postgres redis
```

3. Настройте `.env` файл

4. Примените миграции:

```bash
alembic upgrade head
```

5. Запустите приложение:

```bash
python -m src.presentation.bot.main
```

### Создание миграций

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

## Алгоритм расчета даты овуляции

Система создает детерминированные данные на основе номера телефона:

1. **Первый запрос**: рассчитывается дата в ближайшие 2 недели
   - Формула: `hash(номер_телефона + текущий_месяц) % 14 + 1` дней от текущей даты

2. **Последующие запросы**: тот же результат, пока не наступит рассчитанная дата

3. **После наступления даты**: рассчитывается следующий цикл (+28 дней от предыдущей даты)

## Безопасность

- Валидация входящих данных (номера телефонов, платежей)
- Подписание webhook'ов ЮKassa
- Rate limiting (максимум 5 запросов в минуту с одного пользователя)
- Хеширование чувствительных данных
- Environment variables для всех секретов

## API Endpoints

- `GET /health` - проверка здоровья приложения
- `POST /webhook/telegram` - webhook для Telegram
- `POST /webhook/yookassa` - webhook для ЮKassa

## Структура базы данных

### Таблица `payments`
- `id` - первичный ключ
- `user_id` - ID пользователя Telegram
- `phone_number` - номер телефона
- `amount` - сумма платежа
- `status` - статус (pending, succeeded, canceled)
- `yookassa_payment_id` - ID платежа в ЮKassa
- `created_at` - дата создания

### Таблица `user_requests`
- `id` - первичный ключ
- `user_id` - ID пользователя Telegram
- `phone_number` - номер телефона
- `calculated_date` - рассчитанная дата овуляции
- `cycle_number` - номер цикла
- `is_active` - активен ли запрос
- `created_at` - дата создания
- `updated_at` - дата обновления

## Лицензия

MIT

