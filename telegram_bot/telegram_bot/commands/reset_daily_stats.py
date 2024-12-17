from django.core.management.base import BaseCommand
from django.utils.timezone import now
from telegram_bot.users.models import User

class Command(BaseCommand):
    help = "Сброс ежедневной статистики задач"

    def handle(self, *args, **kwargs):
        today = now().date()
        users = User.objects.filter(last_reset__lt=today)
        users.update(daily_tasks_completed=0, last_reset=today)
        self.stdout.write(f"Сброшена ежедневная статистика для {users.count()} пользователей.")