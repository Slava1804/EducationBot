# Generated by Django 5.1.4 on 2024-12-09 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_tasks_completed_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]