from django.urls import path
from .views import (
    DebtListView,
    DebtDetailView,
    CategoryListView,
    CategoryDetailView, MeApi
)

app_name = "authorizer"

urlpatterns = [
    path('me/', MeApi.as_view(), name='me'),
    path('debts/', DebtListView.as_view(), name='debt-list'),
    path('debts/<int:pk>/', DebtDetailView.as_view(), name='debt-detail'),

    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]
