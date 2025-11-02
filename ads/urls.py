from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our admin viewset with it.
router = DefaultRouter()
router.register(r'manage', views.AdAdminViewSet, basename='ad-manage')

# The API URLs are determined automatically by the router.
# The public-facing view is defined manually.
urlpatterns = [
    # Public API endpoint, e.g., /api/ads/
    path('', views.PublishedAdListView.as_view(), name='ad-public-list'),

    # Admin API endpoints, e.g., /api/ads/manage/
    path('', include(router.urls)),
]
