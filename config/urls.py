# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

"""Root URL configuration for the Study Planner project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('planner.urls')),
]
