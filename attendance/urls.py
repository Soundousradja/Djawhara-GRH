from django.urls import path
from . import views

urlpatterns = [
    path('', views.daily_entry, name='attendance_daily'),
    path('imprimer/', views.daily_attendance_print, name='daily_attendance_print'),
    path('enregistrer/', views.save_attendance, name='save_attendance'),
    path('biometrique/', views.biometric_terminal, name='biometric_terminal'),
    path('biometrique/pointer/', views.biometric_punch, name='biometric_punch'),
    path('api/biometrique/', views.biometric_api, name='biometric_api'),
    path('historique/', views.attendance_history, name='attendance_history'),
    path('discipline/', views.discipline_dashboard, name='discipline_dashboard'),
]
