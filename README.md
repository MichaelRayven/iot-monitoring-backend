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

Как определять тип устройства?
Пока что предоставляется пользователем

### Запуск приложение
docker compose -f infra/docker/docker-compose.yaml up --build
uv run alembic upgrade head

### TODO:
- [ ] Add prek and ruff
- [ ] Define out schemas for floors and devices
- [ ] Define in schemas for floor and device updates
- [ ] Upload files directly to S3 with presigned urls (pass key to create floor, optional)
- [ ] Define websocket subscribe request message schema
- [ ] Define websocket unsubscribe request message schema
- [ ] Define websocket rx message schema
- [ ] Create floor service
- [ ] Create floor device service
- [ ] Extract helper function from payload_decoders into utils 
- [ ] Use strategies for payload decoders
- [ ] Create decoder service
- [ ] Test concurrent request handling by VegaClient
- [ ] Test realtime updates handling by VegaClient and ConnectionManager
- [ ] Add support for more devices (list models here...)
- [ ] Authenticate users with JWT