# План рефакторинга бэкенда по коммитам

Этот файл описывает, что именно нужно сделать в каждом коммите.  
Формат: сначала этап, потом по каждому коммиту краткое назначение и подробные шаги.

Нумерация коммитов условная, важен порядок сверху вниз.

---

## Stage 1. Provider Abstraction Layer

Цель этапа: отвязать бэкенд от конкретной реализации diffusers и ввести слой абстракций для провайдеров генерации изображений.

### ✅ 1. `feat(providers): introduce IImageProvider and generation DTOs`

**Цель:** заложить доменную абстракцию провайдера и структурированные запросы и ответы генерации.

**Что сделать:**

1. Создать новый модуль домена, например:
   - `app/domain/providers/base.py`
2. Определить `GenerationRequest` как `@dataclass` или Pydantic модель с полями:
   - `prompt: str`
   - `negative_prompt: str | None`
   - `seed: int | None`
   - `width: int`
   - `height: int`
   - `steps: int | None`
   - `guidance_scale: float | None`
   - дополнительные опции, которые уже используются в текущем пайплайне.
3. Определить `GenerationResult`:
   - `image_path: str` или `list[str]`
   - `metadata: dict[str, Any]` для технических и бизнес метаданных.
4. Определить интерфейс провайдера:
   - `class IImageProvider(Protocol)` или абстрактный класс:
     - `async def generate(self, request: GenerationRequest) -> GenerationResult`
     - `async def health_check(self) -> bool`
     - при необходимости `supports_features(self, features: set[str]) -> bool`.
5. Не использовать в этом модуле никаких импортов diffusers и инфраструктуры, только доменные типы.

---

### ✅ 2. `feat(providers): add provider registry for image generation`

**Цель:** централизованный реестр провайдеров, через который весь код получает нужный провайдер.

**Что сделать:**

1. Создать модуль:
   - `app/domain/providers/registry.py`
2. Определить класс `ProviderRegistry`:
   - конструктор принимает словарь `dict[str, IImageProvider]`
   - методы:
     - `register(name: str, provider: IImageProvider) -> None`
     - `get(name: str) -> IImageProvider`
     - `get_default() -> IImageProvider`
     - `list_providers() -> list[str]`
3. Добавить метод:
   - `async def health_report(self) -> dict[str, bool]` с вызовами `provider.health_check()`.
4. Подготовить DI функцию, например `get_provider_registry()`, которая создаст и вернет `ProviderRegistry`.

---

### ✅ 3. `refactor(inference): extract diffusers logic to DiffusersProvider`

**Цель:** вынести реализацию генерации через diffusers в отдельный провайдер.

**Что сделать:**

1. Найти текущую реализацию diffusers, обычно в:
   - `app/inference/pipeline.py` или похожем модуле.
2. Создать файл:
   - `app/infra/providers/diffusers_provider.py`
3. Реализовать `class DiffusersProvider(IImageProvider)`:
   - конструктор принимает зависимости:
     - загруженную модель
     - scheduler
     - device, dtype
     - дефолтные параметры.
   - `generate`:
     - принимает `GenerationRequest`
     - маппит поля на аргументы пайплайна
     - запускает генерацию
     - сохраняет изображения и собирает `GenerationResult`.
4. В старом `pipeline.py` оставить только вспомогательные функции и инициализацию, если они нужны, либо постепенно его выпиливать.
5. Убедиться, что внешний код больше не вызывает прямой diffusers пайплайн, а будет ходить в `DiffusersProvider`.

---

### ✅ 4. `refactor(services): route generation through ProviderRegistry`

**Цель:** сервисы больше не знают про diffusers напрямую, только про реестр провайдеров.

**Что сделать:**

1. Найти сервисы генерации, например:
   - `app/services/generation_service.py`
2. Добавить в конструктор зависимость `ProviderRegistry`.
3. В местах, где раньше был вызов diffusers:
   - собрать `GenerationRequest` из входных данных
   - получить провайдера:
     - `provider = provider_registry.get_default()` или `get(name)`
   - `result = await provider.generate(request)`
   - обработать `GenerationResult` и сохранить в БД при необходимости.
4. Проверить, что нет прямых импортов diffusers в сервисах.

