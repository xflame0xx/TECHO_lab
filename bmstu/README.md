
# TECHO_lab

## Краткое описание проекта

**TECHO_lab** — учебный веб-проект на базе **Django**, подготовленный в рамках лабораторной работы №1 по первичной настройке проекта с соблюдением современных стандартов разработки.

Проект представляет собой серверное веб-приложение для работы с вакансиями и заявками соискателя. Пользователь может:

- просматривать список активных вакансий;
- открывать страницу конкретной вакансии;
- добавлять вакансии в черновик заявки;
- просматривать список своих заявок;
- редактировать профиль заявителя;
- изменять статус заявки;
- работать с изображениями вакансий через S3-совместимое хранилище.

Основная цель проекта в рамках лабораторной работы — не только реализовать рабочее приложение, но и показать корректную организацию окружения, инфраструктуры и инструментов качества кода:

- использование `.env` для конфигурации;
- настройка линтера и форматтера;
- настройка `pre-commit`;
- наличие `Dockerfile` и `docker-compose`;
- единый code style;
- наличие подробной проектной документации.

---

## Назначение проекта

Проект предназначен для демонстрации базовой организации Python/Django-проекта в учебной среде.

### В рамках лабораторной работы проверяются следующие аспекты

| Направление | Что должно быть настроено |
|---|---|
| Качество кода | Линтер, форматтер, `.gitignore` |
| Документация | Полный `README.md` |
| Автоматические проверки | `pre-commit` |
| Конфигурация | `.env` |
| Контейнеризация | `Dockerfile`, `docker-compose` |
| Code style | Единые правила именования |

---

## Предметная область

Проект моделирует процесс работы с вакансиями и заявками.

### Основные сущности

| Сущность | Назначение |
|---|---|
| `Vacancy` | Хранение информации о вакансии |
| `ApplicantProfile` | Профиль соискателя |
| `Application` | Заявка пользователя |
| `ApplicationVacancy` | Связь между заявкой и вакансиями |

### Базовые пользовательские сценарии

| Сценарий | Описание |
|---|---|
| Просмотр вакансий | Пользователь открывает список доступных вакансий |
| Просмотр детали вакансии | Пользователь изучает полную информацию о вакансии |
| Формирование заявки | Пользователь добавляет вакансии в черновик |
| Работа с профилем | Пользователь заполняет персональные данные |
| Управление статусом | Пользователь изменяет статус заявки |

---

## Архитектура проекта

Проект реализован как **монолитное Django-приложение** с серверным рендерингом HTML.

### Архитектурная схема

| Слой | Назначение |
|---|---|
| **Django Models** | Описание сущностей и работа с базой данных |
| **Django Views** | Обработка запросов и подготовка данных для шаблонов |
| **Django Templates** | Формирование HTML-страниц |
| **PostgreSQL** | Основное реляционное хранилище |
| **MinIO** | Хранение изображений и прочих медиафайлов |
| **Docker Compose** | Локальный запуск всех сервисов проекта |
| **Ruff** | Линтинг и форматирование Python-кода |
| **pre-commit** | Проверки перед коммитом |

### Общая логика взаимодействия

1. Пользователь обращается к Django-приложению.
2. Django получает данные из PostgreSQL.
3. При необходимости изображения и медиа берутся из MinIO.
4. Django формирует HTML-ответ через шаблоны.
5. Перед коммитом код автоматически проверяется через `pre-commit`.

---

## Описание файловой структуры проекта

Ниже приведена основная структура проекта.

