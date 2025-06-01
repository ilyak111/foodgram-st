# Foodgram Project Setup Guide

## Installation Steps

1. Перейдите в папку infra
   ```bash
   cd infra
   ```

2. Скопируйте шаблон .env файла и заполните его в соответствии с вашими данными
   ```bash
   cp env_copy.txt .env
   ```

3. Запустите docker контейнеры
   ```bash
   docker-compose up -d --build
   ```

4. Создайте и примените миграции
   ```bash
   docker exec -it foodgram-backend python manage.py makemigrations
   docker exec -it foodgram-backend python manage.py migrate
   ```

5. Скопируйте таблицу ингридиентов в базу данных
   ```bash
   docker exec -it foodgram-backend python manage.py load_ingredients_database data/ingredients.json
   ```

6. Подгрузите статику
   ```bash
   docker exec -it foodgram-backend python manage.py collectstatic
   docker exec -it foodgram-backend cp -r /app/collected_static/. /backend_static_files/static/
   ```

7. Создайте суперпользователя
   ```bash
   docker exec -it foodgram-backend python manage.py createsuperuser
   ```

8. Зайдите на сайт по адресу [localhost:8080/](http://localhost:8080/)

9. После завершения работы с сайтом закройте docker контейнеры
   ```bash
   docker-compose down -v
   ```