---

### ✅ 5. `chore(config): add provider settings and default provider name`

**Цель:** сделать выбор провайдера конфигурируемым.

**Что сделать:**

1. В модуле конфигурации, например `app/core/config.py` или `app/settings.py`:
   - добавить поля:
     - `providers_default_name: str = "diffusers"`
     - при необходимости `providers_enabled: list[str]`
     - настройки для diffusers провайдера, например `diffusers_device`, `diffusers_model_id`.
2. Изменить DI, где создается `ProviderRegistry`:
   - зарегистрировать `DiffusersProvider` под ключом `"diffusers"`
   - читать `providers_default_name` из настроек и использовать в `get_default`.
3. Убедиться, что ENV переменные корректно маппятся в эти настройки.

---

### ✅ 6. `docs(backend): document provider abstraction and default provider config`

**Цель:** описать слой провайдеров в документации.

**Что сделать:**

1. В `docs/ru` и `docs/en` создать или обновить файлы, например:
   - `docs/ru/backend_providers.md`
   - `docs/en/backend_providers.md`
2. Описать:
   - что такое `IImageProvider`
   - что такое `GenerationRequest` и `GenerationResult`
   - как устроен `ProviderRegistry`
   - как выбрать дефолтный провайдер через настройки.
3. В общей архитектурной схеме бэкенда добавить блок Provider Layer.

---

## Stage 2. Queue and Workers for Generation

Цель этапа: перевести тяжелую генерацию в очередь и воркеры, а HTTP оставить легким.

### ✅ 7. `feat(queue): introduce TaskQueue abstraction with Redis backend`

**Цель:** создать абстракцию очереди задач.

**Что сделать:**

1. Создать модуль:
   - `app/infra/queue/task_queue.py`
2. Определить интерфейс `TaskQueue`:
   - `enqueue(payload: dict[str, Any]) -> str`
   - `get_status(task_id: str) -> dict[str, Any]`
   - при необходимости вспомогательные методы для обновления статуса.
3. Реализовать Redis версию:
   - использовать UUID как `task_id`
   - хранить задачи и статусы в Redis, например:
     - очередь: список или stream
     - статусы: hash по ключу `task:{id}`.
4. Подготовить DI функцию `get_task_queue()`, использующую текущий Redis клиент.

---

### ✅ 8. `feat(workers): add generation worker consuming TaskQueue`

**Цель:** выделить воркер для обработки задач.

**Что сделать:**

1. Создать файл:
   - `app/workers/generation_worker.py`
2. Реализовать `async def run_worker()`:
   - бесконечный цикл:
     - блокирующее или полублокирующее чтение задачи из очереди
     - преобразование payload в `GenerationRequest` и вспомогательные данные (user_id и т.д.)
     - выбор провайдера через `ProviderRegistry`
     - вызов `provider.generate`
     - сохранение результата в БД, файловой системе
     - обновление статуса задачи в Redis.
3. Обработка ошибок:
   - ловить исключения
   - помечать задачу как `failed`
   - логировать ошибку.

---

### ✅ 9. `feat(api): change generate endpoint to async task model`

**Цель:** запрос на генерацию не блокирует HTTP до конца инференса.

**Что сделать:**

1. Найти endpoint генерации, например:
   - `POST /api/v1/images/generate`
2. Изменить обработчик:
   - получить входные данные
   - сформировать `payload`, пригодный для воркера:
     - prompt, параметры генерации
     - user_id
     - параметры безопасности при необходимости.
   - `task_id = task_queue.enqueue(payload)`
   - вернуть клиенту JSON: `{"task_id": task_id, "status": "queued"}`.
3. Убедиться, что сервисы и use cases больше не выполняют реальную генерацию внутри этого запроса.

---

### ✅ 10. `feat(api): add generation status endpoint`

**Цель:** дать клиенту способ узнать статус задачи.

**Что сделать:**

1. Добавить endpoint:
   - `GET /api/v1/images/status/{task_id}`
2. В обработчике:
   - `status = task_queue.get_status(task_id)`
   - если нет записи, вернуть 404
   - если `completed`, вернуть:
     - статус
     - ссылку на изображение
     - метаданные
   - если `failed`, вернуть статус и описание ошибки
   - если `queued` или `running`, вернуть статус и при желании прогресс.

