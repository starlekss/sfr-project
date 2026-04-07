from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import SocialApplication, ApplicationHistory
from loguru import logger
import sys

# Настройка логирования
logger.add(
    "logs/actions.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)

@receiver(pre_save, sender=SocialApplication)
def log_application_change(sender, instance, **kwargs):
    """Логирование изменений заявки"""
    if instance.pk:
        old_instance = SocialApplication.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            # Сохраняем в базу
            ApplicationHistory.objects.create(
                application=instance,
                operator=instance.assigned_operator,
                action='STATUS_CHANGED',
                old_status=old_instance.status,
                new_status=instance.status,
                comment=instance.employee_comment
            )
            # Логируем в файл
            logger.info(f"Заявка #{instance.id} | Оператор: {instance.assigned_operator} | "
                       f"Статус изменен: {old_instance.status} -> {instance.status}")

@receiver(post_save, sender=SocialApplication)
def log_application_created(sender, instance, created, **kwargs):
    """Логирование создания заявки"""
    if created:
        logger.info(f"СОЗДАНА НОВАЯ ЗАЯВКА #{instance.id} | {instance.last_name} {instance.first_name} | "
                   f"СНИЛС: {instance.snils}")