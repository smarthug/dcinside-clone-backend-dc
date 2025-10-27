from django.contrib import admin
from .models import Ad


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    """
    Customizes the Django admin interface for Ads.
    """
    list_display = (
        'title',
        'location',
        'order',
        'is_active',
        'start_date',
        'end_date'
    )
    list_filter = ('location', 'is_active', 'start_date')
    search_fields = ('title', 'link_url')

    # Allows for easy re-ordering and activation directly in the list view
    list_editable = ('order', 'is_active')

    fieldsets = (
        (None, {
            'fields': ('title', 'location', 'link_url')
        }),
        ('Ad Content', {
            'fields': ('image_large',
                       'image_small',)
        }),
        ('Publishing & Ordering', {
            'fields': ('is_active', 'start_date', 'end_date', 'order')
        }),
    )
