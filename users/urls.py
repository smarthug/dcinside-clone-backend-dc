from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (UserProfileView, UserRegistrationView, UserVerifyView, UserLevelView, UserDataCSVView, UsersView, 
                    UserPasswordResetRequestView, UserPasswordResetConfirmView, UserFindIDView, DisputeSubmissionView, AdvertisementSubmissionView,
                    UserEducationViewSet, UserCareerViewSet, UserCertificateViewSet, UserExternalActivityViewSet, UserPublicationViewSet, UserAwardViewSet)

router = DefaultRouter()
router.register(r'educations', UserEducationViewSet, basename='user-educations')
router.register(r'careers', UserCareerViewSet, basename='user-careers')
router.register(r'certificates', UserCertificateViewSet, basename='user-certificates')
router.register(r'activities', UserExternalActivityViewSet, basename='user-activities')
router.register(r'publications', UserPublicationViewSet, basename='user-publications')
router.register(r'awards', UserAwardViewSet, basename='user-awards')
router.register(r'', UsersView, basename='users')

urlpatterns = [
    path('level/', UserLevelView.as_view(), name='user-level'),
    path('csv/', UserDataCSVView.as_view(), name='user-data-csv'),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('verify/', UserVerifyView.as_view(), name='user-verify'),
    path('password-reset-request/', UserPasswordResetRequestView.as_view(), name='user-password-reset-request'),
    path('password-reset-confirm/', UserPasswordResetConfirmView.as_view(), name='user-password-reset-confirm'),
    path('find-id/', UserFindIDView.as_view(), name='user-find-id'),
    path('dispute/', DisputeSubmissionView.as_view(), name='user-dispute-submission'),
    path('advertisement/', AdvertisementSubmissionView.as_view(), name='user-advertisement-submission'),
    path('', include(router.urls)),
]
