# Аудит проекта AmaImagery и план исправлений

**Дата проведения аудита:** 05.01.2026  
**Версия проекта:** 0.2.0

---

## 1. Краткая сводка

### Что сейчас сломано

| Функция | Статус | Причина |
|---------|--------|---------|
| Регистрация | ⚠️ Частично работает | Токен не сохраняется в localStorage отдельно |
| Логин | ❌ Не работает | Cookie path несовпадение, refresh не отправляется |
| Refresh токена | ❌ Не работает | Cookie path=/auth вместо /api/v1/auth |
| Получение профиля | ⚠️ Частично | Зависит от токена |
| Генерация изображений | ⚠️ Условно | Требует Redis + модель + worker |
| История генераций | ❌ Неверные URL | URL файлов без /api/v1 prefix |
| Загрузка файлов | ⚠️ Условно | Работает если URL корректен |

### Главные причины (7 пунктов)

1. **P0-001**: Cookie `refresh_token` устанавливается с `path="/auth"`, но запросы идут на `/api/v1/auth/refresh` — браузер не отправляет cookie
2. **P0-002**: URL изображений в истории генерируется как `/file?path=...` вместо `/api/v1/file?path=...`
3. **P0-003**: `REFRESH_COOKIE_SECURE=true` по умолчанию блокирует cookies на localhost без HTTPS
4. **P1-001**: SECRET_KEY по умолчанию = `CHANGE_ME_LONG_RANDOM` — JWT невалидны
5. **P1-002**: Дублирование HTTP клиентов в `lib/api.ts` и `lib/http.ts`
6. **P1-003**: После регистрации `access_token` не сохраняется отдельно в localStorage
7. **P2-001**: NO_NETWORK=true требует локальных моделей, которые отсутствуют

### Риски, если чинить без плана

- Нарушение работающей функциональности при изменении cookie path
- Потеря сессий пользователей при изменении SECRET_KEY
- Поломка фронтенда при несогласованных изменениях API контракта

---

## 2. Карта репозитория

### Дерево ключевых папок

```
/workspace/
├── app/                          # Backend (FastAPI)
│   ├── api/v1/                   # HTTP слой (роутеры)
│   │   ├── auth/                 # Авторизация
│   │   │   ├── router.py         # Endpoints: register, login, refresh, logout
│   │   │   └── deps.py           # Dependencies: current_user, optional_user
│   │   ├── files/router.py       # Endpoint: /file (скачивание файлов)
│   │   ├── images/               # Endpoints генерации
│   │   │   ├── generate.py       # POST /images/generate
│   │   │   └── status.py         # GET /images/status/{task_id}
│   │   └── users/router.py       # GET /users/me/generations, settings
│   ├── application/use_cases/    # Application слой
│   ├── domain/                   # Domain слой
│   │   ├── models.py             # SQLAlchemy модели
│   │   ├── schemas.py            # Pydantic схемы
│   │   └── providers/            # Абстракции провайдеров
│   ├── infra/                    # Infrastructure слой
│   │   ├── db.py                 # Async SQLAlchemy engine
│   │   ├── redis.py              # Redis client
│   │   ├── queue/task_queue.py   # Redis task queue
│   │   └── repositories/         # SQLAlchemy repositories
│   ├── workers/                  # Background workers
│   │   └── generation_worker.py  # Обработчик очереди генерации
│   ├── config.py                 # Pydantic Settings
│   └── main.py                   # FastAPI app entry point
│
├── frontend/                     # Frontend (React + Vite)
│   └── src/
│       ├── lib/
│       │   ├── api.ts            # API клиент (основной)
│       │   └── http.ts           # API клиент (дублирует!)
│       ├── pages/
│       │   ├── Login.tsx         # Страница входа
│       │   ├── Register.tsx      # Страница регистрации
│       │   ├── Generate.tsx      # Страница генерации
│       │   └── History.tsx       # История генераций
│       ├── providers/
│       │   ├── JobProvider.tsx   # Polling статуса задач
│       │   └── SettingsProvider.tsx
│       └── App.tsx               # Главный компонент
│
├── docker/
│   ├── compose.local.yml         # Docker Compose для локальной разработки
│   └── .env.docker.example       # Пример переменных для Docker
│
├── .env.example                  # Пример переменных окружения
└── migrations/                   # Alembic migrations
```

