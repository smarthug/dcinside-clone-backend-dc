from rest_framework import serializers
from .models import Ad


class PublicAdSerializer(serializers.ModelSerializer):
    """
    Serializer for public consumption.
    Only shows fields safe for public display.
    """
    class Meta:
        model = Ad
        fields = ('id', 'title', 'image_large',
                  'image_small', 'link_url', 'location')
        read_only_fields = fields


class AdAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for admin/management use.
    Shows all fields needed for CRUD operations.
    """
    class Meta:
        model = Ad
        fields = (
            'id',
            'title',
            'image_large',
            'image_small',
            'link_url',
            'location',
            'start_date',
            'end_date',
            'is_active',
            'order'
        )
