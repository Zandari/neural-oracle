# Neural Oracle 🔮
<img src="https://github.com/Zandari/neural-oracle/blob/master/images/screenshot.png?raw=true" alt="screenshot" width="500" />

Проект Neural Oracle - это интерактивный чат-бот, который использует нейронные сети для генерации ответов на вопросы пользователей. Провайдером LLM-моделей является OpenRouter.Разработан в рамках тестового задания.

## Инструкции по запуску

Ключ доступа к API OpenRouter можно получить в [личном кабинете](https://openrouter.ai/settings/keys).
Список доступных моделей можно посмотреть в [документации](https://openrouter.ai/models?fmt=cards&input_modalities=text&output_modalities=text).

Для запуска приложения в Docker-контейнере, выполните следующие команды:

```sh
docker build -t neural-oracle:local .

docker run -d --name neural-oracle \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY="your-api-key" \
  -e OPENROUTER_MODEL="bytedance-seed/seed-2.0-mini" \
  neural-oracle:local
  
docker exec -it neural-oracle sh -lc 'poetry run user-manager add test_user'
```

В терминале выведится ключ доступа для тестового пользователя. Строка следующего вида: 
```
========================================
User added successfully!
Name: test_user
Access Token (save this - it won't be shown again):
4d785d22-3103-4391-8471-e8c01f5082a0
========================================
```

Остановка и удаление контейнера:
```sh
docker stop neural-oracle
docker rm neural-oracle
```

## Пояснение к стеку

В качестве backend фреймворка был выбран FastAPI, т.к. он позволяет быстро разрабатывать RESTful API и имеет богатый функционал для работы с HTTP-запросами и ответами.

База данных для хранения пользователей и их ключей доступа реализована с использованием SQLite и в частности библиотеки aiosqlite для организации асинхронного доступа к БД. Выбор был обусловлен контекстом выполнения проекта (тестовое задание) и простотой использования. Доступ к БД осуществляется посредством SQL запросом, без использования ORM с целью минимизирования зависимостей.

Взаимодействие с LLM-моделями осуществляется http-запросами, без использования библиотек реализующих интерфейс. Данное решение было принято с целью изучения предоставляемого провайдером API и минимизирования зависимостей. Для запросов использовалась библиотека aiohttp.

На фронтенде используются ванильные HTML/CSS/JS согласно ТЗ.

## Структура проекта

```
app                     # backend
├── __init__.py
├── app.py              # входная точка
├── config.py           # переменные конфигурации 
├── dependencies.py     # зависимости endpoint'ов
├── llm                 # пакет реализующий доступ к LLM
├── models.py           # модели данных pydantic
├── repository          # пакет реализующий доступ к БД
├── security.py         # функции для работы с ключами доступа
└── router.py           # endpoint'ы
scripts                 # скрипты администратора 
├── __init__.py
├── cli.py              # cli для редактирования пользователей
static                  # frontend
├── auth.html           # страница авторизации
├── index.html          # страница приложения
├── script.js
└── style.css
Dockerfile
poetry.lock
pyproject.toml
README.md
```

## Что можно доработать

- Заменить SQLite на PostgreSQL или рассмотреть MongoDB.
- Использовать ORM(SQLAlchemy, Peewee) с целью обеспечения безопасного доступа и проведения автоматических миграция.
- Использовать nginx для раздачи статического контента (в текущей реализации это делает FastAPI и uvicorn).
- Реализовать тестирование приложения. Как backend, так и frontend.
- Более детальные ошибки API.
- Интеграция систем мониторинга (Prometheus, Grafana).
- CI/CD.

## Примечание
- Для деплоя приложения в текущей реализации, следует сохранять файл БД используя docker volume. Это не было сделано, т.к. подразумевается что приложение будет запущено один раз проверяющим.
- Ключи доступа хешируются.
