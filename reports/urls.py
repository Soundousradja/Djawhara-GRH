from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('journalier/', views.daily_report, name='daily_report'),
    path('hebdomadaire/', views.weekly_report, name='weekly_report'),
    path('mensuel/', views.monthly_report, name='monthly_report'),
    path('employe/<int:pk>/', views.employee_report, name='employee_report'),
]
