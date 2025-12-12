from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Task
from .serializers import TaskSerializer, TaskCalendarSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.select_related('author', 'author__meta_info').all()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = {
        'start_date': ['gte', 'lte', 'exact'],
        'end_date': ['gte', 'lte', 'exact'],
        'created_at': ['gte', 'lte']
    }

    @action(detail=False, methods=['get'])
    def month_events(self, request):
        """
        Return all events for a specific range without pagination.
        Used for Calendar view.
        """
        queryset = self.filter_queryset(Task.objects.all())
        # Optimize query: select only required fields, avoid joins if possible
        queryset = queryset.only('id', 'title', 'start_date', 'end_date')
        
        serializer = TaskCalendarSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        
        # Enforce view permission level <= 50 for the feature itself
        if user.level > 50:
             return Task.objects.none()

        # View permission logic:
        # 1. User level is <= level_required
        # 2. OR User is in assigned_users
        # 3. OR User is the author
        return self.queryset.filter(
            Q(level_required__gte=user.level) | 
            Q(assigned_users=user) |
            Q(author=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
