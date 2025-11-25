# Security Guide — genai 2.0 

Версия документа: 2025-09-13

## 0. TL;DR / Чек-лист перед релизом
- [ ] `.env.prod` заполнен из `/.env.prod.example` (секреты, лимиты, пути).
- [ ] Docker Compose: `docker/compose.prod.yml` используется; сеть внутренняя; порты наружу только у `nginx`.
- [ ] `nginx.conf`: CSP/COOP/COEP/CORP, `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy no-referrer`; `/api/auth`, `/api/generate`, `/api/file` с лимитами и отдельными локациями.
- [ ] FastAPI: `/docs`/`/openapi.json` отключены в prod; `RequestLimitsMiddleware`; `RequestIDMiddleware`; унифицированные ошибки без стеков; `TrustedHostMiddleware` (если используется).
- [ ] Аутентификация: Access-JWT TTL = 15 минут; refresh-cookie `HttpOnly+Secure+SameSite=Lax+Path=/auth`; реюз-детект в Redis.
- [ ] Анти-DoS: лимиты и очереди на `/generate`, rate-limit на `/auth` и `/file`; таймауты запроса и инференса.
- [ ] Файлы: белые списки MIME/расширений, запрет traversal, выдача как `attachment`, подписанные ссылки `sig+exp` ≤ 900 c, одноразовость (Redis).
- [ ] PostgreSQL: роли `pgroot/migrator/app`, SCRAM-SHA-256; Alembic-миграции, **никаких** `create_all` в prod; индексы/ограничения.
- [ ] Redis: `requirepass`, `protected-mode yes`, переименованы FLUSH*/CONFIG/SHUTDOWN/DEBUG; политика памяти; healthcheck с AUTH.
- [ ] ML/инференс: `NO_NETWORK=1`, `local_files_only=True`; `socket.connect` заблокирован; IP-Adapter грузится локально из `IP_ADAPTER_DIR`.
- [ ] Логи/аудит: security-канал JSONL, `X-Request-ID` в ответах, маскирование, ротация логов контейнеров и файлов.
- [ ] Тесты: unit/integration/e2e прогнаны; e2e проверяет заголовки безопасности и `/docs` off.

---

## 1. Модель угроз и принципы
- Развёртывание локальное, интернет-выход в рантайме запрещён.
- Атаки: подбор токенов, реюз refresh, DoS на `/auth|/generate|/file`, traversal/недопустимые имена файлов, утечки через логи/заголовки, SSRF через библиотеки инференса, слабые роли в БД/Redis.
- Принципы: **минимально необходимые права**, **надёжные дефолты**, **жёсткие лимиты**, **fail-fast** при неверной конфигурации, **детерминированность** (оффлайн).

## 2. Окружения и файлы
- Продовый стек: `docker/compose.prod.yml` + `nginx` + `api` + `postgres` + `redis`.
- Локальные модели: монтируются в контейнер по пути `/models` (пример: `./models:/models:ro`).
- Статика фронтенда: монтируется в `/app/static` и отдаётся nginx.

## 3. Секреты и переменные окружения
- Образец: `/.env.prod.example`.
- Минимум для прода: `SECRET_KEY`, `DATABASE_URL` (user *app*), `REDIS_URL` с паролем, `REFRESH_COOKIE_SECURE=1`, лимиты (см. таблицу ниже).
- Не коммить реальные `.env`. Храни вне Git.

