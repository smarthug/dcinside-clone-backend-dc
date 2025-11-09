from django.urls import path

from .views import FileView

urlpatterns = [
    path('', FileView.as_view(), name='file-create'),
    # path('list/', FileView.as_view(), name='file-list'),
    path('<int:pk>/', FileView.as_view(), name='file-detail'),
]
