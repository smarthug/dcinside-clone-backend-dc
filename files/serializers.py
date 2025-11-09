from rest_framework import serializers

from core.models import Gallery
from files.models import File


class FileSerializer(serializers.ModelSerializer):
    gallery = serializers.SlugRelatedField(
        slug_field='slug', queryset=Gallery.objects.all())

    class Meta:
        model = File
        fields = '__all__'
        read_only_fields = ['id', 'author', 'created_at', 'filename']

    def create(self, validated_data):

        request = self.context['request']
        if request.user and request.user.is_authenticated:
            validated_data['author'] = request.user

        validated_data['filename'] = validated_data['file'].name
        return super().create(validated_data)
