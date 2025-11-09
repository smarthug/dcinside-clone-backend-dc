from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserProfileView, UserRegistrationView, UserVerifyView, UserLevelView, UserDataCSVView, UsersView

router = DefaultRouter()
router.register(r'', UsersView, basename='users')

urlpatterns = [
    path('level/', UserLevelView.as_view(), name='user-level'),
    path('data-csv/', UserDataCSVView.as_view(), name='user-data-csv'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('verify/', UserVerifyView.as_view(), name='user-verify'),
    path('', include(router.urls)),
]
