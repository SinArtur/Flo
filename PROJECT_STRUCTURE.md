# Структура проекта Flo Hack Bot

## Обзор архитектуры

Проект следует принципам Clean Architecture, разделяя код на слои:

### Core Layer (Бизнес-логика)
- **entities/**: Доменные сущности (Payment, UserRequest, PhoneNumber)
- **use_cases/**: Бизнес-логика (CalculateOvulationDate, ProcessPayment, VerifyPayment)
- **interfaces/**: Абстракции для репозиториев и внешних сервисов

### Infrastructure Layer (Внешние зависимости)
- **database/**: SQLAlchemy модели, репозитории, миграции
- **payment_gateway/**: Адаптер для YooKassa API
- **telegram_bot/**: Обработчики команд и сообщений Telegram
- **redis/**: Клиент для Redis (rate limiting, кеширование)
- **utils/**: Вспомогательные утилиты (форматирование дат)

### Presentation Layer (Слой представления)
- **bot/**: FastAPI приложение, точка входа
- **webhooks/**: Обработчики webhook'ов (Telegram, YooKassa)

### Config Layer
- **settings.py**: Управление конфигурацией через environment variables

## Поток данных

### 1. Запрос пользователя
```
User → Telegram → Bot Handler → Use Case → Repository → Database
```

### 2. Обработка платежа
```
User → Payment Link → YooKassa → Webhook → Verify Use Case → Database → Bot Notification
```

### 3. Расчет даты овуляции
```
Phone Number → Hash Algorithm → Date Calculation → Storage → Response
```

## Ключевые компоненты

### Use Cases

1. **CalculateOvulationDateUseCase**
   - Детерминированный расчет на основе номера телефона
   - Управление циклами (обновление после наступления даты)

2. **ProcessPaymentUseCase**
   - Создание платежа в YooKassa
   - Проверка существующих успешных платежей

3. **VerifyPaymentUseCase**
   - Верификация webhook от YooKassa
   - Автоматический расчет даты после успешной оплаты

### Repositories

- **PaymentRepository**: CRUD операции для платежей
- **RequestRepository**: Управление запросами пользователей

### Adapters

- **YooKassaAdapter**: Интеграция с платежным шлюзом
- **RedisClient**: Управление кешем и rate limiting

## Безопасность

- Валидация номеров телефонов (regex)
- Rate limiting через Redis (5 запросов/минуту)
- Верификация webhook'ов YooKassa
- Environment variables для секретов
- Хеширование чувствительных данных

## Масштабируемость

- Асинхронная обработка (async/await)
- Connection pooling для БД
- Кеширование в Redis
- Легко добавить новые платежные системы
- Легко добавить поддержку других мессенджеров

