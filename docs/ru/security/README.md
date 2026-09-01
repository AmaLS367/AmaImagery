# Документация безопасности

## Обзор

Security notes для текущего runtime **AmaImagery**: auth, file delivery, rate limiting, moderation и operational safeguards.

## Функции безопасности

### 🔐 Аутентификация
- JWT-based auth flows
- хэширование паролей
- refresh token flow
- session/cookie related config

### 🛡️ Авторизация
- защита authenticated routes
- superuser-only доступ к admin pages

### 🚦 Rate Limiting
- ограничения на пользователя и IP
- Redis-backed режим при включённом Redis

### ✅ Валидация ввода
- Pydantic validation
- лимиты на размер запросов
- валидация файлов на delivery side

### 🔍 Фильтрация контента
- NSFW rules
- prompt hygiene
- пользовательские NSFW preferences

### 🌐 Сетевая / Runtime безопасность
- настройки network guard
- host/origin related config
- security headers и cookie settings

## Разделы документации

| Тема | Статус |
|------|--------|
| Authentication deep-dive | 🚧 Coming soon |
| Authorization deep-dive | 🚧 Coming soon |
| Rate limiting deep-dive | 🚧 Coming soon |
| Input validation deep-dive | 🚧 Coming soon |
| Content filtering deep-dive | 🚧 Coming soon |
| Network security deep-dive | 🚧 Coming soon |
| Data protection deep-dive | 🚧 Coming soon |
| Security best practices page | 🚧 Coming soon |

## Сообщение о проблемах безопасности

Если вы нашли уязвимость, пишите на `ama@amadev.tech`. Не открывайте публичный issue для непочиненной security-проблемы.

Смотрите корневой [SECURITY.md](../../../SECURITY.md) для актуальной disclosure policy.
