# README Ledger-Logic

## Basic Django Project Setup Guide

### Basic Commands

- Setup virtual environment:
  ```
  python -m venv /path/to/new/virtual/environment
  ```

- Activate virtual environment:
  ```
  my_project\venv\Scripts\activate
  ```

- Deactivate virtual environment:
  ```
  deactivate
  ```

- Install Django:
  ```
  pip install django
  ```

- Setup first project (after activating virtual environment and `cd` into project directory):
  ```
  django-admin startproject myproject
  ```

- Install requirements:
  ```
  pip install -r requirements.txt
  ```

- View project:
  ```
  python manage.py runserver
  ```

- Migrate:
  ```
  python manage.py migrate
  ```

- Create an app:
  ```
  python manage.py startapp appname
  ```

- Create admin account:
  ```
  python manage.py createsuperuser
  ```

- Admin account: admin
- Email account: taylor.austin004@gmail.com
- Password: whatisapassword

### Basic Django Knowledge

- As soon as you create a new "app", you need to add the app to your `mysite/settings.py` `INSTALLED_APPS` list.
- Next, you want to make sure you create a `urls.py` file in your new app.
- Continue to add new URLs only to the authentic `urls.py` file, not the `mysite` `urls.py` file.