---

### ✅ 11. `chore(infra): add worker process entrypoint and compose wiring`

**Цель:** внедрить воркер в окружение.

**Что сделать:**

1. Создать entrypoint:
   - `app/entrypoints/generation_worker.py` с запуском `run_worker()`.
2. В `docker-compose.yml`:
   - добавить сервис `generation_worker`:
     - использовать тот же образ, что и backend
     - команду запуска воркера
     - общие сети, Redis, БД.
3. При наличии другого оркестратора подготовить соответствующий конфиг.

---

### ✅ 12. `docs(backend): document generation queue, workers and status api`

**Цель:** задокументировать новую модель обработки генерации.

**Что сделать:**

1. В документации:
   - описать жизненный цикл:
     - запрос → постановка задачи → обработка воркером → статус
   - описать форматы:
     - `task_id`
     - статусы задач.
2. Описать API:
   - `POST /generate`
   - `GET /status/{task_id}`
3. В разделе про деплой описать запуск воркера и его зависимости.

---

## Stage 3. Repositories and Unit of Work

Цель этапа: отделить домен от SQLAlchemy и централизовать транзакции.

### ✅ 13. `feat(repositories): add base repository interfaces for entities`

**Цель:** определить базовые интерфейсы репозиториев.

**Что сделать:**

1. Создать файл:
   - `app/domain/repositories/base.py`
2. Определить `IRepository[T]`:
   - `async def add(self, entity: T) -> None`
   - `async def get(self, id: int | str) -> T | None`
   - `async def list(self, **filters) -> list[T]`
   - `async def delete(self, id: int | str) -> None`
3. Определить интерфейсы:
   - `IGenerationRepository(IRepository[Generation])`
   - `IUserRepository(IRepository[User])`
   - и другие по мере необходимости.

---

### ✅ 14. `feat(repositories): implement generation repository on SQLAlchemy`

**Цель:** вынести работу с генерациями в отдельный репозиторий.

**Что сделать:**

1. Создать файл:
   - `app/infra/repositories/generation_repository.py`
2. Реализовать `SqlAlchemyGenerationRepository(IGenerationRepository)`:
   - хранит `AsyncSession`
   - методы:
     - `add`
     - `get`
     - `list_by_user(user_id: ...)`
     - `update_status`
3. Найти код, который делает SQL запросы по генерациям напрямую, и заменить на вызовы репозитория.

---

### ✅ 15. `feat(repositories): implement user repository and auth helpers`

**Цель:** вынести работу с пользователями.

**Что сделать:**

1. Создать файл:
   - `app/infra/repositories/user_repository.py`
2. Реализовать `SqlAlchemyUserRepository(IUserRepository)`:
   - методы:
     - `get_by_id`
     - `get_by_email` или `get_by_username`
     - `add`
     - `list`
     - при необходимости `delete`.
3. Обновить сервисы авторизации и профилей, чтобы они использовали репозиторий, а не Session.

---

### ✅ 16. `feat(uow): introduce UnitOfWork abstraction for db transactions`

**Цель:** управляющая сущность для транзакций.

**Что сделать:**

1. Создать файл:
   - `app/infra/uow.py`
2. Реализовать `class UnitOfWork` или `class SqlAlchemyUnitOfWork`:
   - свойства:
     - `users: IUserRepository`
     - `generations: IGenerationRepository`
   - методы:
     - `async def __aenter__(self) -> UnitOfWork`
     - `async def __aexit__(self, exc_type, exc, tb)`
       - при успехе `commit`
       - при ошибке `rollback`.
3. Внутри `__aenter__` создавать `AsyncSession` и репозитории, а в `__aexit__` закрывать сессию.
4. Добавить DI функцию `get_uow()`.

---

### ✅ 17. `refactor(services): migrate services to repository and UnitOfWork pattern`

**Цель:** сервисы больше не используют Session напрямую.

**Что сделать:**

1. В сервисах, которые работают с БД:
   - заменить зависимость Session на UnitOfWork.
