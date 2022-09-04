![example workflow](https://github.com/IvanGolenko/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

# Продуктовый помощник foodgram
Развёрнутый проект и REDOC по API:
```
Адрес проекта: http://51.250.102.175/
Адрес API: http://51.250.102.175/api/
un: ivan@ya.ru / pw: qwerty123@@  -(superuser)
```

# Описание проекта:
Проект представляет из себя продуктовый помощник, в котором можно размещать рецепты, добавлять рецепты в избранное и в список покупок, формировать txt-файл списка покупок. Также сервис позволяет подписываться на авторов.

### Как запустить проект:
1. Выполните вход на свой удаленный сервер:
```
ssh <USERNAME>@<IP_ADDRESS>
```
2. Установите docker на сервер:
```
sudo apt install docker.io
```
3. Установите docker-compose на сервер:
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
4. Перенести подготовленные файлы docker-compose.yml и default.conf на сервер:
```bash
scp docker-compose.yml username@server_ip:/home/<username>/
```
```bash
scp default.conf <username>@<server_ip>:/home/<username>/
```
5. Создайте папку infra:
```bash
mkdir infra
```
6. Создайте файл .env в дериктории infra:
```bash
touch .env
```
- Заполните файл .env, указав переменные окружения:
```
SECRET_KEY=<SECRET_KEY>
DEBUG=<True/False>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```
7. Добавьте Secrets:
Для работы с Workflow добавьте в Secrets GitHub переменные окружения для работы:
```
DB_ENGINE
DB_HOST
DB_NAME
DB_PORT
POSTGRES_USER
POSTGRES_PASSWORD

DOCKER_PASSWORD=<Docker password>
DOCKER_USERNAME=<Docker username>

USER=<username для подключения к серверу>
HOST=<IP сервера>
PASSPHRASE=<пароль для сервера, если он установлен>
SSH_KEY=<ваш SSH ключ(cat ~/.ssh/id_rsa)>

TG_CHAT_ID=<ID чата, в который поступит сообщение>
TELEGRAM_TOKEN=<токен вашего бота>
```

### После успешного деплоя на сервер
Зайдите на боевой сервер и выполните команды:
В папке infra выполните команду, что бы собрать контейнер:
```bash
sudo docker-compose up -d
```
Для доступа к контейнеру выполните следующие команды:
```bash
sudo docker-compose exec backend python manage.py makemigrations
```
```bash
sudo docker-compose exec backend python manage.py migrate
```
```bash
sudo docker-compose exec backend python manage.py collectstatic --no-input
```
```bash
sudo docker-compose exec backend python manage.py createsuperuser
```
Дополнительно можно наполнить базу данных ингредиентами:
```
sudo docker-compose exec -T backend python manage.py loaddata data/ingredients_1.json
```
- Создайте теги: завтрак, обед, ужин

### Технологии, которые использовались:
- Python ![Python](https://img.shields.io/badge/-Python-black?style=flat-square&logo=Python)
- Django ![Django](https://img.shields.io/badge/-Django-0aad48?style=flat-square&logo=Django)
- Django REST Framework ![Django Rest Framework](https://img.shields.io/badge/DRF-red?style=flat-square&logo=Django)
- PostgresSQL ![Postgresql](https://img.shields.io/badge/-Postgresql-%232c3e50?style=flat-square&logo=Postgresql)
- Nginx ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=flat-square&logo=nginx&logoColor=white)

Автор:
```
Иван Голенко
```