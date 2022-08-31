# praktikum_new_diplom 
### README заполнен для сдачи первой части

Описание проекта:
```
Проект представляет из себя продуктовый помощник, в котором можно размещать рецепты, добавлять рецепты в избранное и в список покупок, формировать pdf-файл списка покупок. Также сервис позволяет подписываться на авторов.
```

Развёрнутый проект и REDOC по API:
```
Адрес приложения: http://127.0.0.1:8000/api/
REDOC:
В папке infra выполните команду docker-compose up при запущенном Docker Desktop.
Увидеть спецификацию API вы сможете по адресу:
http://localhost/api/docs/
```

### Как запустить проект:
Клонировать репозиторий:
```
git clone https://github.com/IvanGolenko/foodgram-project-react.git
```

Создать и активировать виртуальное окружение:
```
py -m venv env
```
```
source venv/Scripts/activate
```

Установить зависимости:
```
pip install -r requirements.txt
```

В 'backend' выполнить миграции, создать суперпользователя и собрать статику
```
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver
```

### Пример запроса через API.
Для доступа к API необходимо

1. регистрация пользователяыцф:
Нужно выполнить POST-запрос http://127.0.0.1:8000/api/users/ передав поля:
```
{
    "email": "vpupkin@yandex.ru",
    "username": "vasya.pupkin",
    "first_name": "Вася",
    "last_name": "Пупкин",
    "password": "Qwerty123"
}
```
API вернет Status 201 о том, что пользователь зарегистрирован.

2. получить токен:
Нужно выполнить POST-запрос http://127.0.0.1:8000/api/auth/token/login/ передав поля:
```
{
    "password": "string",
    "email": "string"
}
```
API вернет JWT-токен.

**Важно!** При отправке запроса передайте токен в заголовке Authorization: Token <токен>

Технологии, которые использовались:
- Python ![Python](https://img.shields.io/badge/-Python-black?style=flat-square&logo=Python)
- Django ![Django](https://img.shields.io/badge/-Django-0aad48?style=flat-square&logo=Django)
- Django REST Framework ![Django Rest Framework](https://img.shields.io/badge/DRF-red?style=flat-square&logo=Django)
- PostgresSQL ![Postgresql](https://img.shields.io/badge/-Postgresql-%232c3e50?style=flat-square&logo=Postgresql)
- Nginx ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=flat-square&logo=nginx&logoColor=white)

Автор:
```
Иван Голенко
```