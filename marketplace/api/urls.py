from django.urls import path

from .views import DeleteItemAPIView, PutItemAPIView, GetItemAPIView

urlpatterns = [
    path('nodes/<str:pk>', GetItemAPIView.as_view()),
    path('imports', PutItemAPIView.as_view()),
    path('delete/<str:pk>', DeleteItemAPIView.as_view()),
]
