from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from .serializers import UserSerializer
from django.http import HttpResponse

class UserListCreateAPIView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserRegistrationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        telegram_id = request.data.get("telegram_id")
        username = request.data.get("username")

        if not telegram_id or not username:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, существует ли пользователь
        if User.objects.filter(telegram_id=telegram_id).exists():
            return Response({"error": "User already registered"}, status=status.HTTP_400_BAD_REQUEST)

        # Сохранение нового пользователя
        user = User.objects.create(telegram_id=telegram_id, username=username)

        User.objects.create(user=user)

        return Response(
            {"message": "User registered successfully", "user": {"id": user.id, "username": user.username}},
            status=status.HTTP_201_CREATED
        )

class UserDetailAPIView(APIView):
    def get(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
            return Response({
                "telegram_id": user.telegram_id,
                "username": user.username,
                "tasks_completed": user.tasks_completed,
                "is_admin": user.is_admin,
                "is_subscribed": user.is_subscribed,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class UpdateUserTasksAPIView(APIView):
    def post(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Обновление количества выполненных заданий
        tasks_completed = request.data.get("tasks_completed")
        if tasks_completed is not None:
            user.tasks_completed = tasks_completed
            user.save()
            return Response({"message": "Tasks completed updated successfully"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

class MakeAdminAPIView(APIView):
    def post(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
            user.is_admin = True
            user.save()
            return Response({"message": "User promoted to admin successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class AdminManagementAPIView(APIView):
    def post(self, request, telegram_id):
        try:
            user = User.objects.get(telegram_id=telegram_id)
            user.is_admin = True
            user.save()
            return Response({"message": "User promoted to admin successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        admins = User.objects.filter(is_admin=True)
        data = [{"telegram_id": admin.telegram_id, "username": admin.username} for admin in admins]
        return Response(data, status=status.HTTP_200_OK)

class DailyStatisticsAPIView(APIView):
    def get(self, request, telegram_id):
        try:
            # Получение пользователя по telegram_id
            user = User.objects.get(telegram_id=telegram_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Проверка, является ли пользователь администратором
        if not user.is_admin:
            return Response({"error": "You do not have permission to view this."}, status=status.HTTP_403_FORBIDDEN)

        users = User.objects.all()
        stats = {}

        for user in users:
            stats[user.telegram_id] = {
                'username': user.username,
                'count_daily_tasks': user.daily_tasks_completed,
                'count_tasks': user.tasks_completed,
                }
        # Возвращение статистики в ответе
        return Response(stats, status=status.HTTP_200_OK)

class UpdateTasksView(APIView):
    def patch(self, request, telegram_id):
        user = User.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        tasks_completed = request.data.get("tasks_completed")
        daily_tasks_completed = request.data.get("daily_tasks_completed")

        if tasks_completed is not None:
            user.tasks_completed += tasks_completed

        if daily_tasks_completed is not None:
            user.daily_tasks_completed += daily_tasks_completed

        user.save()
        return Response({"message": "Tasks updated successfully"}, status=status.HTTP_200_OK)

def home(request):
    return HttpResponse("Welcome to the homepage!")
