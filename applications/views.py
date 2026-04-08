from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, JsonResponse
from django.core.files.uploadedfile import UploadedFile
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import get_user_model
from .models import SocialApplication, Operator, Citizen
from .forms import SocialApplicationForm
from loguru import logger
import requests
import traceback
import os
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone
import json

User = get_user_model()


def upload_to_fastapi(file, doc_type: str):
    """Отправка файла в FastAPI сервис"""
    try:
        if not file:
            return None

        file.seek(0)

        url = f"http://127.0.0.1:8001/upload/{doc_type}"
        files = {"file": (file.name, file.read(), file.content_type or 'application/octet-stream')}

        response = requests.post(url, files=files, timeout=30)

        if response.status_code == 200:
            logger.info(f"Файл {file.name} успешно загружен в FastAPI")
            return response.json()
        else:
            logger.error(f"FastAPI ошибка: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        logger.warning(f"FastAPI сервис не доступен, файл {file.name} не загружен")
        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки в FastAPI: {e}")
        return None


def index(request):
    """Главная страница с формой подачи заявки"""
    if request.method == 'POST':
        form = SocialApplicationForm(request.POST, request.FILES)

        logger.info(f"Получены файлы: {list(request.FILES.keys())}")

        if form.is_valid():
            try:
                application = form.save()
                logger.info(f"Заявка #{application.id} успешно сохранена в БД")

                if request.FILES.get('passport_scan'):
                    upload_to_fastapi(request.FILES['passport_scan'], 'passport')

                if request.FILES.get('snils_scan'):
                    upload_to_fastapi(request.FILES['snils_scan'], 'snils')

                if request.FILES.get('additional_docs'):
                    upload_to_fastapi(request.FILES['additional_docs'], 'additional')

                messages.success(
                    request,
                    f'✅ Заявка №{application.id} успешно принята! Сохраните этот номер для отслеживания.'
                )
                return redirect('index')

            except Exception as e:
                logger.error(f"Ошибка при сохранении заявки: {e}")
                logger.error(traceback.format_exc())
                messages.error(request, f'❌ Ошибка при создании заявки: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    logger.error(f"Ошибка в поле {field}: {error}")
                    messages.error(request, f'Ошибка в поле "{field}": {error}')
    else:
        form = SocialApplicationForm()

    return render(request, 'applications/index.html', {'form': form})


def application_status(request, app_id):
    """Просмотр статуса заявки по ID"""
    application = get_object_or_404(SocialApplication, id=app_id)
    return render(request, 'applications/status.html', {'app': application})


def search_application(request):
    """Поиск заявки по номеру или СНИЛС"""
    query = request.GET.get('query')
    app_id = request.GET.get('app_id')

    if app_id:
        try:
            app = SocialApplication.objects.get(id=app_id)
            return redirect('application_status', app_id=app_id)
        except SocialApplication.DoesNotExist:
            messages.error(request, 'Заявка с таким номером не найдена')
            return render(request, 'applications/search.html')

    if query:
        applications = SocialApplication.objects.filter(snils=query).order_by('-created_at')
        if applications.exists():
            return render(request, 'applications/search_results.html', {'applications': applications})
        else:
            messages.error(request, 'Заявки с таким СНИЛС не найдены')

    return render(request, 'applications/search.html')


def operator_login(request):
    """Вход оператора"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            logger.info(f"Оператор {username} вошел в систему")
            messages.success(request, f'Добро пожаловать, {username}!')
            return redirect('application_list')
        else:
            messages.error(request, 'Неверные учетные данные')

    return render(request, 'applications/login.html')


def operator_logout(request):
    """Выход оператора"""
    logger.info(f"Оператор {request.user.username} вышел из системы")
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('operator_login')


@login_required
def application_list(request):
    """Список всех заявок с пагинацией"""
    applications = SocialApplication.objects.all().order_by('-created_at')

    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'applications/list.html', {'page_obj': page_obj})


@login_required
def application_detail(request, app_id):
    """Детальный просмотр заявки для оператора"""
    application = get_object_or_404(SocialApplication, id=app_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        comment = request.POST.get('comment')

        if new_status:
            application.status = new_status
            application.employee_comment = comment
            application.save()

            messages.success(request, f'Статус заявки #{app_id} обновлен!')
            logger.info(f"Оператор {request.user.username} изменил статус заявки #{app_id} на {new_status}")

            return redirect('application_detail', app_id=app_id)

    return render(request, 'applications/detail.html', {'app': application})


@login_required
def download_pdf(request, app_id):
    """Скачать PDF-уведомление"""
    from .utils import generate_application_pdf

    application = get_object_or_404(SocialApplication, id=app_id)

    try:
        pdf_path = generate_application_pdf(application)

        if os.path.exists(pdf_path):
            logger.info(f"PDF для заявки #{app_id} сгенерирован пользователем {request.user.username}")
            return FileResponse(
                open(pdf_path, 'rb'),
                as_attachment=True,
                filename=f'zayavka_{app_id}.pdf'
            )
        else:
            messages.error(request, 'Ошибка генерации PDF')
    except Exception as e:
        logger.error(f"Ошибка генерации PDF: {e}")
        messages.error(request, 'Ошибка при создании PDF')

    return redirect('application_detail', app_id=app_id)


def create_admin(request):
    """Временный эндпоинт для создания администратора"""
    if not User.objects.filter(username='Zubkova').exists():
        User.objects.create_superuser(
            username='Zubkova',
            email='zubkova.v1k@yandex.ru',
            password='1234'
        )
        return JsonResponse({'status': 'Admin created!', 'username': 'Zubkova', 'password': '1234'})
    return JsonResponse({'status': 'Admin already exists'})


def privacy_policy(request):
    """Страница с политикой обработки персональных данных"""
    return render(request, 'applications/privacy_policy.html')


def citizen_login(request):
    """Вход гражданина в личный кабинет"""
    if request.method == 'POST':
        snils = request.POST.get('snils')
        password = request.POST.get('password')

        try:
            citizen = Citizen.objects.get(snils=snils)
            if check_password(password, citizen.password):
                request.session['citizen_id'] = citizen.id
                request.session['citizen_name'] = f"{citizen.last_name} {citizen.first_name}"
                messages.success(request, f'Добро пожаловать, {citizen.first_name}!')
                return redirect('citizen_cabinet')
            else:
                messages.error(request, 'Неверный пароль')
        except Citizen.DoesNotExist:
            messages.error(request, 'Пользователь с таким СНИЛС не найден')

    return render(request, 'applications/citizen_login.html')


def citizen_register(request):
    """Регистрация гражданина"""
    if request.method == 'POST':
        snils = request.POST.get('snils')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        patronymic = request.POST.get('patronymic', '')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'applications/citizen_register.html')

        if Citizen.objects.filter(snils=snils).exists():
            messages.error(request, 'Пользователь с таким СНИЛС уже зарегистрирован')
            return render(request, 'applications/citizen_register.html')

        if Citizen.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже зарегистрирован')
            return render(request, 'applications/citizen_register.html')

        citizen = Citizen.objects.create(
            snils=snils,
            last_name=last_name,
            first_name=first_name,
            patronymic=patronymic,
            email=email,
            phone=phone,
            password=make_password(password)
        )

        request.session['citizen_id'] = citizen.id
        request.session['citizen_name'] = f"{citizen.last_name} {citizen.first_name}"

        messages.success(request, f'Регистрация прошла успешно! Добро пожаловать, {citizen.first_name}!')
        return redirect('citizen_cabinet')

    return render(request, 'applications/citizen_register.html')


def citizen_cabinet(request):
    """Личный кабинет гражданина"""
    if 'citizen_id' not in request.session:
        messages.error(request, 'Пожалуйста, войдите в личный кабинет')
        return redirect('citizen_login')

    citizen = Citizen.objects.get(id=request.session['citizen_id'])
    applications = SocialApplication.objects.filter(snils=citizen.snils).order_by('-created_at')

    context = {
        'citizen': citizen,
        'applications': applications,
    }
    return render(request, 'applications/citizen_cabinet.html', context)


def citizen_logout(request):
    """Выход из личного кабинета"""
    request.session.flush()
    messages.success(request, 'Вы вышли из личного кабинета')
    return redirect('index')


def analytics_dashboard(request):
    """Отдельная страница аналитики"""

    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, 'Доступ запрещен. Только для сотрудников.')
        return redirect('operator_login')

    # Общая статистика
    total_applications = SocialApplication.objects.count()
    new_applications = SocialApplication.objects.filter(status='new').count()
    processing_applications = SocialApplication.objects.filter(status='processing').count()
    completed_applications = SocialApplication.objects.filter(status='completed').count()
    rejected_applications = SocialApplication.objects.filter(status='rejected').count()

    # Процент выполнения
    completion_rate = 0
    if total_applications > 0:
        completion_rate = round((completed_applications / total_applications) * 100, 1)

    # Статистика по статусам для круговой диаграммы
    status_stats = SocialApplication.objects.values('status').annotate(
        count=Count('status')
    )

    status_labels = {
        'new': 'Новые',
        'processing': 'В обработке',
        'completed': 'Выполненные',
        'rejected': 'Отказанные'
    }

    status_data = {
        'labels': [status_labels.get(item['status'], item['status']) for item in status_stats],
        'counts': [item['count'] for item in status_stats],
    }

    # Динамика за последние 30 дней
    last_30_days = timezone.now() - timedelta(days=30)
    monthly_stats = SocialApplication.objects.filter(
        created_at__gte=last_30_days
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    daily_data = {
        'labels': [item['date'].strftime('%d.%m') for item in monthly_stats] if monthly_stats else [],
        'counts': [item['count'] for item in monthly_stats] if monthly_stats else []
    }

    # Статистика по месяцам
    monthly_data = SocialApplication.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    monthly_chart = {
        'labels': [item['month'].strftime('%B %Y') for item in monthly_data] if monthly_data else [],
        'counts': [item['count'] for item in monthly_data] if monthly_data else []
    }

    # Популярные услуги
    popular_services = SocialApplication.objects.values('service_type').annotate(
        count=Count('service_type')
    ).order_by('-count')[:5]

    services_data = {
        'labels': [item['service_type'][:25] for item in popular_services],
        'counts': [item['count'] for item in popular_services]
    }

    # Последние заявки
    recent_applications = SocialApplication.objects.all().order_by('-created_at')[:10]

    context = {
        'total_applications': total_applications,
        'new_applications': new_applications,
        'processing_applications': processing_applications,
        'completed_applications': completed_applications,
        'rejected_applications': rejected_applications,
        'completion_rate': completion_rate,
        'status_data': json.dumps(status_data),
        'daily_data': json.dumps(daily_data),
        'monthly_chart': json.dumps(monthly_chart),
        'services_data': json.dumps(services_data),
        'recent_applications': recent_applications,
    }

    return render(request, 'applications/analytics.html', context)