2. Каждую бизнес операцию, которая требует транзакцию:
   - обернуть в `async with uow:`
   - использовать `uow.users`, `uow.generations` вместо прямого доступа к БД.
3. Удалить из сервисов вызовы:
   - `session.add`, `session.commit`, `session.rollback`.

---

### ✅ 18. `refactor(api): stop using raw db session in handlers`

**Цель:** обработчики HTTP не работают с БД напрямую.

**Что сделать:**

1. В роутерах:
   - убрать зависимости `Session` из сигнатур обработчиков.
2. Внедрить вместо этого:
   - use case или сервис, который внутри использует UnitOfWork.
3. Проверить, что ни один handler не делает SQL напрямую.

---

### ✅ 19. `docs(backend): document repositories and unit of work layer`

**Цель:** зафиксировать в документации новый слой данных.

**Что сделать:**

1. В архитектурной документации:
   - добавить описание:
     - Repository layer
     - UnitOfWork
     - схема: API → Use Case → UnitOfWork → Repositories → БД.
2. Добавить правила:
   - прямой Session не используется
   - все операции идут через UoW и репозитории.

---

## Stage 4. Application Use Cases Layer

Цель этапа: вынести сценарии в отдельный слой Use Case.

### ❌ 20. `feat(application): introduce use case layer with base Command`

**Цель:** создать каркас Application слоя.

**Что сделать:**

1. Создать пакет:
   - `app/application/use_cases/`
2. Определить базовые сущности:
   - `Command` как dataclass или base class
   - `UseCaseResult` с полями `success`, `data`, `error`.
3. Определить протокол use case:
   - `class UseCase(Protocol):`
     - `async def __call__(self, command: Command) -> UseCaseResult`.

---

### ❌ 21. `feat(application): add GenerateImageUseCase`

**Цель:** вынести генерацию в use case.

**Что сделать:**

1. Создать файл:
   - `app/application/use_cases/generate_image.py`
2. Определить `GenerateImageCommand` с параметрами:
   - `user_id`
   - `prompt`
   - `negative_prompt`
   - настройки генерации.
3. Реализовать `GenerateImageUseCase`:
   - зависимости:
     - `UnitOfWork`
     - `ProviderRegistry`
     - `TaskQueue` при работе через очередь.
   - логика:
     - валидация прав и лимитов
     - подготовка payload или `GenerationRequest`
     - постановка задачи в очередь
     - запись записи в БД через UoW
     - возврат `UseCaseResult` с `task_id`.

---

### ❌ 22. `feat(application): add GetGenerationStatusUseCase`

**Цель:** вынести получение статуса в use case.

**Что сделать:**

1. Создать файл:
   - `app/application/use_cases/get_generation_status.py`
2. Определить `GetGenerationStatusCommand` с полем `task_id` или `generation_id`.
3. Реализовать `GetGenerationStatusUseCase`:
   - зависимости:
     - `TaskQueue`
     - `UnitOfWork` при необходимости.
   - логика:
     - получить статус
     - получить запись из БД, если нужно
     - собрать `UseCaseResult` с полями для ответа API.

---

### ❌ 23. `refactor(api): delegate generation endpoints to use cases`

**Цель:** роутеры используют только use cases.

**Что сделать:**

1. В роутере генерации:
   - добавить зависимости `GenerateImageUseCase`, `GetGenerationStatusUseCase`.
2. В обработчиках:
   - собрать команду
   - вызвать use case
   - маппить `UseCaseResult` в HTTP ответ.
3. Удалить из роутеров прямую работу с сервисами и UoW.

---

### ❌ 24. `refactor(services): slim down services to pure domain helpers`

**Цель:** сервисы становятся более узкими.

**Что сделать:**

1. Просмотреть сервисы:
   - удалить из них orchestration логики
   - оставить только:
     - доменные операции
     - хелперы по бизнес правилам.
2. Если какие то сервисы стали дублировать use cases, перенести логику в use cases и удалить лишнее.

---

### ❌ 25. `docs(backend): document application use case layer and api flow`

**Цель:** описать новый поток данных.

**Что сделать:**

1. В документации:
   - добавить раздел про Application Layer
   - схему:
     - HTTP Handler → DTO → Use Case → UoW → Repositories → Providers → Queue.
