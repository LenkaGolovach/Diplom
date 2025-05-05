# Diplom

Этот проект представляет собой веб-приложение для управления задачами с использованием досок Канбан. Проект использует Django для бэкенда и Vue.js для фронтенда.

## Предварительный этап

1. Установите [PostgreSQL](https://www.postgresql.org/download/), если он ещё не установлен.
2. Установите [ollama](https://ollama.com/download).
3. Установите [RabbitMQ](https://www.rabbitmq.com/docs/download).
4. Установите необходимую модель нейросети и запустите ollama
```bash
ollama pull llava:7b
ollama serve
```

## Запуск бэкенда (Django)

### Настройка базы данных

Создайте базу данных:
```bash
sudo -u postgres psql
CREATE DATABASE mydatabase;
CREATE USER postgres WITH PASSWORD 'pass_for_post';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO postgres;
```

### Перейдите в директорию бэкенда:

```bash
cd backend
```

### Создайте виртуальное окружение и активируйте его:

```bash
python -m venv .venv
source .venv/bin/activate  # Для Windows: .venv\Scripts\activate
```

### Установите зависимости:

Убедитесь, что у вас установлен Python и pip. Установите необходимые зависимости, выполнив:

```bash
pip install -r requirements.txt
```

### Примените миграции:

Создайте базу данных и примените миграции:

```bash
python manage.py makemigrations api
python manage.py migrate
```

### Запустите сервер разработки:

Запустите сервер Django:

```bash
python run_socketio.py
```

### Запустите celery:

В отдельном терминале перейдите в директорию бэкенда, активируйте виртуальное окружение, а затем запустите celery:

```bash
celery -A core.celery worker -l info -P eventlet
```

Сервер будет доступен по адресу http://localhost:8000.

## Запуск фронтенда (Vue.js)

### Перейдите в директорию фронтенда:

```bash
cd frontend
```

### Установите зависимости:

Убедитесь, что у вас установлен Node.js и npm. Установите необходимые зависимости, выполнив:

```bash
npm install
```

### Запустите сервер разработки:

Запустите сервер Vue.js:

```bash
npm run serve
```

Приложение будет доступно по адресу http://localhost:8080.