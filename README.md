# BMS (Business Management System)

## Описание функционала
Проект на **Django** для управления пользователями, командами, задачами, встречами и календарём.
Основной функционал:
- Управление пользователями с различными ролями (Team Admin, Team Manager, User)
- Создание, редактирование и удаление задач (`tasks`)
- Управление командами (`teams`): создание, присоединение по invite_code
- Комментирование задач
- Система прав и ролей для доступа к задачам и командам
- Поддержка статусов задач: Open, In Progress, Done

---

## Установка и запуск

## **1. Клонируем проект:**

```bash
git clone https://github.com/yourusername/bms.git
cd bms
```
## **2. Создание виртуального окружения и установка зависимостей**
```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```
## **3. Настройка переменных окружения**
Скопируйте файл .env.example в .env и укажите свои параметры:
```bash
cp .env.example .env
```
## **4. Применение миграций и запуск сервера**
```bash
python manage.py migrate
python manage.py runserver
```

**После этого проект будет доступен по адресу:**
👉 http://127.0.0.1:8000

---

## 📖 Примеры использования

**Запуск тестов**
```bash
pytest
```

**Создание суперпользователя**
```bash
python manage.py createsuperuser
```

**Создание задачи через форму** /tasks/create/

**Присоединение к команде по invite_code** /teams/join/

**Просмотр списка задач** /tasks/

**Комментирование задачи на странице** /tasks/<id>/

---

## 📂 Структура проекта
**bms/**  
├── accounts/       # управление пользователями  
├── calendarapp/    # календарь и события  
├── core/           # базовые настройки проекта  
├── evaluations/    # модуль оценок  
├── meetings/       # встречи и расписание  
├── tasks/          # задачи и управление ими  
├── teams/          # команды и участники  
├── templates/      # HTML-шаблоны  
├── manage.py  
├── requirements.txt  
└── db.sqlite3  

---

## 🛠️ Используемые технологии

**Python 3.12+**

**Django 5.2**

**Pytest**

**SQLite (по умолчанию)**
