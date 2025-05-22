1) Перейдите в папку infra
    cd infra
2) Запустите docker контейнеры
    docker-compose up -d --build
3) Создайте новую сессию терминала (если команда должна быть запущена из неё, то будет указано (*)) и зайдите в PostgreSQL и создайте базу данных
    (*) docker exec -it foodgram-database psql -U postgres
    (*) create database fg;
4) Создайте миграции и примените
    docker exec -it foodgram-backend python manage.py makemigrations
    docker exec -it foodgram-backend python manage.py migrate
5) Скопируйте таблицу ингридиентов в базу данных
    docker cp "/home/user/Documents/foodgram-st/data/ingredients.csv" foodgram-database:tmp/
    (*) \c fg;
    (*) copy ingredients_myingredient(name, measurement_unit) from '/tmp/ingredients.csv' WITH (FORMAT csv, DELIMITER ',');
6) Подгрузите статику
    docker exec -it foodgram-backend python manage.py collectstatic
    docker exec -it foodgram-backend cp -r /app/collected_static/. /backend_static_files/static/
7) Создайте суперпользователя
    docker exec -it foodgram-backend python manage.py createsuperuser
8) Зайдите на сайт по адресу localhost:8080/
9) После завершения работы с сайтом закройте docker контейнеры
    docker-compose down -v