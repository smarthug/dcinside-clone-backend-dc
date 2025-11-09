from django.http import FileResponse
from rest_framework import generics, mixins, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from files.permissions import IsAuthorOrReadOnly
from .models import File
from .serializers import FileSerializer


class FileView(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    queryset = File.objects.all().order_by('id')
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    parser_classes = [MultiPartParser]
    serializer_class = FileSerializer
    filterset_fields = ['gallery__slug']
    ordering_fields = ['created_at']
    search_fields = ['filename']

    def get_queryset(self):
        qs = super().get_queryset()
        gallery_slug = self.request.data.get('gallery')
        if gallery_slug:
            qs = qs.select_related('gallery').filter(
                gallery__slug=gallery_slug)
        if not self.request.method in SAFE_METHODS:
            qs = qs.select_related('gallery')
        return qs

    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return FileResponse(instance.file.open('rb'))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Return a response with the file URL
        return Response({'url': serializer.data.get('file'), 'filename': serializer.data.get('filename')}, status=status.HTTP_201_CREATED, headers=headers)

    # @action(detail=True, methods=['post'])
    # def list(self, request, *args, **kwargs):
    #     return super().list(request, *args, **kwargs)
