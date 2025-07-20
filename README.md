# Django Webhook Project

## Overview

This is a simple Django project designed to receive webhook payloads, log them into a MySQL database, and expose a webhook endpoint locally using ngrok.

## Prerequisites

- Python 3.10+
- pip
- Virtualenv (recommended)
- Docker (for MySQL setup)
- Ngrok (for exposing localhost to the internet)

## Installation & Setup

### 1. Clone or Download the Project

Extract the project folder to your local machine.

Folder structure:

```
Django-webhook/
├── webhook_project/
│   ├── webhook_project/
│   └── webhook/
└── myenv/ (optional if you use your own virtualenv)
```

### 2. Create Virtual Environment

If `myenv/` is not present:

```bash
cd Django-webhook
python3 -m venv myenv
source myenv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available:

```bash
pip install django mysqlclient
```

### 4. MySQL Setup Using Docker

Run MySQL using Docker:

```bash
docker run --name mysql-db \
-e MYSQL_ROOT_PASSWORD=rootpass \
-e MYSQL_DATABASE=webhook_db \
-e MYSQL_USER=django_user \
-e MYSQL_PASSWORD=django_pass \
-p 3307:3306 -d mysql:8.0
```

### 5. Configure Django Database Settings

In `webhook_project/webhook_project/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'webhook_db',
        'USER': 'django_user',
        'PASSWORD': 'django_pass',
        'HOST': '127.0.0.1',
        'PORT': '3307',
    }
}
```

### 6. Run Migrations

```bash
cd webhook_project
python manage.py makemigrations webhook
python manage.py migrate
```

### 7. Start Django Server

```bash
python manage.py runserver
```

## Ngrok Setup

To expose your webhook endpoint:

```bash
ngrok http 8000
```

Use the generated URL for webhook testing:

```
POST https://<your-ngrok-id>.ngrok-free.app/webhook/
```

## Accessing the MySQL Database

### Using Docker CLI:

```bash
docker exec -it mysql-db mysql -u django_user -p
```

Enter `django_pass` when prompted.

### Using MySQL Workbench:

- Host: 127.0.0.1
- Port: 3307
- User: django_user
- Password: django_pass
- Database: webhook_db

## Developer Workflow Summary

1. Extract or clone project
2. Set up Python virtual environment
3. Install required packages
4. Run MySQL using Docker
5. Update `settings.py` for DB connection
6. Run migrations
7. Start Django server
8. Use Ngrok for webhook testing
9. Check MySQL data via CLI or MySQL Workbench

## Note

This project is intended for local development and webhook testing purposes.