```text
bmstu/
├── Docker/
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   └── nginx.conf
├── config/
│   ├── Asgi.py
│   ├── Settings.py
│   ├── Urls.py
│   ├── Wsgi.py
│   └── __init__.py
├── core/
│   ├── Admin.py
│   ├── Apps.py
│   ├── Models.py
│   ├── Tests.py
│   ├── Views.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── vacancies.html
│   ├── vacancy.html
│   ├── applications.html
│   └── application.html
├── scripts/
│   └── CheckFilenames.py
├── .env
├── .gitignore
├── .pre-commit-config.yaml
├── manage.py
├── pyproject.toml
├── requirements.txt
└── README.md
````

### Назначение директорий и файлов

| Путь                         | Назначение                              |
| ---------------------------- | --------------------------------------- |
| `Docker/`                    | Docker-конфигурация проекта             |
| `Docker/Dockerfile`          | Инструкция сборки контейнера приложения |
| `Docker/docker-compose.yaml` | Описание сервисов локального запуска    |
| `config/`                    | Конфигурация Django                     |
| `config/Settings.py`         | Основные настройки проекта              |
| `config/Urls.py`             | Маршрутизация приложения                |
| `config/Wsgi.py`             | WSGI entry point                        |
| `config/Asgi.py`             | ASGI entry point                        |
| `core/`                      | Основная бизнес-логика проекта          |
| `core/Models.py`             | Django-модели                           |
| `core/Views.py`              | Представления приложения                |
| `core/Tests.py`              | Тесты                                   |
| `templates/`                 | HTML-шаблоны                            |
| `scripts/`                   | Вспомогательные служебные скрипты       |
| `.env`                       | Переменные окружения                    |
| `.gitignore`                 | Игнорируемые Git-файлы                  |
| `.pre-commit-config.yaml`    | Конфигурация pre-commit                 |
| `pyproject.toml`             | Конфигурация Ruff                       |
| `requirements.txt`           | Python-зависимости                      |
| `manage.py`                  | Основная management-точка входа Django  |

---

## Используемые технологии

| Технология          | Назначение                                         | Официальная документация                                                 |
| ------------------- | -------------------------------------------------- | ------------------------------------------------------------------------ |
| **Python**          | Основной язык разработки                           | [Python Documentation](https://docs.python.org/3/)                       |
| **Django**          | Backend-фреймворк и серверный рендеринг            | [Django Documentation](https://docs.djangoproject.com/)                  |
| **PostgreSQL**      | Реляционная база данных                            | [PostgreSQL Documentation](https://www.postgresql.org/docs/)             |
| **MinIO**           | S3-совместимое файловое хранилище                  | [MinIO Documentation](https://docs.min.io/)                              |
| **Docker**          | Контейнеризация                                    | [Docker Documentation](https://docs.docker.com/)                         |
| **Docker Compose**  | Локальный запуск мультисервисного окружения        | [Docker Compose Documentation](https://docs.docker.com/compose/)         |
| **Ruff**            | Линтер и форматтер Python-кода                     | [Ruff Documentation](https://docs.astral.sh/ruff/)                       |
| **pre-commit**      | Git hooks и автоматические проверки перед коммитом | [pre-commit Documentation](https://pre-commit.com/)                      |
| **python-dotenv**   | Загрузка настроек из `.env`                        | [python-dotenv](https://pypi.org/project/python-dotenv/)                 |
| **django-storages** | Интеграция Django с S3-совместимым storage         | [django-storages Documentation](https://django-storages.readthedocs.io/) |

---

## Инструкция по установке и запуску

### Системные требования

Для запуска проекта должны быть установлены:

| Компонент      | Рекомендуемая версия |
| -------------- | -------------------- |
| Python         | 3.11+                |
| pip            | актуальная версия    |
| Git            | актуальная версия    |
| Docker         | актуальная версия    |
| Docker Compose | актуальная версия    |

---

## Установка проекта локально без Docker

### 1. Клонирование репозитория

```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd TECHO_lab/bmstu
```

### 2. Создание виртуального окружения

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Создание файла `.env`

Создай файл `.env` в корне проекта и заполни его значениями из раздела **Переменные окружения**.

### 5. Применение миграций

```bash
python manage.py migrate
```

### 6. Запуск локального сервера

```bash
python manage.py runserver
```

После запуска приложение будет доступно по адресу:

```text
http://127.0.0.1:8000/
```

---

## Установка и запуск через Docker

### 1. Проверка наличия `.env`

Перед запуском через Docker убедись, что в корне проекта уже создан файл `.env`.

### 2. Сборка и запуск контейнеров

```bash
docker compose -f Docker/docker-compose.yaml up --build
```

### 3. Остановка контейнеров

```bash
docker compose -f Docker/docker-compose.yaml down
```

### 4. Остановка контейнеров с удалением volume

```bash
docker compose -f Docker/docker-compose.yaml down -v
```

### Сервисы, доступные после запуска

| Сервис        | Адрес                   |
| ------------- | ----------------------- |
| Django        | `http://127.0.0.1:8000` |
| PostgreSQL    | `127.0.0.1:54322`       |
| Adminer       | `http://127.0.0.1:8081` |
| MinIO API     | `http://127.0.0.1:9000` |
| MinIO Console | `http://127.0.0.1:9001` |

### Действие после первого запуска MinIO

После первого запуска проекта через Docker необходимо:

1. открыть `http://127.0.0.1:9001`;
2. войти под учётными данными из `.env`;
3. создать bucket, имя которого указано в переменной `MINIO_BUCKET`.

---

## Работа с линтером и форматтером

В проекте используется **Ruff** как единый инструмент для линтинга и форматирования Python-кода.

### Проверка кода линтером

```bash
ruff check .
```

### Автоматическое исправление части замечаний

```bash
ruff check . --fix
```

### Проверка форматирования

```bash
ruff format . --check
```

### Автоматическое форматирование

```bash
ruff format .
```

### Рекомендуемая последовательность перед коммитом

```bash
ruff check . --fix
ruff format .
```

