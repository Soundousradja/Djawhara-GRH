from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),

    path('nouveau/', views.employee_create, name='employee_create'),

    path(
        'dossiers-incomplets/',
        views.incomplete_files,
        name='incomplete_files'
    ),

    path('<int:pk>/', views.employee_detail, name='employee_detail'),

    path(
        '<int:pk>/modifier/',
        views.employee_update,
        name='employee_update'
    ),

    path(
        '<int:pk>/supprimer/',
        views.employee_delete,
        name='employee_delete'
    ),

    path(
        '<int:pk>/document/',
        views.employee_add_document,
        name='employee_add_document'
    ),

    path('ateliers/', views.workshop_list, name='workshop_list'),
]