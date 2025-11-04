from django.urls import path

from .views import UserProfileView, UserRegistrationView, UserVerifyView


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('verify/', UserVerifyView.as_view(), name='user-verify'),
]
