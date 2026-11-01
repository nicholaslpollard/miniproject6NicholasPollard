# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

app_name = 'planner'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('features/', views.features, name='features'),
    path('help/', views.help_page, name='help'),

    # Authentication (Django's built-in login/logout views; logout requires POST)
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(
        authentication_form=LoginForm, redirect_authenticated_user=True,
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Private pages
    path('dashboard/', views.dashboard, name='dashboard'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/new/', views.course_create, name='course_create'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),

    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/new/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_update, name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('assignments/<int:pk>/toggle/', views.assignment_toggle, name='assignment_toggle'),
]
