from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('users.urls')),  # Подключаем маршруты приложения `users`
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),  # Все API будет доступно через /api/
]