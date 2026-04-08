from .models import Citizen


def global_user_context(request):
    """Глобальный контекст для всех шаблонов"""
    context = {}

    # Для сотрудников (Django auth)
    if request.user.is_authenticated:
        context['is_operator'] = True
        context['operator_name'] = request.user.get_full_name() or request.user.username
    else:
        context['is_operator'] = False

    # Для граждан (сессия)
    citizen_id = request.session.get('citizen_id')
    if citizen_id:
        try:
            citizen = Citizen.objects.get(id=citizen_id)
            context['is_citizen'] = True
            context['citizen_name'] = f"{citizen.first_name} {citizen.last_name}"
            context['citizen'] = citizen
        except Citizen.DoesNotExist:
            request.session.flush()
            context['is_citizen'] = False
    else:
        context['is_citizen'] = False

    return context