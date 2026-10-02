from django.urls import path
from . import views

urlpatterns = [
    path('', views.contract_list, name='contract_list'),
    path('nouveau/', views.contract_create, name='contract_create'),
    path('<int:pk>/modifier/', views.contract_update, name='contract_update'),
    path('<int:pk>/supprimer/', views.contract_delete, name='contract_delete'),
    
]
