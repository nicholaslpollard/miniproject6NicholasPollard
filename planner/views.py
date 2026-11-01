# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.shortcuts import render


def home(request):
    """Display the public home page."""
    return render(request, 'planner/home.html')
