import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sfr_site.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = 'Zubkova'
email = 'zubkova.v1k@yandex.ru'
password = '1234'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"Администратор {username} создан!")
else:
    print(f"Администратор {username} уже существует")