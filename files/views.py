from django.http import FileResponse
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from files.permissions import IsAuthorOrReadOnly
from .models import File
from .serializers import FileSerializer


class FileView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    queryset = File.objects.select_related(
        'gallery', 'author').all().order_by('id')
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    parser_classes = [MultiPartParser]
    serializer_class = FileSerializer
    filterset_fields = ['gallery__slug']
    ordering_fields = ['created_at']
    search_fields = ['filename']

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_authenticated:
            qs = qs.filter(gallery__permission_read__gte=self.request.user.level)
        else:
            qs = qs.filter(gallery__permission_read__gte=100)

        gallery_slug = self.request.query_params.get(
            'gallery', self.request.data.get('gallery'))
        if gallery_slug:
            qs = qs.filter(
                gallery__slug=gallery_slug)
        return qs

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return FileResponse(instance.file.open('rb'), as_attachment=True, filename=instance.filename)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Return a response with the file URL
        pk = str(serializer.data.get('id'))
        return Response({'url': f'/api/files/{pk}/', 'filename': serializer.data.get('filename')}, status=status.HTTP_201_CREATED, headers=headers)
