from pathlib import PurePath

from rest_framework import serializers

from core.models import Gallery
from files.models import File

BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.sh', '.ps1', '.msi', '.dll', '.com',
    '.scr', '.pif', '.vbs', '.js', '.wsh', '.wsf', '.jar',
    '.php', '.py', '.rb', '.pl',
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class FileSerializer(serializers.ModelSerializer):
    gallery = serializers.SlugRelatedField(
        slug_field='slug', queryset=Gallery.objects.all())

    class Meta:
        model = File
        fields = ['id', 'gallery', 'author', 'file', 'filename', 'created_at', 'is_deleted']
        read_only_fields = ['id', 'author', 'created_at', 'filename']

    def validate_file(self, value):
        ext = PurePath(value.name).suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            raise serializers.ValidationError(
                f"파일 확장자 '{ext}'는 업로드할 수 없습니다.")
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f"파일 크기가 {MAX_FILE_SIZE // (1024 * 1024)}MB를 초과합니다.")
        return value

    def create(self, validated_data):
        request = self.context['request']
        if request.user and request.user.is_authenticated:
            validated_data['author'] = request.user

        validated_data['filename'] = validated_data['file'].name
        return super().create(validated_data)
