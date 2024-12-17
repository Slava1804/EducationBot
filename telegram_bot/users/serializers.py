from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'telegram_id', 'username', 'created_at', 'tasks_completed', 'is_admin', 'is_subscribed', 'daily_tasks_completed', 'subscription_end']
        extra_kwargs = {
            'is_subscribed': {'required': False},
            'subscription_end': {'required': False, 'format': '%Y-%m-%dT%H:%M:%S'},
        }
    def validate_telegram_id(self, value):
        if User.objects.filter(telegram_id=value).exists():
            raise serializers.ValidationError('This telegram_id is already registered.')
        return value
