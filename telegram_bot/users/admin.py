from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "is_admin", "is_subscribed", "tasks_completed", "daily_tasks_completed")
    list_filter = ("is_admin", "is_subscribed")
    search_fields = ("telegram_id", "username")
