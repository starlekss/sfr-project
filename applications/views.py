from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse
from django.core.files.uploadedfile import UploadedFile
from .models import SocialApplication, Operator
from .forms import SocialApplicationForm
from loguru import logger
from django.http import JsonResponse
import requests
import traceback


def upload_to_fastapi(file, doc_type: str):
    """Отправка файла в FastAPI сервис"""
    try:
        if not file:
            return None

        # Сбрасываем указатель файла в начало
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

        # Логируем полученные файлы
        logger.info(f"Получены файлы: {list(request.FILES.keys())}")

        if form.is_valid():
            try:
                # Сохраняем заявку
                application = form.save()
                logger.info(f"Заявка #{application.id} успешно сохранена в БД")

                # Загрузка файлов в FastAPI (опционально, не блокирует создание заявки)
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
            # Выводим ошибки формы
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

    # Поиск по номеру заявки
    if app_id:
        try:
            app = SocialApplication.objects.get(id=app_id)
            return redirect('application_status', app_id=app_id)
        except SocialApplication.DoesNotExist:
            messages.error(request, 'Заявка с таким номером не найдена')
            return render(request, 'applications/search.html')

    # Поиск по СНИЛС
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

from django.contrib.auth import get_user_model
User = get_user_model()

def create_admin(request):
    """Временный эндпоинт для создания администратора"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='Zubkova',
            email='zubkova.v1k@yandex.ru',
            password='1234'
        )
        return JsonResponse({'status': 'Admin created! Login: admin, Password: admin123'})
    return JsonResponse({'status': 'Admin already exists'})