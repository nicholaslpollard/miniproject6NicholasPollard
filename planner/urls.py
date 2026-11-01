# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.urls import path

from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.home, name='home'),
]
