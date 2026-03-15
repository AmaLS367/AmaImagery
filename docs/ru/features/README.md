# Документация функций

## Обзор

| Символ | Значение |
|--------|---------|
| ✅ | Доступно |
| 🧪 | Зависит от provider-а или окружения |
| 🚧 | Запланировано, публично недоступно |

## Статус функций

| Функция | Статус | Примечание |
|---------|--------|------------|
| Text-to-image генерация | ✅ Доступно | Публичный flow через `/api/v1/images/generate` |
| Polling статуса генерации | ✅ Доступно | `/api/v1/images/status/{task_id}` |
| История генераций | ✅ Доступно | `/api/v1/users/me/generations` |
| Пользовательские настройки | ✅ Доступно | `/api/v1/users/me/settings` |
| Hygiene mode | ✅ Доступно | `/api/v1/users/me/hygiene-mode` |
| NSFW moderation routes | ✅ Доступно | Под `/api/v1/nsfw/*` |
| Signed file delivery | ✅ Доступно | Через `/api/v1/file` |
| Admin pages | ✅ Доступно | Под `/admin/*` |
| Локальный Diffusers runtime | 🧪 Поддерживается | Зависит от окружения и provider config |
| Внешний ComfyUI runtime | 🧪 Поддерживается | Зависит от окружения и provider config |
| Редактирование изображений | 🚧 Planned / not public | Пока не опубликовано как public API |
| Upscaling | 🚧 Planned / not public | Пока не опубликовано как public API |
| Resize | 🚧 Planned / not public | Пока не опубликовано как public API |

## Основные функции

### 🎨 Генерация изображений
Генерация изображений через async job flow.

**Возможности:**
- text-to-image генерация
- отправка prompt и negative prompt
- параметры генерации: width, height, steps, guidance
- выполнение через `comfyui` или `diffusers`

### 🛡️ Модерация контента
Moderation и hygiene controls.

**Возможности:**
- переключатель NSFW preference
- маршруты просмотра и reload правил
- поддержка prompt hygiene mode

### 📁 Управление файлами

**Возможности:**
- signed file access flow
- download path для артефактов
- persisted output handling через lifecycle worker-а

## Planned / Coming Soon Areas

- `Image Editing` — Coming soon
- `Image Upscaling` — Coming soon
- `Image Resizing` — Coming soon
- более глубокие feature playbooks и walkthroughs — Coming soon

## API Endpoints

- `POST /api/v1/images/generate` - Генерация изображений
- `GET /api/v1/images/status/{task_id}` - Получение статуса
- `GET /api/v1/users/me/generations` - История генераций
- `GET/PATCH /api/v1/users/me/settings` - Пользовательские настройки
- `GET/PATCH /api/v1/users/me/hygiene-mode` - Hygiene mode
- `PATCH /api/v1/nsfw/users/me/nsfw` - Переключение NSFW preference
- `POST /api/v1/nsfw/check` - Проверка текста по moderation rules
- `GET /api/v1/file` - Скачивание signed artifact

Смотрите также [Reference](../reference/README.md).
