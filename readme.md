# Базовые инструкции по деплою (без специфики разных серверов).

## Зависимости

- Django 5.2.6
- openpyxl 3.1.5
- pdfplumber 0.11.7
- requests 2.32.5
- psycopg2/psycopg2-binary

## Настройка settings.py

В файл `safety_calc/settings.py` внести следующие изменения:

```python
DEBUG = False  # Отключить отладочный режим для продакшена

ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'IP_сервера']  # Разрешённые хосты

SECRET_KEY = 'your_secret_key' # В идеале через переменные окружения через os.environ.get

# Статические файлы 
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  

# Заменить на актуальные данные для подключения к базе (в идеале тоже через переменные окружения)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'promaeks_calc',
        'USER': 'postgres',         
        'PASSWORD': 'passfordb',   
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Подготовка проекта
В директории проекта выполните следующие команды:

### 1. Создать и применить миграции
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```
### 2. Создать superuser
```bash
python3 manage.py createsuperuser
```
### 3. Заполнить таблицы начальными данными
```bash
python3 manage.py shell
```
```py
from calculations.helpers.tables import populate_database
populate_database()
exit()
```
### 4. Собрать статические файлы
```bash
python3 manage.py collectstatic
```
### 5. Проверка готовности
```bash
python3 manage.py check --deploy
```
## Запуск на продакшен-сервере

Документация по запуску на различных серверах (в т.ч. Apache, gunicorn): 
https://docs.djangoproject.com/en/5.2/howto/deployment/