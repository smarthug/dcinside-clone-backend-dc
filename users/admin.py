
from django.contrib import admin
from .models import User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'display_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'display_name')