2. Описать, как добавлять новые use cases и где им место в структуре.

---

## Stage 5. Async ORM and Event Loop Safety

Цель этапа: убрать блокирующие операции БД из event loop.

### ❌ 26. `feat(db): switch to async SQLAlchemy engine and session`

**Цель:** перейти на async SQLAlchemy.

**Что сделать:**

1. В `app/infra/db.py`:
   - заменить `create_engine` на `create_async_engine`
   - создать `async_sessionmaker`.
2. Обновить места, где используется старый engine или sessionmaker.
3. Настроить миграции:
   - или оставить их на sync engine отдельно
   - или использовать async режим Alembic, если это уже предусмотрено.

---

### ❌ 27. `refactor(repositories): migrate repositories to async API`

**Цель:** привести репозитории к async стилю.

**Что сделать:**

1. В репозиториях:
   - заменить `session.execute` на `await session.execute`
   - заменить остальные sync методы на async варианты.
2. Сделать все методы репозиториев `async def`.
3. Обновить все вызовы репозиториев, добавив `await`.

---

### ❌ 28. `refactor(services): remove blocking db calls from async code`

**Цель:** убрать sync БД вызовы из async функций.

**Что сделать:**

1. Найти все места, где в async коде вызываются sync функции БД.
2. Перевести их на async вариант.
3. В крайних случаях обернуть в `asyncio.to_thread`, но по возможности избегать.
4. Проверить ключевые сценарии генерации и статусов.

---

### ❌ 29. `chore(tests): update db fixtures for async session`

**Цель:** привести тесты к async БД.

**Что сделать:**

1. Обновить фикстуры:
   - использовать async engine и async session.
2. Если используется pytest:
   - добавить `pytest.mark.asyncio` там, где нужно.
3. Обновить helpers, которые создают тестовые данные, под async.

---

### ❌ 30. `docs(backend): document async orm and concurrency model`

**Цель:** зафиксировать модель конкурентности.

**Что сделать:**

1. В документации:
   - описать, что:
     - БД работает через async ORM
     - все операции с БД должны быть async
   - описать:
     - роль очередей и воркеров
     - куда можно и нельзя класть тяжелый код.
2. Добавить краткие правила:
   - внутри HTTP обработчика никаких тяжелых операций
   - всё тяжелое через воркеры.

---

## Stage 6. Observability, Errors, Feature Flags, Events

Цель этапа: укрепить прод готовность и наблюдаемость.

### ❌ 31. `feat(core): add typed domain exceptions and error mapping`

**Цель:** единая система доменных ошибок.

**Что сделать:**

1. Создать файл:
   - `app/core/exceptions.py`
2. Определить:
   - `class DomainException(Exception)` с полями:
     - `code: str`
     - `message: str`
     - `details: dict[str, Any] | None`
3. Определить:
   - `GenerationFailedException`
   - `ProviderUnavailableException`
   - `RateLimitExceededException`
   - другие по необходимости.
4. Добавить функцию:
   - `map_exception_to_http(e: Exception) -> tuple[int, dict]`.

---

### ❌ 32. `feat(api): implement global error handler with structured responses`

**Цель:** единый формат ошибок в API.

**Что сделать:**

1. В конфигурации фреймворка:
   - зарегистрировать глобальный обработчик исключений.
2. В обработчике:
   - если это `DomainException`, использовать `map_exception_to_http`
   - если нет, маппить в 500 с generic сообщением.
3. Формат ответа:
   - `{"error": {"code": "...", "message": "...", "details": {...}}, "request_id": "..."}`.

---

### ❌ 33. `feat(metrics): extend metrics for providers and queue processing`

**Цель:** метрики провайдеров и очередей.

**Что сделать:**

1. Добавить счетчики и таймеры:
   - время ответа провайдера
   - число успешных и неуспешных генераций
   - длина очереди
   - время обработки задачи воркером.
2. Встроить метрики:
   - в use cases
   - в воркер
   - в provder layer.
3. Обеспечить экспорт метрик в Prometheus или другую систему.

---

### ❌ 34. `feat(config): introduce feature flags for providers and features`

**Цель:** управляемое включение и выключение фич.

