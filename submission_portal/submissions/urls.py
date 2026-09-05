from django.urls import path
from . import views

urlpatterns = [
    path('', views.submit_paper, name='submit_paper'),
    path('setup/', views.setup_admin, name='setup_admin'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.submission_list, name='submission_list'),
    path('dashboard/detail/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('dashboard/detail/<int:pk>/pdf/', views.download_pdf, name='download_pdf'),
    path('dashboard/admins/create/', views.create_admin, name='create_admin'),
    path('submitted/<int:pk>/', views.submit_success, name='submit_success'),
    path('status/', views.check_status, name='check_status'),
]
