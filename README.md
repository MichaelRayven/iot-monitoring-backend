### Работа с приложением

#### Зависимости

- [Пакетный менеджер uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Docker](https://www.docker.com/get-started/)

#### Локальная разработка

Установка
```bash
uv venv --python 3.13 # создаем виртуальное окружение
uv sync # загружаем библиотеки

docker compose -f infra/docker/docker-compose.local.yaml up --build -d # Запускаем инфраструктуру
uv run alembic upgrade head # применяем миграции для БД

uv run fastapi dev src/app/main.py # запуск тестового веб-сервера
```

#### Развертка в продакшен

```bash
docker compose -f infra/docker/docker-compose.prod.yaml up --build -d
```

### Endpoint'ы 
- залить изображение для этажа

- получение списка зарегестрированных устройств
- получение данных с устройства

- создание этажа
- удаление этажа
- список этажей
- обновление характеристик этажа

- добавление устройства на этаж
- удаление устройства с этажа
- обновление состояния устройства на этаже
- получение списка устройств на этаже

### Поддержка устройств:
- Smart-MS0101
- Smart-WB0101
- Beacon L
- Smart Badge