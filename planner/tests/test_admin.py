# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from planner.models import Assignment, Course

User = get_user_model()


class AdminTestBase(TestCase):
    """Users are created without passwords and logged in with force_login()."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(username='admin', email='admin@example.com', password=None)
        self.alice = User.objects.create_user(username='alice')
        self.bob = User.objects.create_user(username='bob')
        self.alice_course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        self.bob_course = Course.objects.create(owner=self.bob, code='CS101', name='Intro to CS')
        self.assignment = Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Mini Project 6', due_date=date(2026, 12, 1),
        )
        self.admin_urls = [
            reverse('admin:planner_course_changelist'),
            reverse('admin:planner_course_add'),
            reverse('admin:planner_course_change', args=[self.alice_course.pk]),
            reverse('admin:planner_assignment_changelist'),
            reverse('admin:planner_assignment_add'),
            reverse('admin:planner_assignment_change', args=[self.assignment.pk]),
        ]


class AdminAccessTests(AdminTestBase):
    def test_models_registered(self):
        self.assertTrue(admin.site.is_registered(Course))
        self.assertTrue(admin.site.is_registered(Assignment))

    def test_superuser_can_access_admin_pages(self):
        self.client.force_login(self.superuser)
        for url in self.admin_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_user_redirected_to_admin_login(self):
        for url in self.admin_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith(reverse('admin:login')))

    def test_ordinary_user_cannot_access_admin(self):
        self.client.force_login(self.alice)
        for url in self.admin_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith(reverse('admin:login')))

    def test_staff_without_permissions_is_forbidden(self):
        staff = User.objects.create_user(username='staff', is_staff=True)
        self.client.force_login(staff)
        for url in self.admin_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_with_view_permission_can_view_but_not_add(self):
        staff = User.objects.create_user(username='staff', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_course'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse('admin:planner_course_changelist')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:planner_course_add')).status_code, 403)

    def test_ordinary_user_cannot_post_to_admin(self):
        self.client.force_login(self.alice)
        response = self.client.post(reverse('admin:planner_course_add'), {
            'owner': self.alice.pk, 'code': 'HACK1', 'name': 'Should not save',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(code='HACK1').exists())


class AdminFormValidationTests(AdminTestBase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.superuser)

    def assignment_data(self, **overrides):
        data = {
            'owner': self.alice.pk,
            'course': self.alice_course.pk,
            'title': 'Reading',
            'description': '',
            'due_date': '2026-12-05',
        }
        data.update(overrides)
        return data

    def test_superuser_can_add_assignment_with_matching_owner(self):
        response = self.client.post(reverse('admin:planner_assignment_add'), self.assignment_data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assignment.objects.filter(title='Reading', owner=self.alice).exists())

    def test_add_rejects_mismatched_owner(self):
        response = self.client.post(
            reverse('admin:planner_assignment_add'),
            self.assignment_data(course=self.bob_course.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The selected course belongs to a different user.')
        self.assertFalse(Assignment.objects.filter(title='Reading').exists())

    def test_change_rejects_mismatched_owner(self):
        response = self.client.post(
            reverse('admin:planner_assignment_change', args=[self.assignment.pk]),
            self.assignment_data(title=self.assignment.title, owner=self.bob.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The selected course belongs to a different user.')
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.owner, self.alice)

    def test_course_owner_change_rejected_when_assignments_exist(self):
        response = self.client.post(
            reverse('admin:planner_course_change', args=[self.alice_course.pk]),
            {'owner': self.bob.pk, 'code': 'INF601', 'name': 'Advanced Python', 'description': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This course has assignments belonging to another user.')
        self.alice_course.refresh_from_db()
        self.assertEqual(self.alice_course.owner, self.alice)

    def test_duplicate_course_code_for_same_owner_rejected(self):
        response = self.client.post(
            reverse('admin:planner_course_add'),
            {'owner': self.alice.pk, 'code': 'INF601', 'name': 'Duplicate', 'description': ''},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You already have a course with this code.')
        self.assertEqual(Course.objects.filter(owner=self.alice, code='INF601').count(), 1)

    def test_same_course_code_for_different_owner_allowed(self):
        response = self.client.post(
            reverse('admin:planner_course_add'),
            {'owner': self.bob.pk, 'code': 'INF601', 'name': 'Advanced Python', 'description': ''},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(owner=self.bob, code='INF601').exists())


class AdminSearchFilterTests(AdminTestBase):
    def setUp(self):
        super().setUp()
        Assignment.objects.create(
            owner=self.bob, course=self.bob_course, title='Lab Report', due_date=date(2026, 11, 20),
            is_completed=True,
        )
        self.client.force_login(self.superuser)

    def test_course_search_by_code(self):
        response = self.client.get(reverse('admin:planner_course_changelist'), {'q': 'CS101'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['cl'].result_list), [self.bob_course])

    def test_assignment_search_by_title(self):
        response = self.client.get(reverse('admin:planner_assignment_changelist'), {'q': 'Lab'})
        titles = [a.title for a in response.context['cl'].result_list]
        self.assertEqual(titles, ['Lab Report'])

    def test_assignment_search_by_course_code(self):
        response = self.client.get(reverse('admin:planner_assignment_changelist'), {'q': 'INF601'})
        titles = [a.title for a in response.context['cl'].result_list]
        self.assertEqual(titles, ['Mini Project 6'])

    def test_assignment_filter_by_completion(self):
        url = reverse('admin:planner_assignment_changelist')
        completed = self.client.get(url, {'is_completed__exact': '1'}).context['cl'].result_list
        pending = self.client.get(url, {'is_completed__exact': '0'}).context['cl'].result_list
        self.assertEqual([a.title for a in completed], ['Lab Report'])
        self.assertEqual([a.title for a in pending], ['Mini Project 6'])

    def test_assignment_filter_by_owner(self):
        response = self.client.get(
            reverse('admin:planner_assignment_changelist'), {'owner__id__exact': str(self.bob.pk)},
        )
        self.assertEqual([a.title for a in response.context['cl'].result_list], ['Lab Report'])
