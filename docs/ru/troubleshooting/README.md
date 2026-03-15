# Документация устранения неполадок

## Обзор

Текущие проблемы, debugging paths и operational notes для **AmaImagery**.

## Быстрые ссылки

| Тема | Статус |
|------|--------|
| Common issues page | 🚧 Coming soon |
| Error code reference | 🚧 Coming soon |
| GPU-specific page | 🚧 Coming soon |
| Memory issues page | 🚧 Coming soon |
| Performance issues page | 🚧 Coming soon |

Пока именно эта README остаётся основной точкой входа в troubleshooting.

## Частые проблемы

### Проблемы установки

#### Проблема: локальный ML runtime не стартует
**Симптомы:** provider boot failures, missing models, missing CUDA или неподходящий dtype

**Проверки:**
1. проверьте model files и cache paths
2. проверяйте GPU/CUDA только если вы реально используете локальный Diffusers
3. проверьте provider env config

#### Проблема: фронтенд работает, но генерация не завершается
**Проверки:**
1. убедитесь, что worker process запущен
2. убедитесь, что PostgreSQL доступен
3. убедитесь, что выбранный provider usable

### Ошибки runtime

#### Проблема: ComfyUI flow не подключается
**Проверки:**
1. проверьте `COMFYUI_BASE_URL`
2. проверьте `COMFYUI_WEBSOCKET_URL`
3. проверьте доступность внешнего ComfyUI сервиса

#### Проблема: signed file access ломается
**Проверки:**
1. убедитесь, что артефакт существует
2. проверьте signing/TTL settings
3. проверьте, что URL rewriting не ломает download path

### Проблемы Docker

#### Проблема: контейнер сразу завершается
**Проверки:**
1. смотрите `docker compose logs`
2. проверяйте env files
3. проверяйте ports/volumes

## Получение помощи

1. Сначала откройте нужный section README
2. Соберите логи и точные команды
3. Зафиксируйте env/runtime/provider context
4. Повторите проблему на самом простом поддерживаемом flow
