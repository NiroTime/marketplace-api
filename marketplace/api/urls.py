from django.urls import path

from .views import (DeleteItemAPIView, GetItemAPIView, ItemStatisticAPIView,
                    PutItemAPIView, SalesItemAPIView)

urlpatterns = [
    path('nodes/<str:pk>', GetItemAPIView.as_view()),
    path('imports', PutItemAPIView.as_view()),
    path('delete/<str:pk>', DeleteItemAPIView.as_view()),
    path('sales', SalesItemAPIView.as_view()),
    path('nodes/<str:pk>/statistic', ItemStatisticAPIView.as_view())
]
