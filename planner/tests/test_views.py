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


class PublicPageTests(TestCase):
    def test_public_pages_render_with_expected_templates(self):
        pages = {
            'planner:about': ('planner/about.html', 'About Study Planner'),
            'planner:features': ('planner/features.html', 'Personal dashboard'),
            'planner:help': ('planner/help.html', 'What happens when I delete a course?'),
        }
        for name, (template, text) in pages.items():
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, template)
                self.assertTemplateUsed(response, 'base.html')
                self.assertContains(response, text)

    def test_home_page_has_registration_call_to_action_for_visitors(self):
        response = self.client.get(reverse('planner:home'))
        self.assertContains(response, 'Create a free account')
