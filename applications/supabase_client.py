from decouple import config
from supabase import create_client, Client

# Инициализация Supabase клиента
SUPABASE_URL = config('SUPABASE_URL')
SUPABASE_ANON_KEY = config('SUPABASE_ANON_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase_client():
    """Возвращает клиент Supabase для работы с API"""
    return supabase

def test_connection():
    """Тестирование подключения к Supabase"""
    try:
        # Простой запрос для проверки
        response = supabase.table('_django_migrations').select('*').limit(1).execute()
        print("Подключение к Supabase успешно!")
        return True
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return False