web: python manage.py migrate --noinput && python manage.py seed_data && gunicorn vegfruit_store.wsgi:application --bind 0.0.0.0:$PORT