### Точки входа

| Компонент | Файл | Команда запуска |
|-----------|------|-----------------|
| Backend API | `app/main.py` | `uvicorn app.main:app --reload` |
| Generation Worker | `app/entrypoints/generation_worker.py` | `python -m app.entrypoints.generation_worker` |
| Frontend Dev | `frontend/` | `npm run dev` (Vite на порту 5173) |

### Как устроен роутинг

**Backend:**
```
/api/v1/
├── /auth/register          POST  - Регистрация
├── /auth/me                POST  - Логин (!)
├── /auth/me                GET   - Получить профиль
├── /auth/refresh           POST  - Обновить токены
├── /auth/logout            POST  - Выход
├── /auth/forgot-password   POST  - Забыли пароль
├── /auth/reset-password    POST  - Сброс пароля
├── /images/generate        POST  - Создать задачу генерации
├── /images/status/{id}     GET   - Статус задачи
├── /users/me/generations   GET   - История генераций пользователя
├── /users/me/settings      GET/PATCH - Настройки пользователя
├── /file                   GET   - Скачать файл (с подписью)
└── /health                 GET   - Health check
```

**Frontend Vite Proxy:**
```javascript
// vite.config.ts
proxy: {
  '/api': { target: 'http://localhost:8000' },
  '/file': { target: 'http://localhost:8000' },  // Не используется!
  '/auth': { target: 'http://localhost:8000' },  // Не соответствует /api/v1/auth
}
```

### Где конфиги и переменные окружения

| Файл | Назначение |
|------|------------|
| `.env.example` | Шаблон переменных (корень проекта) |
| `app/config.py` | Pydantic Settings, читает ENV |
| `frontend/.env.example` | Отсутствует! |
| `docker/.env.docker.example` | Для Docker Compose |

---

## 3. Несоответствия фронт <-> бэк (контракт API)

### API-001: Cookie path для refresh_token

**Симптомы:**
- После логина refresh не работает
- Браузер не отправляет cookie на `/api/v1/auth/refresh`

**Причина:**
Cookie устанавливается с `path="/auth"`, но запросы идут на `/api/v1/auth/refresh`. Браузер отправляет cookies только если путь запроса **начинается** с cookie path.

**Где в бэке:**
```python
# app/api/v1/auth/router.py, строки 54-62, 154-162, 324-332
def _set_refresh_cookie(resp: Response, token: str) -> None:
    resp.set_cookie(
        ...
        path="/auth",  # ОШИБКА!
    )
```

**Правка:**
```python
path="/api/v1/auth",  # Правильный путь
```

**Проверка:**
1. Логин
2. Открыть DevTools → Application → Cookies
3. Проверить, что refresh_token имеет path=/api/v1/auth
4. Через 15 минут (или вручную) вызвать refresh
5. Проверить, что cookie отправляется и токен обновляется

---

### API-002: URL изображений в истории без /api/v1 prefix

**Симптомы:**
- Изображения в истории не загружаются
- 404 при попытке открыть картинку

**Причина:**
В `users/router.py` URL формируется без prefix:

**Где в бэке:**
```python
# app/api/v1/users/router.py, строка 75
image_url = f"/file?path={name}&exp={exp}&sig={sig}"  # ОШИБКА!
```

**Правка:**
```python
image_url = f"/api/v1/file?path={name}&exp={exp}&sig={sig}"
```

**Проверка:**
1. Создать генерацию
2. Открыть историю
3. Проверить, что изображения загружаются

---

### API-003: REFRESH_COOKIE_SECURE=true на localhost

**Симптомы:**
- Cookies не устанавливаются в браузере на localhost (HTTP)
- Refresh не работает даже с правильным path

**Причина:**
Secure cookies не отправляются по HTTP, только по HTTPS.

**Где:**
```python
# app/config.py, строка 181
refresh_cookie_secure: Annotated[bool, Field(...)] = True
```

**Правка .env.example:**
```env
# Для локальной разработки без HTTPS
REFRESH_COOKIE_SECURE=false
```

