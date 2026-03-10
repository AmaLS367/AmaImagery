# Документация развертывания

## Обзор

Комплексные руководства по развертыванию AI Image Generator в production окружении, включая облачное развертывание, конфигурацию окружения и процедуры обслуживания.

## Варианты развертывания

### 🐳 Docker развертывание (рекомендуется)
- Самый простой для развертывания и поддержки
- Согласованность между окружениями
- Встроенная оркестрация с Docker Compose
- См. [Документация Docker](../docker/README.md)

### ☁️ Облачное развертывание
- Поддержка AWS, GCP, Azure
- Конфигурации Kubernetes
- Возможности автомасштабирования
- Интеграция управляемых сервисов

### 🖥️ Bare Metal
- Максимальная производительность
- Прямой доступ к GPU
- Кастомная оптимизация
- Ручное управление зависимостями

## Разделы документации

- [Требования](./requirements.md) - Системные требования
- [Окружение](./environment/) - Настройка окружения
  - [Переменные окружения](./environment/environment-variables.md)
  - [Управление секретами](./environment/secrets-management.md)
  - [Конфигурация](./environment/configuration.md)
- [Production](./production/) - Production развертывание
  - [Чеклист](./production/checklist.md)
  - [Безопасность](./production/security.md)
  - [SSL сертификаты](./production/ssl-certificates.md)
  - [Мониторинг](./production/monitoring.md)
  - [Масштабирование](./production/scaling.md)
- [Облако](./cloud/) - Облачные руководства
  - [AWS](./cloud/aws.md)
  - [GCP](./cloud/gcp.md)
  - [Azure](./cloud/azure.md)
  - [DigitalOcean](./cloud/digitalocean.md)
- [Обслуживание](./maintenance.md) - Текущее обслуживание
- [Rollout провайдеров](./provider-rollout.md) - Профили верификации Diffusers и ComfyUI и rollout policy

## Быстрый старт

### Чеклист Production развертывания

1. ✅ Проверьте [Системные требования](./requirements.md)
2. ✅ Настройте [Переменные окружения](./environment/environment-variables.md)
3. ✅ Установите [SSL сертификаты](./production/ssl-certificates.md)
4. ✅ Настройте [Безопасность](./production/security.md)
5. ✅ Настройте [Мониторинг](./production/monitoring.md)
6. ✅ Разверните используя [Docker](../docker/compose/production-setup.md)
7. ✅ Проверьте smoke тестами
8. ✅ Настройте [Бэкап](../operations/backup-restore.md)

## Минимальные требования

- **CPU:** 4 ядра (8+ рекомендуется)
- **RAM:** 16GB (32GB+ рекомендуется)
- **GPU:** NVIDIA GPU с 6GB+ VRAM
- **Хранилище:** 50GB+ SSD
- **ОС:** Linux (Ubuntu 20.04+)
- **Docker:** 20.10+
- **CUDA:** 11.8+ с NVIDIA драйверами

