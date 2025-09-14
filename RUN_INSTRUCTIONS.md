# 🚀 Инструкция по запуску GenAI приложения

## 📋 Требования

- Python 3.8+
- Виртуальное окружение (рекомендуется)

## 🔧 Установка

1. **Создайте виртуальное окружение:**
   ```bash
   python -m venv .venv
   ```

2. **Активируйте виртуальное окружение:**
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Запуск

### Вариант 1: Простой запуск (без Redis)
```bash
python run_simple.py
```

### Вариант 2: Полный запуск (с Redis)
```bash
python run_dev.py
```

### Вариант 3: Оригинальный запуск
```bash
python run.py
```

## 🌐 Доступ к приложению

После запуска приложение будет доступно по адресам:

- **API:** http://localhost:8000
- **Документация API:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## ⚙️ Настройки

### Переменные окружения

Вы можете настроить приложение через переменные окружения:

```bash
# Основные настройки
export ENV=dev
export SECRET_KEY=your-secret-key
export DATABASE_URL=sqlite:///./genai.db
export REDIS_URL=redis://localhost:6379/0

# Отключить Redis (для простого тестирования)
export NO_REDIS=1

# Настройки модели
export DEVICE=CUDA
export MAX_STEPS=20
export MAX_SIZE=512
```

### Конфигурация по умолчанию

- **База данных:** SQLite (genai.db)
- **Redis:** localhost:6379 (можно отключить)
- **Порт:** 8000
- **Логирование:** INFO уровень

## 🐛 Устранение неполадок

### Ошибка "REDIS_URL must include a password"
- Используйте `python run_simple.py` (отключает Redis)
- Или установите переменную `NO_REDIS=1`

### Ошибка "SECRET_KEY must be set"
- Установите переменную `SECRET_KEY=your-secret-key`
- Или используйте `run_simple.py` (устанавливает автоматически)

### Ошибка подключения к базе данных
- Проверьте, что файл `genai.db` создается
- Убедитесь, что у вас есть права на запись в директорию

### Ошибка импорта модулей
- Убедитесь, что вы находитесь в корневой директории проекта
- Проверьте, что все зависимости установлены

## 📁 Структура проекта

```
genai/
├── app/                    # Основной код приложения
│   ├── main.py            # Главный файл FastAPI
│   ├── config.py          # Конфигурация
│   ├── services/          # Бизнес-логика
│   ├── routes/            # API роуты
│   └── ...
├── run.py                 # Оригинальный запуск
├── run_dev.py             # Запуск для разработки
├── run_simple.py          # Простой запуск (без Redis)
└── requirements.txt       # Зависимости
```

## 🔍 Тестирование

После запуска проверьте:

1. **Health Check:** http://localhost:8000/health
2. **API Docs:** http://localhost:8000/docs
3. **Генерация изображений:** POST http://localhost:8000/generate

## 📝 Логи

Логи сохраняются в папке `logs/`:
- `app/` - логи приложения
- `access/` - логи доступа
- `errors/` - логи ошибок
- `generations/` - логи генерации

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте логи в папке `logs/`
2. Убедитесь, что все зависимости установлены
3. Попробуйте запустить с `run_simple.py`
4. Проверьте переменные окружения
