from django.urls import path

from .views import (DeleteItemAPIView, GetItemAPIView, ItemStatisticAPIView,
                    PostItemAPIView, SalesItemAPIView)

urlpatterns = [
    path('nodes/<str:pk>', GetItemAPIView.as_view()),
    path('imports', PostItemAPIView.as_view()),
    path('delete/<str:pk>', DeleteItemAPIView.as_view()),
    path('sales', SalesItemAPIView.as_view()),
    path('node/<str:pk>/statistic', ItemStatisticAPIView.as_view())
]
