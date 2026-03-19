# TeleReposter

**TeleReposter** --- это ПО для автоматического кросспостинга сообщений
в Telegram. Оно отслеживает указанные Telegram-каналы и RSS-ленты и
пересылает новые записи в заданные каналы или чаты.

------------------------------------------------------------------------

## 📦 Установка

Перейдите в директорию `/opt` (или другую, где вы размещаете проекты):

``` bash
cd /opt
```

### Клонирование репозитория

``` bash
git clone https://github.com/aksofty/TeleReposter.git
cd TeleReposter
```

### Подготовка окружения

``` bash
mkdir -p volumes/{data,logs}
cp app/data/db_sources.example.json volumes/data/db_sources.json
cp app/data/db_rss_sources.example.json volumes/data/db_rss_sources.json
touch volumes/all_logs.log
touch .env
```

------------------------------------------------------------------------

## ⚙️ Конфигурация

### Файлы источников

-   `volumes/data/db_sources.json` --- список
    Telegram-каналов-источников
-   `volumes/data/db_rss_sources.json` --- список RSS-лент

Оба файла имеют формат **JSON** и должны быть заполнены в соответствии с
вашими источниками.

------------------------------------------------------------------------

## 🔐 Переменные окружения (.env)

Пример содержимого:

``` env
# Данные приложения Telegram (получить на my.telegram.org)
CLIENT_ID=ваш_app_id
CLIENT_TOKEN=ваш_app_hash

# Имя сессии (необязательно)
SESSION_NAME=my_session

# Пути к файлам внутри контейнера (менять не рекомендуется)
DB_SOURCES_FILE=app/data/db_sources.json
DB_RSS_SOURCES_FILE=app/data/db_rss_sources.json
LOG_FILE=app/logs/all_logs.log

# Интеграция с gen-api (опционально)
GEN_API_KEY=ваш_api_ключ
GEN_API_MODEL=название_модели
```

------------------------------------------------------------------------

## 🚀 Запуск с Docker

После настройки выполните:

``` bash
docker compose up -d --build
```

Контейнер будет работать в фоновом режиме.

Логи сохраняются в файл, указанный в `LOG_FILE`.