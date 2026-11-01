# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

"""Shared helpers for view tests. All data lives only in the temporary test database."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from planner.models import Assignment, Course

User = get_user_model()


def days_from_today(days):
    return timezone.localdate() + timedelta(days=days)


class TwoUserTestCase(TestCase):
    """
    Creates two users (alice and bob), each with one course and one assignment.
    Users have no password; tests log in with force_login().
    """

    def setUp(self):
        self.alice = User.objects.create_user(username='alice')
        self.bob = User.objects.create_user(username='bob')

        self.alice_course = Course.objects.create(
            owner=self.alice, code='INF601', name='Advanced Python', description='Alice private notes',
        )
        self.bob_course = Course.objects.create(
            owner=self.bob, code='BIO200', name='Bob Secret Biology', description='Bob private notes',
        )
        self.alice_assignment = Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Alice Project', due_date=days_from_today(7),
        )
        self.bob_assignment = Assignment.objects.create(
            owner=self.bob, course=self.bob_course, title='Bob Secret Lab', due_date=days_from_today(7),
        )