**Проверка:**
1. Установить REFRESH_COOKIE_SECURE=false
2. Логин
3. Проверить в DevTools, что cookie установлен

---

### API-004: Логин и получение профиля на одном endpoint

**Симптомы:**
- Путаница в API контракте
- Фронт вызывает POST /api/v1/auth/me для логина

**Причина:**
Архитектурное решение использовать `/auth/me` для двух целей:
- GET — получить профиль
- POST — логин

**Где в бэке:**
```python
# app/api/v1/auth/router.py
@router.get("/me", response_model=MeOut)  # Профиль
@router.post("/me", response_model=LoginOut, ...)  # Логин
```

**Где во фронте:**
```typescript
// frontend/src/pages/Login.tsx, строка 107
const res = await fetch('/api/v1/auth/me', { method: 'POST', ... })

// frontend/src/App.tsx, строка 99
const response = await fetch('/api/v1/auth/me', { ... })  // GET
```

**Правка (рекомендуется, но необязательно):**
Лучше разделить на `/auth/login` для POST и `/auth/me` для GET. Но это breaking change.

**Текущий workaround:** Оставить как есть, работает корректно.

---

### API-005: Регистрация не сохраняет access_token отдельно

**Симптомы:**
- После регистрации пользователь не авторизован
- Запросы к API возвращают 401

**Причина:**
Login сохраняет токен в два места, Register — только в одно.

**Где во фронте:**
```typescript
// frontend/src/pages/Login.tsx, строки 124-129
localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
if (payload?.access_token) {
    localStorage.setItem('access_token', payload.access_token)  // ✓
}

// frontend/src/pages/Register.tsx, строка 164
localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
// access_token НЕ сохраняется отдельно! ✗
```

**Правка Register.tsx:**
```typescript
try { 
    localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
    if (payload?.access_token) {
        localStorage.setItem('access_token', payload.access_token)
    }
} catch {}
```

**Проверка:**
1. Зарегистрироваться
2. Проверить localStorage: должен быть access_token
3. Попробовать создать генерацию

---

## 4. Ошибки авторизации и безопасности

### SEC-001: SECRET_KEY по умолчанию небезопасен

**Проблема:**
```python
# app/config.py, строка 49
secret_key: ... = ""
```
```env
# .env.example, строка 29
SECRET_KEY=CHANGE_ME_LONG_RANDOM
```

**Риск:**
- JWT можно подделать
- Подписи файлов можно угадать

**Правка:**
1. Генерировать при первом запуске:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
2. Добавить в `.env`:
```env
SECRET_KEY=<сгенерированный_ключ>
```

---

### SEC-002: Cookie SameSite=Lax недостаточен для cross-origin

**Текущее состояние:**
```python
samesite="lax"
```

**Анализ:**
- `Lax` подходит для same-site запросов
- Для cross-origin (если фронт на другом домене) нужен `None` + `Secure=true`
- Для localhost разработки `Lax` работает

**Решение:** Оставить `Lax` для локальной разработки. Для production с разными доменами — настраивать отдельно.

---

### SEC-003: Хранение токенов на фронте

**Текущая реализация:**
- `access_token` в localStorage
- `refresh_token` в httpOnly cookie

**Анализ:**
- localStorage уязвим к XSS
- httpOnly cookie защищен от XSS
- Это стандартный компромисс для SPA

**Рекомендация:** Приемлемо. Для повышения безопасности можно перенести access_token в httpOnly cookie, но это усложнит архитектуру.

---

## 5. Генерация изображений и фоновые задачи

### Как устроена генерация

```
1. Frontend: POST /api/v1/images/generate
   ↓
2. Backend: GenerateImageUseCase
   - Валидация запроса
   - Проверка safety policies
   - Enqueue в Redis (TaskQueue)
   ↓
3. Redis: tasks:queue (List), task:{id} (Hash)
   ↓
4. Worker: generation_worker.py
   - Dequeue из Redis
   - Вызов DiffusersProvider.generate()
   - Сохранение результата в Redis + DB
   ↓
5. Frontend: Polling GET /api/v1/images/status/{task_id}
   - Каждые 2 секунды
   - До 300 попыток (10 минут)
```

### GEN-001: Redis обязателен

