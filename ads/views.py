from rest_framework import generics, viewsets, permissions
from django.utils import timezone
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
        """
        # Get location from query param, default to 'hero'
        location = self.request.query_params.get('location', 'hero')
        date_now = timezone.now()
        # Use the 'published' manager and filter by location
        # The default ordering from the model's Meta class will be applied.
        return Ad.published.filter(location=location, start_date__lte=date_now, end_date__gte=date_now)


class AdAdminViewSet(viewsets.ModelViewSet):
    """
    ADMIN-FACING VIEWSET:
    Provides full CRUD (Create, Retrieve, Update, Delete) for Ads.

    This view should be protected and only accessible by admins.
    It uses the default `Ad.objects` manager to show *all* ads,
    including inactive or scheduled ones.
    """
    serializer_class = AdAdminSerializer
    permission_classes = [permissions.IsAdminUser]  # Or your custom permission

    # Admin sees all objects, not just published ones
    queryset = Ad.objects.all().order_by('location', 'order')
