from rest_framework import serializers
from .models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskUserSerializer(serializers.ModelSerializer):
    korean_name = serializers.CharField(source='meta_info.korean_name', read_only=True)

    class Meta:
        model = User
        fields = ['username', 'display_name', 'korean_name']

class TaskSerializer(serializers.ModelSerializer):
    author_details = TaskUserSerializer(source='author', read_only=True)
    assigned_users_details = TaskUserSerializer(source='assigned_users', many=True, read_only=True)
    assigned_users = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'memo',
            'start_date', 'end_date', 'level_required', 
            'author', 'author_details',
            'assigned_users', 'assigned_users_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def create(self, validated_data):
        assigned_users = validated_data.pop('assigned_users', [])
        task = Task.objects.create(**validated_data)
        task.assigned_users.set(assigned_users)
        return task

class TaskCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'start_date', 'end_date']