**Проблема:**
```python
# app/infra/queue/task_queue.py, строка 176-180
def get_task_queue() -> RedisTaskQueue:
    redis_client = get_redis()
    if redis_client is None:
        raise RuntimeError("Redis client is not available...")
```

**Симптомы:**
- При NO_REDIS=true или недоступном Redis — crash при генерации
- Ошибка: "Redis client is not available. Cannot create TaskQueue."

**Правка (для development без Redis):**
Вариант 1: Добавить in-memory fallback queue
Вариант 2: Обеспечить запуск Redis

**Рекомендация:** Для локальной разработки запускать Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

### GEN-002: Worker не запускается автоматически

**Проблема:**
При локальном запуске через `uvicorn app.main:app` worker не запускается.

**Решение:**
Запускать worker отдельно:
```bash
python -m app.entrypoints.generation_worker
```

Или использовать Docker Compose из `docker/compose.local.yml`.

---

### GEN-003: NO_NETWORK=true требует локальных моделей

**Проблема:**
```python
# app/config.py, строка 247-259
@field_validator("model_id", "vae_id", mode="after")
def _check_local_when_offline(cls, v, info):
    if no_net and v:
        p = Path(str(v))
        if not p.exists():
            raise ValueError(f"{info.field_name} not found locally: {p}")
```

**Симптомы:**
- При запуске: `model_id not found locally: models/dreamshaper_6NoVae.safetensors`

**Правка .env:**
```env
NO_NETWORK=false  # Разрешить загрузку моделей из HuggingFace
# или
MODEL_ID=runwayml/stable-diffusion-v1-5  # Использовать HF модель
```

---

### Как тестировать без прод окружения

1. **Mock provider:**
```python
# Создать tests/mocks/mock_provider.py
class MockImageProvider:
    async def generate(self, request):
        return GenerationResult(
            image_path="outputs/test.png",
            metadata={"mock": True}
        )
```

2. **Использовать sqlite для тестов:**
```env
DATABASE_URL=sqlite+aiosqlite:///./test.db
```

3. **Запустить минимальный стек:**
```bash
# Terminal 1: Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2: Backend
uvicorn app.main:app --reload

# Terminal 3: Worker (если нужна генерация)
python -m app.entrypoints.generation_worker

# Terminal 4: Frontend
cd frontend && npm run dev
```

---

## 6. Файлы и выдача результатов (file storage)

### Где сохраняются изображения

```python
# app/config.py, строка 228
outputs_dir: ... = Path(__file__).resolve().parents[1] / "outputs"
```

По умолчанию: `/workspace/outputs/`

### Как строятся URL

**При завершении генерации (status.py):**
```python
# app/api/v1/images/status.py, строки 58-63
if data.status == "completed" and data.image_filename:
    exp = now + ttl
    sig = make_signature(data.image_filename, exp)
    image_url = f"/api/v1/file?path={data.image_filename}&exp={exp}&sig={sig}"
```
✓ Корректно

**В истории (users/router.py):**
```python
# app/api/v1/users/router.py, строка 75
image_url = f"/file?path={name}&exp={exp}&sig={sig}"
```
✗ Отсутствует `/api/v1` prefix

### Как фронт открывает файлы

```typescript
// frontend/src/pages/Generate.tsx, строки 71-96
if (res.image_url) {
    setImgUrl(res.image_url);  // Используем готовый URL
} else if (res.image_filename && res.exp && res.sig) {
    const url = `/api/v1/file?path=...`;  // Строим сами
}
```

### FILE-001: Несогласованность URL в разных местах

| Источник | URL Format | Статус |
|----------|------------|--------|
| `/images/status/{id}` | `/api/v1/file?...` | ✓ |
| `/users/me/generations` | `/file?...` | ✗ |
| Frontend Generate | `/api/v1/file?...` | ✓ |
| Frontend History | `/api/v1/file?...` | ✓ (строит сам) |

**Правка:** Исправить `users/router.py` (см. API-002).

---

## 7. Архитектурные проблемы и рефакторинг

### ARCH-001: Дублирование HTTP клиентов

**Проблема:**
```
frontend/src/lib/
├── api.ts    # 285 строк, полноценный клиент с refresh
└── http.ts   # 18 строк, упрощённый клиент
```