### 3.1 Полезные переменные (фрагмент)
| Переменная | Значение по умолчанию | Назначение |
|-----------|------------------------|------------|
| `ENV` | `prod` | Режим приложения |
| `RUN_IN_DOCKER` | `1` | Запуск в контейнере |
| `SECRET_KEY` | — | Ключ для JWT/HMAC подписей |
| `FRONTEND_ORIGIN` | `https://localhost` | Разрешённый Origin для CORS |
| `ACCESS_TTL_MIN` | `15` | Срок жизни Access-JWT (мин) |
| `REFRESH_TTL_DAYS` | `14` | Срок жизни refresh (дней) |
| `REFRESH_COOKIE_SECURE` | `1` | Cookies только по HTTPS |
| `MAX_BODY_BYTES` | `26214400` | Лимит тела запроса (байт) |
| `REQUEST_TIMEOUT_SECONDS` | `30` | Таймаут обработки запроса |
| `MAX_CONCURRENT_GENERATIONS` | `2` | Параллельные генерации |
| `GENERATION_TIMEOUT_SECONDS` | `60` | Таймаут инференса |
| `FILE_DOWNLOAD_TTL_SEC` | `900` | TTL подписей на файлы |
| `FILE_SINGLE_USE` | `1` | Одноразовые ссылки |
| `NO_NETWORK` | `1` | Блок исходящих соединений |
| `IP_ADAPTER_DIR` | `/models/ip-adapter/…` | Папка с весами IP-Adapter |

Полный список см. в `/.env.prod.example`.

## 4. Nginx (reverse proxy)
Файл: `/nginx.conf`  
Ключевые настройки:
- Редирект 80 → 443. TLS 1.2/1.3, `server_tokens off`.
- Заголовки безопасности: CSP, COOP/COEP/CORP, `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy no-referrer`. HSTS закомментирован для self-signed.
- Лимиты и соединения: `limit_req_zone` для `/api/auth`, `/api/generate`, `/api/file`; `limit_conn_zone perip`.
- Таймауты и размеры: `client_max_body_size 25m`, `client_body_timeout`, `send_timeout`, `keepalive_timeout`, `proxy_*_timeout`.
- Отдельные локации до общего `/api/`:
  - `^~ /api/auth/refresh` – высокая частота (`refresh_per_ip`).
  - `^~ /api/auth/` – жёсткие лимиты (`auth_per_ip`).
  - `^~ /api/generate` – `limit_req gen_per_ip` + `limit_conn perip`.
  - `^~ /api/file` – `limit_req file_per_ip` + `limit_conn perip`.
- Проксируются заголовки `X-Forwarded-*`.

## 5. Backend (FastAPI)
Файлы: `app/main.py`, `app/config.py`, `app/errors.py`, `app/middleware/request_limits.py`, `app/middleware/request_id.py`, `app/logging_setup.py`
- Документация (`/docs`, `/redoc`, `/openapi.json`) отключена в prod.
- `RequestLimitsMiddleware`: лимит тела (`MAX_BODY_BYTES`), длины query-параметров, общий таймаут запроса.
- `RequestIDMiddleware`: генерация/прокидывание `X-Request-ID`.
- Унифицированные JSON-ошибки без стеков и версий.
- Логи структурные, маскирование секретов, отдельный security-канал.

## 6. Аутентификация и сессии
Файлы: `app/auth/*`, `app/security.py`
- Access-JWT: TTL берётся из `ACCESS_TTL_MIN`; задаются `typ`, `iat`, `nbf`, `exp`, `jti`.
- Refresh в `HttpOnly+Secure+SameSite=Lax+Path=/auth`; хранение и ротация через Redis; reuse-детект с отзывом семейства токенов.
- Bcrypt rounds задаются `BCRYPT_ROUNDS`.
- Rate-limit на `/auth` в приложении и на уровне nginx.

## 7. Анти-DoS
Файлы: `nginx.conf`, `app/main.py`, `app/limits.py`
- Nginx: `limit_req`/`limit_conn` для `/auth`, `/generate`, `/file`.
- Приложение: очереди генераций через `asyncio.Semaphore`; `asyncio.wait_for` + callback на таймаут внутри пайплайна; rate-limit на `/generate` и `/file`.
- ASGI: зажат `timeout_keep_alive` (см. `run.py`).

## 8. Файлы и загрузки
Файлы: `app/files/validators.py`, `app/files/signing.py`, `app/main.py`
- Белый список расширений и MIME.
- Нормализация имён, запрет traversal (без подкаталогов).
- Выдача только как `attachment`, `X-Content-Type-Options: nosniff`.
- Подписанные ссылки `sig+exp` (HMAC-SHA256) с TTL ≤ 900 c; опциональная одноразовость через Redis (`FILE_SINGLE_USE=1`).

