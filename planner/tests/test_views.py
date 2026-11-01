# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_responds_successfully(self):
        response = self.client.get(reverse('planner:home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_base_template(self):
        response = self.client.get(reverse('planner:home'))
        self.assertTemplateUsed(response, 'planner/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'Study Planner')
