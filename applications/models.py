from django.db import models
from django.contrib.auth.models import AbstractUser


class Operator(AbstractUser):
    """Модель оператора и пользователя"""
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    position = models.CharField(max_length=100, blank=True, verbose_name="Должность")

    # Дополнительные поля для пользователей
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")  # Исправлено
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    address = models.TextField(blank=True, verbose_name="Адрес")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.last_name} {self.first_name})"


def get_upload_path(instance, filename):
    """Генерация пути для загрузки файлов"""
    return f'documents/{instance.__class__.__name__}/{instance.id}/{filename}'


class SocialApplication(models.Model):
    """Заявка в СФР"""
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('processing', 'На рассмотрении'),
        ('completed', 'Выполнена'),
        ('rejected', 'Отказано'),
    ]

    # Личные данные
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    snils = models.CharField(max_length=14, verbose_name="СНИЛС", unique=True)  # Добавлено unique=True

    # Данные заявки
    service_type = models.CharField(max_length=200, verbose_name="Тип услуги")
    description = models.TextField(verbose_name="Описание")

    # Сканы документов
    passport_scan = models.FileField(
        upload_to='documents/passports/',
        null=True,
        blank=True,
        verbose_name="Скан паспорта"
    )
    snils_scan = models.FileField(
        upload_to='documents/snils/',
        null=True,
        blank=True,
        verbose_name="Скан СНИЛС"
    )
    additional_docs = models.FileField(
        upload_to='documents/additional/',
        null=True,
        blank=True,
        verbose_name="Дополнительные документы"
    )

    # Статус
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Ответственный оператор
    assigned_operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True, blank=True)
    employee_comment = models.TextField(blank=True, verbose_name="Комментарий сотрудника")

    def __str__(self):
        return f"Заявка №{self.id} - {self.last_name} {self.first_name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Заявка в СФР"
        verbose_name_plural = "Заявки в СФР"


class ApplicationHistory(models.Model):
    """История изменений заявки"""
    application = models.ForeignKey(SocialApplication, on_delete=models.CASCADE)
    operator = models.ForeignKey(Operator, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at} - {self.operator} - {self.action}"

class Citizen(models.Model):
    """Модель гражданина для личного кабинета"""
    snils = models.CharField(max_length=14, unique=True, verbose_name="СНИЛС")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    password = models.CharField(max_length=255, verbose_name="Пароль")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    last_login = models.DateTimeField(blank=True, null=True, verbose_name="Последний вход")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.snils})"

    class Meta:
        verbose_name = "Гражданин"
        verbose_name_plural = "Граждане"