## 9. PostgreSQL
Файлы: `docker/compose.prod.yml`, `db/init/00-app-user.sh` (инициализация), Alembic миграции
- Роли: `pgroot` (суперюзер), `migrator` (DDL), `app` (RUN, CRUD). Приложение подключается как `app`.
- Инициализация с SCRAM-SHA-256 (`POSTGRES_INITDB_ARGS="--auth=scram-sha-256"`).
- Права по умолчанию выданы `app` только на `SELECT/INSERT/UPDATE/DELETE` + `USAGE, SELECT` на последовательности.
- Индексы и ограничения длины (пример: `users.email lower()`, `refresh_tokens.jti`, `generations.created_at`, `CHECK length(email) ≤ 255`, `CHECK length(prompt) ≤ 2000`).
- **Никаких** `create_all` в prod (создание таблиц только через Alembic).

## 10. Redis
Файлы: `docker/compose.prod.yml`, `docker/redis/redis.conf`
- Внутренняя сеть, без публикации портов.
- `requirepass`, `protected-mode yes`, политика памяти (`noeviction`), `appendonly no`.
- Переименованы/отключены опасные команды: `FLUSHALL/FLUSHDB/CONFIG/SHUTDOWN/DEBUG`.
- Healthcheck с AUTH: `redis-cli -a ${{REDIS_PASSWORD}} ping`.
- Неймспейсы ключей: `auth:`, `rate:`, `file:`, `filedl:`, `jwt:`.

## 11. ML/Инференс
Файлы: `app/infer/net_guard.py`, `app/inference/pipeline.py`, `app/main.py`
- Жёсткий оффлайн: `NO_NETWORK=1` + `apply_net_guard()` блокирует `socket.connect`.
- `local_files_only=True` для загрузки моделей/весов; использование только локальных путей.
- IP-Adapter загружается из `IP_ADAPTER_DIR` (папка с `.safetensors`), без сетевых запросов.
- Верхние пределы параметров: width/height/steps/guidance/batch проверяются на сервере.
- Таймаут инференса с отменой через `callback` и `asyncio.to_thread`, очистка VRAM/GC.
- Ресурсы Torch: `torch.set_num_threads`, `cuda.set_per_process_memory_fraction` (если доступно).

## 12. Логи и аудит
Файлы: `app/logging_setup.py`, `app/middleware/request_id.py`, `app/audit.py`
- Структурные логи (JSON), отдельный файл/канал `security.jsonl` с ротацией.
- События: `login_success`, `login_failure`, `refresh_reuse_detected`, `rate_limited`, `file_download`.
- Контейнерная ротация stdout/stderr (`json-file` 10MB×5).
- Маскирование секретов и кук в логах включено.

## 13. Тесты безопасности
Каталог: `tests/`
- Unit: подписи файлов; fail-fast без `SECRET_KEY`; маскирование логов.
- Integration: `/docs` off; CORS негативные; `405/413`; серверные верхние пределы генерации.
- E2E: заголовки CSP/COOP/COEP; отсутствие исходящих соединений; истечение подписей; лимиты на /auth.
- В CI есть e2e-job для проверки заголовков и запрета внешних соединений.

## 14. CI/CD и сборка
Файлы: `.github/workflows/*.yml`
- Сборка контейнеров, прогон линтеров/тестов, Trivy (если подключён).
- E2E job: поднимает `compose.prod`, проверяет заголовки и `/docs` off, валидирует запрет сети.

## 15. Различия Prod vs Local
- Prod: `ENV=prod`, `RUN_IN_DOCKER=1`, `REFRESH_COOKIE_SECURE=1`, `NO_NETWORK=1`, `docs/openapi off`, строгие лимиты nginx, Redis/PG с паролями, security-канал логов.
- Local/dev: можно включить `docs`, ослабить лимиты для отладки, отключить одноразовость ссылок, но **никогда не коммить секреты** и конфиги dev в репозиторий.

