from django.db import models
from django.conf import settings

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    memo = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Permission: users with level <= level_required can view.
    level_required = models.PositiveSmallIntegerField(
        default=50, 
        help_text="User level must be less than or equal to this value to view."
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_tasks'
    )
    assigned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='assigned_tasks', 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