**Что сделать:**

1. В настройках:
   - добавить секцию `feature_flags`, например `dict[str, bool]` или отдельный класс.
2. Создать сервис:
   - `FeatureFlagService` с методами `is_enabled(name: str) -> bool`.
3. Использовать:
   - при выборе провайдера
   - при включении новых маршрутов или режимов работы.

---

### ❌ 35. `feat(events): introduce simple domain event bus`

**Цель:** добавить доменные события.

**Что сделать:**

1. Создать файл:
   - `app/core/events.py`
2. Определить:
   - `class DomainEvent` с полями `name`, `occurred_at`, `payload`.
3. Реализовать `EventBus`:
   - регистрация обработчиков
   - метод `publish(event: DomainEvent)`.
4. Добавить события:
   - `ImageGeneratedEvent`
   - `GenerationFailedEvent`
5. В use cases:
   - публиковать события при успешной генерации и при ошибках.

---

### ❌ 36. `docs(backend): document errors, metrics, feature flags and domain events`

**Цель:** задокументировать наблюдаемость и управление.

**Что сделать:**

1. В документации:
   - раздел про ошибки:
     - иерархия исключений
     - формат API ошибок.
   - раздел про метрики:
     - какие есть
     - как читать.
   - раздел про feature flags:
     - как включать и выключать.
   - раздел про события:
     - какие события есть
     - как подписываться обработчикам.

---

## Stage 7. Tests and Coverage

Цель этапа: собрать полноценную тестовую базу.

### ❌ 37. `test(application): add tests for GenerateImageUseCase flows`

**Цель:** покрыть ключевой use case.

**Что сделать:**

1. Создать тесты для `GenerateImageUseCase`:
   - успешная генерация
   - провайдер недоступен
   - фича отключена фич флагом
   - лимиты пользователя превышены.
2. Замокать:
   - `UnitOfWork`
   - `ProviderRegistry` или конкретный провайдер
   - `TaskQueue`.

---

### ❌ 38. `test(repositories): add integration tests for core repositories`

**Цель:** проверить работу репозиториев с реальной БД.

**Что сделать:**

1. Написать тесты для:
   - `SqlAlchemyGenerationRepository`
   - `SqlAlchemyUserRepository`
2. Использовать тестовую БД:
   - либо отдельный контейнер
   - либо in memory, если это реально.
3. Проверить CRUD операции и специфичные методы фильтрации.

---

### ❌ 39. `test(providers): add provider tests with mocked external services`

**Цель:** протестировать логику провайдеров.

**Что сделать:**

1. Для локального `DiffusersProvider`:
   - замокать тяжелые вызовы, чтобы не запускать реальную модель
   - проверить сбор `GenerationResult` и обработку настроек.
2. Для внешних провайдеров (если есть):
   - замокать HTTP клиент
   - проверить сценарии ошибок, таймаутов и нестандартных ответов.

---

### ❌ 40. `test(queue): add tests for TaskQueue and worker lifecycle`

**Цель:** протестировать очередь и воркер.

**Что сделать:**

1. Написать тесты для `TaskQueue`:
   - постановка задач
   - чтение статуса
   - переходы статусов.
2. Тесты для воркера:
   - воркер берет задачу
   - вызывает провайдера
   - обновляет статус.
3. Тест для ошибки провайдера:
   - воркер корректно помечает задачу как `failed`.

---

### ❌ 41. `chore(testing): ensure minimum coverage threshold for backend`

**Цель:** зафиксировать минимальный порог покрытия тестами.

**Что сделать:**

1. В конфигурации тестов:
   - добавить `--cov` и `--cov-fail-under=<процент>` (например 80) для backend пакетов.
2. В CI:
   - убедиться, что задача падает при низком покрытии.

---

### ❌ 42. `docs(backend): update testing strategy and coverage targets`

**Цель:** описать тестовую стратегию.

**Что сделать:**

1. В документации:
   - описать уровни тестов:
     - unit
     - integration
     - e2e при наличии.
   - описать цели по покрытию
   - описать правила:
     - когда писать unit
     - когда нужен integration
     - как поднимать тестовую БД
     - как запускать тесты локально и в CI.

---

Конец плана.