Оба файла экспортируют `getToken()` и `api()` с разной логикой.

**Где используется http.ts:**
Нигде в основном коде. Вероятно, legacy.

**Правка:**
Удалить `http.ts` или унифицировать с `api.ts`.

---

### ARCH-002: Смешивание POST/GET на /auth/me

**Проблема:**
REST convention нарушен — один endpoint для разных действий.

**Текущее:**
- `POST /auth/me` = Login
- `GET /auth/me` = Get profile

**Рекомендуется:**
- `POST /auth/login` = Login
- `GET /auth/me` = Get profile

**Риск изменения:** Breaking change для фронтенда.

**Решение:** Оставить как есть, задокументировать.

---

### ARCH-003: Unit of Work создаётся на каждый запрос

**Текущее:**
```python
# app/api/v1/auth/router.py
uow = get_uow()
async with uow:
    ...
```

**Анализ:** Это правильный подход. UoW создаётся per-request, что обеспечивает изоляцию транзакций.

---

### ARCH-004: Provider Registry — Singleton vs Factory

**Текущее:**
```python
# app/domain/providers/registry.py
def get_provider_registry() -> ProviderRegistry:
    # Создаёт новый Registry каждый раз!
```

**Проблема:** DiffusersProvider создаётся при каждом вызове, загрузка модели дорогая.

**Фактически:** DiffusersProvider использует lazy loading через `get_pipeline()`, который кэширует модель.

**Решение:** Не критично, но можно кэшировать registry:
```python
_registry: ProviderRegistry | None = None

def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry(...)
    return _registry
```

---

## 8. План исправлений по коммитам

### Commit 1: Исправление критических проблем авторизации (P0)

**Цель:** Заставить работать логин и refresh token

**Файлы:**
- `app/api/v1/auth/router.py`

**Изменения:**
```python
# Строки 54-62, 154-162, 324-332, 189
# Заменить path="/auth" на path="/api/v1/auth"
```

**Критерий готовности:**
- [ ] Логин устанавливает cookie с path=/api/v1/auth
- [ ] Refresh endpoint получает cookie
- [ ] Токен обновляется

---

### Commit 2: Исправление URL файлов в истории (P0)

**Цель:** Изображения в истории загружаются

**Файлы:**
- `app/api/v1/users/router.py`

**Изменения:**
```python
# Строка 75
image_url = f"/api/v1/file?path={name}&exp={exp}&sig={sig}"
```

**Критерий готовности:**
- [ ] GET /users/me/generations возвращает URLs с /api/v1 prefix
- [ ] История загружает изображения

---

### Commit 3: Исправление сохранения токена при регистрации (P1)

**Цель:** После регистрации пользователь авторизован

**Файлы:**
- `frontend/src/pages/Register.tsx`

**Изменения:**
```typescript
// Строка 164
try { 
    localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
    if (payload?.access_token) {
        localStorage.setItem('access_token', payload.access_token)
    }
} catch {}
```

**Критерий готовности:**
- [ ] После регистрации access_token в localStorage
- [ ] Запросы к API успешны

---

### Commit 4: Обновление .env.example (P1)

**Цель:** Документировать правильные настройки для dev

**Файлы:**
- `.env.example`

**Изменения:**
```env
# Добавить комментарии и dev-friendly defaults
REFRESH_COOKIE_SECURE=false  # true for production with HTTPS
SECRET_KEY=  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(48))"
NO_NETWORK=false  # Set to true only if you have local models
```

**Критерий готовности:**
- [ ] Новый разработчик может запустить проект с минимальной настройкой

---

### Commit 5: Создание frontend/.env.example (P2)

**Цель:** Документировать фронтенд конфигурацию

**Файлы:**
- `frontend/.env.example` (новый)

**Содержимое:**
```env
VITE_API_URL=http://localhost:8000
VITE_API_TARGET=http://localhost:8000
```

**Критерий готовности:**
- [ ] Файл существует
- [ ] Vite корректно читает переменные

---

### Commit 6: Удаление дублирующего http.ts (P3)

**Цель:** Убрать confusion от двух API клиентов

