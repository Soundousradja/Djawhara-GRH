from django.urls import path
from . import views

urlpatterns = [
    path('', views.payroll_list, name='payroll_list'),
    path('nouveau/', views.payroll_create, name='payroll_create'),
    path('<int:pk>/', views.payroll_detail, name='payroll_detail'),
    path('<int:pk>/imprimer/', views.payroll_print, name='payroll_print'),
    path('<int:pk>/modifier/', views.payroll_update, name='payroll_update'),
    path('<int:pk>/supprimer/', views.payroll_delete, name='payroll_delete'),
]
