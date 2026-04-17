from rest_framework import generics, viewsets, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.core.cache import cache
from shared.permissions import IsLevel1User
from .models import Ad
from .serializers import PublicAdSerializer, AdAdminSerializer



class PublishedAdListView(generics.ListAPIView):
    """
    PUBLIC-FACING VIEW:
    Lists all *published* ads.

    Uses the custom `Ad.published` manager to automatically filter for
    ads that are active and within their start/end date range.

    Allows filtering by location, e.g., /api/ads/public/?location=hero
    """
    serializer_class = PublicAdSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Filter by location, defaulting to 'hero' if not specified.
        Ad.published manager already filters is_active, start_date, end_date.
        """
        location = self.request.query_params.get('location', 'hero')
        return Ad.published.filter(location=location).order_by('order', 'start_date')

    def list(self, request, *args, **kwargs):
        location = request.query_params.get('location')
        if location:
            cache_key = f'ads:{location}'
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if location and response.status_code == 200:
            cache.set(cache_key, response.data, 60 * 60 * 24)  # 1 day

        return response

class AdAdminViewSet(viewsets.ModelViewSet):
    """
    ADMIN-FACING VIEWSET:
    Provides full CRUD (Create, Retrieve, Update, Delete) for Ads.

    This view should be protected and only accessible by admins.
    It uses the default `Ad.objects` manager to show *all* ads,
    including inactive or scheduled ones.
    """
    serializer_class = AdAdminSerializer
    permission_classes = [permissions.IsAuthenticated,
                          IsLevel1User]  # Or your custom permission
    filterset_fields = ['location']

    # Admin sees all objects, not just published ones
    queryset = Ad.objects.all().order_by('location', 'order')

    def _invalidate_cache(self, instance):
        cache_key = f'ads:{instance.location}'
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