**Файлы:**
- `frontend/src/lib/http.ts` (удалить)
- Проверить, что нигде не импортируется

**Критерий готовности:**
- [ ] http.ts удалён
- [ ] Сборка фронтенда успешна

---

## 9. Чеклист проверок после фиксов

### Регистрация
- [ ] Форма отправляется без ошибок
- [ ] Ответ содержит access_token
- [ ] access_token сохранён в localStorage
- [ ] Пользователь перенаправлен на /gen
- [ ] Топбар показывает авторизованного пользователя

### Логин
- [ ] Форма отправляется без ошибок
- [ ] Ответ содержит access_token
- [ ] refresh_token cookie установлен с path=/api/v1/auth
- [ ] Cookie имеет httpOnly=true
- [ ] Cookie имеет secure=false (для dev) или true (для prod)

### Refresh
- [ ] После истечения access_token (15 мин)
- [ ] Автоматический refresh при 401
- [ ] Новый access_token получен
- [ ] Новый refresh cookie установлен

### Создание генерации
- [ ] POST /api/v1/images/generate возвращает task_id
- [ ] Статус задачи доступен по GET /api/v1/images/status/{id}
- [ ] При наличии worker — задача обрабатывается
- [ ] Результат содержит image_url с подписью

### Получение результата
- [ ] URL из image_url открывается в браузере
- [ ] Изображение скачивается
- [ ] Подпись валидна (не 403)
- [ ] Срок не истёк (не 410)

### История
- [ ] GET /api/v1/users/me/generations возвращает список
- [ ] Каждый элемент имеет image_url с /api/v1 prefix
- [ ] Изображения загружаются в UI
- [ ] Фильтры работают

### Ошибки и логи
- [ ] При 401 — автоматический refresh или редирект на /login
- [ ] При 403 — понятное сообщение
- [ ] При 500 — логируется в backend
- [ ] Логи не содержат секретов (LOG_MASK_AUTH=true)

---

## Приложение A: Быстрый старт для разработчика

### 1. Клонирование и настройка

```bash
git clone <repo>
cd workspace

# Создать .env из примера
cp .env.example .env

# Сгенерировать SECRET_KEY
python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(48)}')" >> .env

# Установить dev-friendly настройки
echo "REFRESH_COOKIE_SECURE=false" >> .env
echo "DEBUG=true" >> .env
echo "NO_NETWORK=false" >> .env
```

### 2. Запуск инфраструктуры

```bash
# Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=amaimagery \
  -p 5432:5432 \
  postgres:16-alpine
```

### 3. Запуск backend

```bash
# Установка зависимостей
pip install -r requirements.txt

# Миграции
alembic upgrade head

# API сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Worker (в отдельном терминале)
python -m app.entrypoints.generation_worker
```

### 4. Запуск frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Проверка

1. Открыть http://localhost:5173
2. Зарегистрироваться
3. Создать генерацию
4. Проверить историю

---

## Приложение B: Примеры правок кода

### B.1 Исправление cookie path

```python
# app/api/v1/auth/router.py

# БЫЛО (строка 61):
path="/auth",

# СТАЛО:
path="/api/v1/auth",
```

Применить ко всем местам установки cookie:
- строка 61 (в _set_refresh_cookie)
- строка 158 (в login, очистка)
- строка 189 (в logout)
- строка 310 (в refresh, при ошибке)
- строка 318 (в refresh, при ошибке)
- строка 330 (в refresh, успех)

### B.2 Исправление URL в истории

```python
# app/api/v1/users/router.py, строка 75

# БЫЛО:
image_url = f"/file?path={name}&exp={exp}&sig={sig}"

# СТАЛО:
image_url = f"/api/v1/file?path={name}&exp={exp}&sig={sig}"
```

### B.3 Исправление Register.tsx

```typescript
// frontend/src/pages/Register.tsx, строки 163-165

// БЫЛО:
try { localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload })) } catch {}

// СТАЛО:
try { 
  localStorage.setItem('auth', JSON.stringify({ loggedIn: true, user: payload }))
  if (payload?.access_token) {
    localStorage.setItem('access_token', payload.access_token)
  }
} catch {}
```

---

*Конец документа*