---

## Работа с pre-commit

`pre-commit` используется для автоматического запуска проверок перед каждым коммитом.

### Установка хуков

```bash
pre-commit install
```

### Полная ручная проверка всех файлов

```bash
pre-commit run --all-files
```

### Удаление установленных хуков

```bash
pre-commit uninstall
```

### Проверки, выполняемые pre-commit

| Хук                       | Назначение                                    |
| ------------------------- | --------------------------------------------- |
| `check-added-large-files` | Запрет коммита слишком больших файлов         |
| `check-merge-conflict`    | Поиск маркеров неразрешённых merge-конфликтов |
| `check-yaml`              | Проверка корректности YAML-файлов             |
| `check-json`              | Проверка корректности JSON-файлов             |
| `check-toml`              | Проверка корректности TOML-файлов             |
| `trailing-whitespace`     | Удаление пробелов в конце строк               |
| `end-of-file-fixer`       | Исправление конца файла                       |
| `debug-statements`        | Поиск debug-конструкций                       |
| `ruff`                    | Линтинг проекта                               |
| `ruff-format`             | Проверка/форматирование кода                  |
| `check-filenames`         | Проверка стандарта именования файлов          |

### Что блокирует коммит

Коммит не должен выполняться, если:

* в репозитории есть слишком большие файлы;
* в коде обнаружены следы merge-конфликтов;
* код не проходит линтер;
* код не проходит форматирование;
* обнаружены неиспользуемые импорты, переменные или мёртвый код;
* имя файла не соответствует принятому стандарту.

---

## Описание переменных окружения

Проект использует `.env` для хранения конфигурации.

### Таблица переменных окружения

| Переменная               | Пример значения                     | Назначение                    |
| ------------------------ | ----------------------------------- | ----------------------------- |
| `DJANGO_SECRET_KEY`      | `django-insecure-change-me`         | Секретный ключ Django         |
| `DJANGO_DEBUG`           | `True`                              | Режим отладки                 |
| `DJANGO_ALLOWED_HOSTS`   | `127.0.0.1,localhost`               | Разрешённые хосты приложения  |
| `POSTGRES_DB`            | `db`                                | Имя базы данных PostgreSQL    |
| `POSTGRES_USER`          | `admin`                             | Пользователь PostgreSQL       |
| `POSTGRES_PASSWORD`      | `root`                              | Пароль PostgreSQL             |
| `POSTGRES_HOST`          | `127.0.0.1`                         | Адрес PostgreSQL              |
| `POSTGRES_PORT`          | `54322`                             | Порт PostgreSQL               |
| `MINIO_ROOT_USER`        | `minioadmin`                        | Пользователь MinIO            |
| `MINIO_ROOT_PASSWORD`    | `minioadmin123`                     | Пароль MinIO                  |
| `MINIO_BUCKET`           | `jobability`                        | Bucket для хранения медиа     |
| `MINIO_ENDPOINT`         | `http://127.0.0.1:9000`             | Endpoint MinIO API            |
| `MINIO_PUBLIC_MEDIA_URL` | `http://127.0.0.1:9000/jobability/` | Базовый адрес для медиафайлов |

### Пример файла `.env`

```env
DJANGO_SECRET_KEY=django-insecure-change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

POSTGRES_DB=db
POSTGRES_USER=admin
POSTGRES_PASSWORD=root
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=54322

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=jobability
MINIO_ENDPOINT=http://127.0.0.1:9000
MINIO_PUBLIC_MEDIA_URL=http://127.0.0.1:9000/jobability/
```

---

## Принятые соглашения по code style

В проекте используется единый стандарт именования.

### Правила именования

| Тип сущности                  | Стандарт           |
| ----------------------------- | ------------------ |
| Python-файлы                  | `PascalCase.py`    |
| Python-классы                 | `PascalCase`       |
| Python-функции и переменные   | `camelCase`        |
| Константы                     | `UPPER_SNAKE_CASE` |
| HTML / CSS / JS / изображения | `kebab-case`       |

### Примеры корректных имён

| Тип         | Пример                 |
| ----------- | ---------------------- |
| Python-файл | `Views.py`             |
| Python-файл | `Settings.py`          |
| Класс       | `ApplicantProfile`     |
| Функция     | `homeRedirect`         |
| Переменная  | `draftCount`           |
| HTML-файл   | `vacancies-list.html`  |
| CSS-файл    | `application-card.css` |

### Технические исключения

Следующие имена сохраняются без изменения по техническим причинам:

* `manage.py`
* `__init__.py`
* файлы миграций Django
* `.gitignore`
* `.pre-commit-config.yaml`
* `.env`
* `requirements.txt`
* `pyproject.toml`
* `Dockerfile`
* `docker-compose.yaml`


```
