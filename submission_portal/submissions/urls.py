from django.urls import path
from . import views


def page(route, view, name=None):
    routes = [path(route, view, name=name)]
    if route.endswith('/') and route != '/':
        routes.append(path(route.rstrip('/'), view))
    return routes


urlpatterns = [
    path('', views.submit_paper, name='submit_paper'),
    *page('csrf/', views.csrf_token_json, 'csrf_token'),
    *page('setup/', views.setup_admin, 'setup_admin'),
    *page('login/', views.admin_login, 'admin_login'),
    *page('logout/', views.admin_logout, 'admin_logout'),
    *page('dashboard/', views.submission_list, 'submission_list'),
    *page('dashboard/detail/<int:pk>/', views.submission_detail, 'submission_detail'),
    *page('dashboard/detail/<int:pk>/pdf/', views.download_pdf, 'download_pdf'),
    *page('dashboard/admins/create/', views.create_admin, 'create_admin'),
    *page('submitted/', views.submit_success, 'submit_success'),
    *page('status/', views.check_status, 'check_status'),
]
