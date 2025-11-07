from django.urls import path

from .views import UserProfileView, UserRegistrationView, UserVerifyView, UserLevelView, UserDataCSVView


urlpatterns = [
    path('level/', UserLevelView.as_view(), name='user-level'),
    path('data-csv/', UserDataCSVView.as_view(), name='user-data-csv'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('verify/', UserVerifyView.as_view(), name='user-verify'),
]
