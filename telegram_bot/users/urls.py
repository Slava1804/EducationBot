from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'),  # Стартовая страница
    path('api/users/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('api/users/register/', UserRegistrationAPIView.as_view(), name='user-register'),
    path('api/users/<int:telegram_id>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('api/users/<int:telegram_id>/update_tasks/', UpdateTasksView.as_view(), name='update_tasks'),  # С использованием PATCH
    path('api/users/<int:telegram_id>/daily_statistics/', DailyStatisticsAPIView.as_view(), name='daily_statistics'),
    path('api/users/<int:telegram_id>/make_admin/', MakeAdminAPIView.as_view(), name='make_admin'),
]