
from django.db.models import F, Sum
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, SAFE_METHODS

from core.paginations import PostPagination
from shared.permissions import IsLevel1UserOrReadOnly
from .models import Gallery, Post, Comment, PostVote, CommentVote
from .serializers import GallerySerializer, PostListSerializer, PostSerializer, CommentSerializer
from .permissions import IsAuthorOrReadOnly
from django.utils import timezone
from datetime import timedelta


class GalleryViewSet(viewsets.ModelViewSet):
    queryset = Gallery.objects.all().order_by('id')
    serializer_class = GallerySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsLevel1UserOrReadOnly]
    # filter_backends = [filters.SearchFilter]
    filterset_fields = ['slug', 'title']
    ordering_fields = ['created_at', 'title']
    search_fields = ['slug']


    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.filter(permission_read__gte=self.request.user.level)
        else:
            qs = qs.filter(permission_read_gte=99)
        return qs

    def list(self, request, *args, **kwargs):
        slug = request.query_params.get('slug')
        if slug:
            cache_key = f'gallery_view:{slug}'
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if slug and response.status_code == 200:
            cache.set(cache_key, response.data, 60 * 60 * 24)  # 1 day

        return response

    def _invalidate_cache(self, instance):
        cache_key = f'gallery_view:{instance.slug}'
        cache.delete(cache_key)

    def perform_create(self, serializer):
        instance = serializer.save()
        self._invalidate_cache(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_cache(instance)

    def perform_destroy(self, instance):
        self._invalidate_cache(instance)
        instance.delete()



class PostViewSet(viewsets.ModelViewSet):
    pagination_class = PostPagination
    queryset = Post.objects.select_related(
        'gallery', 'author').all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    search_fields = ['title', 'content', 'nickname']
    ordering = ['-is_notice', '-created_at', '-updated_at']
    ordering_fields = ['is_notice', 'created_at', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_authenticated:
            qs = qs.filter(gallery__permission_read__gte=self.request.user.level)
        else:
            qs = qs.filter(gallery__permission_read__gte=100)

        gallery_slug = self.request.query_params.get('gallery')
        if gallery_slug:
            qs = qs.filter(gallery__slug=gallery_slug)
        if not self.request.method in SAFE_METHODS:
            qs = qs.select_related('gallery')
        
        # Filter out soft-deleted posts
        qs = qs.filter(is_delete=False)
        return qs

    def list(self, request, *args, **kwargs):
        gallery_slug = request.query_params.get('gallery')
        page = request.query_params.get('page', '1')

        # Cache only the first page of a specific gallery
        if gallery_slug and page == '1':
            cache_key = f'posts:{gallery_slug}:page:1'
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

            response = super().list(request, *args, **kwargs)

            if response.status_code == 200:
                cache.set(cache_key, response.data, 60 * 60 * 24)  # 1 day
            return response

        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.gallery:
            cache_key = f'posts:{instance.gallery.slug}:page:1'
            cache.delete(cache_key)

    def perform_destroy(self, instance):
        if instance.gallery:
            cache_key = f'posts:{instance.gallery.slug}:page:1'
            cache.delete(cache_key)
        instance.is_delete = True
        instance.save(update_fields=['is_delete'])

    def get_object(self):
        return super().get_object()

    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        post = self.get_object()
        Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
        post.refresh_from_db()
        return Response({'views': post.views})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        post = self.get_object()
        try:
            value = int(request.data.get('value', 0))
        except (TypeError, ValueError):
            return Response({'detail': 'value must be 1 or -1'}, status=status.HTTP_400_BAD_REQUEST)
        if value not in (1, -1):
            return Response({'detail': 'value must be 1 or -1'}, status=status.HTTP_400_BAD_REQUEST)
        PostVote.objects.update_or_create(
            post=post, user=request.user, defaults={'value': value})
        total = PostVote.objects.filter(post=post).aggregate(
            total=Sum('value'))['total'] or 0
        post.recommend = total
        post.save(update_fields=['recommend'])
        return Response({'recommend': post.recommend})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related(
        'post','post__gallery', 'author', 'parent').all().order_by('created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    search_fields = ['content', 'nickname']
    ordering_fields = ['created_at', 'updated_at', 'recommend']

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.user.is_authenticated:
            qs = qs.filter(post__gallery__permission_read__gte=self.request.user.level)
        else:
            qs = qs.filter(post__gallery__permission_read_gte=100)

        post_id = self.request.query_params.get('post')
        if post_id:
            qs = qs.filter(post_id=post_id)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        comment = self.get_object()
        try:
            value = int(request.data.get('value', 0))
        except (TypeError, ValueError):
            return Response({'detail': 'value must be 1 or -1'}, status=status.HTTP_400_BAD_REQUEST)
        if value not in (1, -1):
            return Response({'detail': 'value must be 1 or -1'}, status=status.HTTP_400_BAD_REQUEST)
        CommentVote.objects.update_or_create(
            comment=comment, user=request.user, defaults={'value': value})
        total = CommentVote.objects.filter(comment=comment).aggregate(
            total=Sum('value'))['total'] or 0
        comment.recommend = total
        comment.save(update_fields=['recommend'])
        return Response({'recommend': comment.recommend})


# @api_view(['GET'])
# def hot_feed(request):
#     recent_since = timezone.now() - timedelta(hours=48)
#     posts = (Post.objects
#              .filter(created_at__gte=recent_since)
#              .annotate(score=F('recommend'))
#              .order_by('-score', '-created_at')[:100])
#     serializer = PostSerializer(posts, many=True, context={'request': request})
#     return Response(serializer.data)