## 16. Типовые команды проверки
```bash
# заголовки безопасности
curl -kI https://localhost | egrep -i 'content-security-policy|cross-origin-(opener|embedder)-policy|cross-origin-resource-policy|x-frame-options|x-content-type-options|referrer-policy'

# /docs выключены
curl -k -o /dev/null -w "%{{http_code}}\n" https://localhost/docs

# лимиты на /auth
ab -n 30 -c 10 -p login.json -T application/json https://localhost/api/auth/me

# 413 большой upload (если есть /upload)
dd if=/dev/zero of=big.bin bs=1M count=30
curl -k -F "file=@big.bin" https://localhost/api/upload -i

# истёкшая подпись на файл
now=$(date +%s); exp=$((now-10)); name="x.png"; sig=$(python - <<'PY'
from app.files.signing import make_signature; import os; print(make_signature(os.environ.get('NAME','x.png'), int(os.environ.get('EXP','0'))))
PY)
curl -k "https://localhost/api/file?path=$name&exp=$exp&sig=$sig" -I

# запрет исходящей сети внутри контейнера api
docker compose exec -T api python - <<'PY'
import socket; s=socket.socket();
try:
  s.connect(('1.1.1.1',80)); print('ERR')
except OSError:
  print('OK')
finally:
  s.close()
PY
```

## 17. Изменение лимитов и параметров
- Через ENV (см. `.env.prod.example`). Синхронизация с nginx: `MAX_BODY_BYTES` ↔ `client_max_body_size`.
- Генерация: `MAX_CONCURRENT_GENERATIONS`, `GENERATION_TIMEOUT_SECONDS`.
- Файлы: `FILE_DOWNLOAD_TTL_SEC`, `FILE_SINGLE_USE`, списки `FILE_ALLOWED_*` (JSON-массивы).
- Auth: `ACCESS_TTL_MIN`, `REFRESH_TTL_DAYS`, `BCRYPT_ROUNDS`.
- Redis память: `--maxmemory`, `--maxmemory-policy` в compose.

## 18. Инциденты и отзыв токенов
- При компрометации refresh: лог `refresh_reuse_detected`, выполняется отзыв семейства токенов в Redis; заблокированные jti хранятся в `jwt:`-префиксе.
- Форс-отзыв всех refresh пользователя: команда в админ-утилите (или ручной `DEL` по ключам семейства в Redis).

## 19. Что намеренно жёстко (не смягчать)
- CSP без inline-скриптов.
- `/docs` off в prod.
- `NO_NETWORK=1` для инференса.
- Access-JWT короткий (15 минут).
- Выдача файлов только `attachment` + `nosniff`.
- Redis команды FLUSH*/CONFIG/SHUTDOWN/DEBUG отключены.

---

## 20. Карта файлов безопасности
- `nginx.conf` — заголовки, лимиты, таймауты, маршрутизация API.
- `docker/compose.prod.yml` — изоляция сервисов, политика логов, монтирование моделей.
- `app/config.py` — единая конфигурация (лимиты, таймауты, оффлайн, пути).
- `app/errors.py` — унифицированные JSON-ошибки.
- `app/middleware/request_limits.py` — размер тела, длины query, общий таймаут запроса.
- `app/middleware/request_id.py` — `X-Request-ID`.
- `app/logging_setup.py` — структурные логи, security-канал, маскирование, ротация.
- `app/files/validators.py` — белые списки, нормализация имён.
- `app/files/signing.py` — HMAC-подписи `sig+exp`, одноразовость.
- `app/main.py` — маршруты `/file`, `/generate`, отключение `/docs` в prod, очередь/таймаут инференса, события безопасности.
- `app/infer/net_guard.py` — запрет исходящей сети.
- `app/inference/pipeline.py` — `local_files_only=True`, локальная загрузка моделей и IP-Adapter.
- `db/init/00-app-user.sh` — роли `pgroot/migrator/app`, права по минимуму.
- `docker/redis/redis.conf` — защищённый режим, переименование опасных команд.
- `tests/**` — unit/integration/e2e проверки безопасности.

---

## 21. Поддержка и обновления
- Проверка CVE: `pip-audit`, `safety`, контейнерный сканер (Trivy) в CI.
- Регулярное обновление зависимостей в `requirements.txt` с прогоном тестов и e2e.
- Регулярные smoke-проверки заголовков и DoS-лимитов.

---
