from django.db import models

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=150, null=True, blank=True) # Имя пользователя
    created_at = models.DateTimeField(auto_now_add=True) # Дата регистрации
    tasks_completed = models.IntegerField(default=0) # Общее число задач
    daily_tasks_completed = models.PositiveIntegerField(default=0)  # Число задач за сутки
    is_subscribed = models.BooleanField(default=False) # Оформлена ли подписка
    is_admin = models.BooleanField(default=False) # Является ли админом
    subscription_end = models.DateTimeField(blank=True, null=True)  # Дата окончания подписки

    def __str__(self):
        return self.username or f"User {self.telegram_id}"

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    actions_count = models.IntegerField(default=0)