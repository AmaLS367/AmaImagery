# Слой абстракции провайдеров

## Обзор

Слой абстракции провайдеров отделяет приложение от конкретных реализаций генерации изображений, позволяя переключаться между разными провайдерами (diffusers, внешние API и т.д.) без изменения кода приложения.

## Архитектура

```
┌─────────────────┐
│  API / Services │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ProviderRegistry│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ IImageProvider   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼───┐
│Diffusers│ │External│
│Provider │ │Provider │
└────────┘ └────────┘
```

## Основные компоненты

### IImageProvider

Протокол-интерфейс, который должны реализовывать все провайдеры генерации изображений:

```python
class IImageProvider(Protocol):
    async def generate(request: GenerationRequest) -> GenerationResult
    async def health_check() -> bool
    def supports_features(features: set[str]) -> bool
```

**Назначение:** Определяет единый контракт для генерации изображений, позволяя приложению работать с любым провайдером через единый интерфейс.

### GenerationRequest

Доменный DTO, содержащий все параметры, необходимые для генерации изображения:

- `prompt: str` - Основной промпт генерации
- `negative_prompt: Optional[str]` - Негативный промпт
- `seed: Optional[int]` - Случайное зерно для воспроизводимости
- `width: int` - Ширина изображения
- `height: int` - Высота изображения
- `steps: Optional[int]` - Количество шагов инференса
- `guidance_scale: Optional[float]` - Масштаб guidance
- `ref_image_b64: Optional[str]` - Base64 изображение-референс для IP-Adapter
- `ip_scale: Optional[float]` - Масштаб IP-Adapter
- `style: Style` - Визуальный стиль ('realistic' или 'anime')

**Назначение:** Формат запроса, независимый от провайдера, который изолирует код приложения от специфичных для провайдера структур параметров.

### GenerationResult

Доменный DTO, содержащий результат генерации изображения:

- `image_path: str` - Путь к сгенерированному изображению
- `metadata: Dict[str, Any]` - Технические и бизнес метаданные

**Назначение:** Нормализует вывод от разных провайдеров, позволяя коду приложения единообразно работать с результатами.

### ProviderRegistry

Центральный реестр, который управляет экземплярами провайдеров и маршрутизирует запросы:

```python
class ProviderRegistry:
    def register(name: str, provider: IImageProvider) -> None
    def get(name: str) -> IImageProvider
    def get_default() -> IImageProvider
    def list_providers() -> list[str]
    async def health_report() -> Dict[str, bool]
```

**Назначение:** Изолирует код приложения от логики выбора провайдера, позволяя переключение провайдеров в runtime и мониторинг их состояния.

## Конфигурация

### Переменные окружения

- `PROVIDERS_DEFAULT_NAME` - Имя провайдера по умолчанию (по умолчанию: `"diffusers"`)
- `PROVIDERS_ENABLED` - Список включенных провайдеров через запятую (по умолчанию: `"diffusers"`)

### Пример конфигурации

```bash
PROVIDERS_DEFAULT_NAME=diffusers
PROVIDERS_ENABLED=diffusers
```

### Выбор провайдера по умолчанию

Провайдер по умолчанию выбирается через переменную окружения `PROVIDERS_DEFAULT_NAME`. Реестр использует это значение при вызове `get_default()`:

1. Если `default_name` задан и провайдер существует → возвращает этот провайдер
2. Иначе → возвращает первый зарегистрированный провайдер
3. Если провайдеры не зарегистрированы → выбрасывает `ValueError`

## Использование

### Получение провайдера из реестра

```python
from app.domain.providers import get_provider_registry

registry = get_provider_registry()
provider = registry.get_default()

result = await provider.generate(request)
```

### Проверка состояния провайдера

```python
registry = get_provider_registry()
health_status = await registry.health_report()
# Возвращает: {"diffusers": True, "external_api": False}
```

### Проверка поддержки функций

```python
provider = registry.get_default()
supports_ip = provider.supports_features({"ip_adapter"})
```

## Текущие провайдеры

### DiffusersProvider

Реализация, использующая библиотеку diffusers для локального инференса Stable Diffusion.

**Расположение:** `app/infra/providers/diffusers_provider.py`

**Возможности:**
- Генерация текст-в-изображение
- Поддержка IP-Adapter для кондиционирования изображений
- Управление устройствами и типами данных
- Контроль таймаутов
- Управление памятью

**Конфигурация:** Использует существующую конфигурацию моделей (`MODEL_ID`, `DEVICE`, `TORCH_DTYPE` и т.д.)

## Добавление новых провайдеров

Чтобы добавить новый провайдер:

1. Реализуйте интерфейс `IImageProvider`
2. Зарегистрируйте в функции `get_provider_registry()`
3. Добавьте имя провайдера в `PROVIDERS_ENABLED` при необходимости
4. Обновите `PROVIDERS_DEFAULT_NAME` для использования нового провайдера

Пример:

```python
# В app/infra/providers/external_api_provider.py
class ExternalAPIProvider:
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        # Реализация
        pass
    
    async def health_check(self) -> bool:
        # Реализация
        pass
    
    def supports_features(self, features: set[str]) -> bool:
        # Реализация
        pass

# В app/domain/providers/registry.py
def get_provider_registry() -> ProviderRegistry:
    # ...
    if "external_api" in settings.providers_enabled:
        from app.infra.providers.external_api_provider import ExternalAPIProvider
        providers["external_api"] = ExternalAPIProvider()
```

## Преимущества

- **Разделение:** Код приложения не зависит от конкретных ML библиотек
- **Гибкость:** Легко переключать или добавлять провайдеры
- **Тестируемость:** Провайдеры можно мокировать для тестов
- **Поддерживаемость:** Логика, специфичная для провайдера, изолирована

