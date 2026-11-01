# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.test import Client
from django.urls import reverse

from planner.models import Assignment, Course

from .helpers import TwoUserTestCase, days_from_today


class AnonymousAccessTests(TwoUserTestCase):
    def private_urls(self):
        course_pk = self.alice_course.pk
        assignment_pk = self.alice_assignment.pk
        return [
            reverse('planner:dashboard'),
            reverse('planner:course_list'),
            reverse('planner:course_create'),
            reverse('planner:course_detail', args=[course_pk]),
            reverse('planner:course_update', args=[course_pk]),
            reverse('planner:assignment_list'),
            reverse('planner:assignment_create'),
            reverse('planner:assignment_update', args=[assignment_pk]),
        ]

    def test_anonymous_get_redirects_to_login(self):
        for url in self.private_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('planner:login')}?next={url}")

    def test_anonymous_post_cannot_change_data(self):
        posts = [
            (reverse('planner:course_create'), {'name': 'Anon', 'code': 'ANON1'}),
            (reverse('planner:course_update', args=[self.alice_course.pk]), {'name': 'Anon', 'code': 'ANON2'}),
            (reverse('planner:course_delete', args=[self.alice_course.pk]), {}),
            (reverse('planner:assignment_create'), {'course': self.alice_course.pk, 'title': 'Anon',
                                                    'due_date': '2026-12-01'}),
            (reverse('planner:assignment_delete', args=[self.alice_assignment.pk]), {}),
            (reverse('planner:assignment_toggle', args=[self.alice_assignment.pk]), {}),
        ]
        for url, data in posts:
            with self.subTest(url=url):
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response['Location'].startswith(reverse('planner:login')))

        self.alice_course.refresh_from_db()
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_course.name, 'Advanced Python')
        self.assertFalse(self.alice_assignment.is_completed)
        self.assertEqual(Course.objects.count(), 2)
        self.assertEqual(Assignment.objects.count(), 2)

    def test_public_pages_available_anonymously(self):
        for name in ('home', 'about', 'features', 'help', 'login', 'register'):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f'planner:{name}')).status_code, 200)


class CrossAccountIsolationTests(TwoUserTestCase):
    """Alice tries to reach Bob's records by guessing their IDs."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    def test_other_users_objects_return_404_without_leaking_details(self):
        urls = [
            reverse('planner:course_detail', args=[self.bob_course.pk]),
            reverse('planner:course_update', args=[self.bob_course.pk]),
            reverse('planner:assignment_update', args=[self.bob_assignment.pk]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                for secret in ('Bob Secret Biology', 'BIO200', 'Bob private notes', 'Bob Secret Lab'):
                    self.assertNotContains(response, secret, status_code=404)

    def test_other_users_and_missing_ids_give_identical_responses(self):
        # A 404 for "exists but not yours" must look the same as "does not exist".
        missing = self.client.get(reverse('planner:course_detail', args=[99999]))
        not_mine = self.client.get(reverse('planner:course_detail', args=[self.bob_course.pk]))
        self.assertEqual(missing.status_code, not_mine.status_code)

    def test_cross_account_mutations_leave_data_unchanged(self):
        posts = [
            (reverse('planner:course_update', args=[self.bob_course.pk]), {'name': 'Hacked', 'code': 'HACKED'}),
            (reverse('planner:course_delete', args=[self.bob_course.pk]), {}),
            (reverse('planner:assignment_update', args=[self.bob_assignment.pk]),
             {'course': self.alice_course.pk, 'title': 'Hacked', 'due_date': '2026-12-01'}),
            (reverse('planner:assignment_toggle', args=[self.bob_assignment.pk]), {}),
            (reverse('planner:assignment_delete', args=[self.bob_assignment.pk]), {}),
        ]
        for url, data in posts:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, data).status_code, 404)

        self.bob_course.refresh_from_db()
        self.bob_assignment.refresh_from_db()
        self.assertEqual(self.bob_course.name, 'Bob Secret Biology')
        self.assertEqual(self.bob_assignment.title, 'Bob Secret Lab')
        self.assertEqual(self.bob_assignment.owner, self.bob)
        self.assertEqual(self.bob_assignment.course, self.bob_course)
        self.assertFalse(self.bob_assignment.is_completed)

    def test_cannot_move_own_assignment_into_other_users_course(self):
        url = reverse('planner:assignment_update', args=[self.alice_assignment.pk])
        response = self.client.post(url, {
            'course': self.bob_course.pk, 'title': 'Alice Project', 'due_date': days_from_today(7).isoformat(),
            'owner': self.bob.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('course', response.context['form'].errors)
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_assignment.course, self.alice_course)
        self.assertEqual(self.alice_assignment.owner, self.alice)
        self.assertEqual(self.bob_course.assignments.count(), 1)

    def test_dashboard_statistics_are_isolated(self):
        # Give Bob lots of data; Alice's numbers must not change.
        for i in range(3):
            Assignment.objects.create(
                owner=self.bob, course=self.bob_course, title=f'Bob Overdue {i}', due_date=days_from_today(-5),
            )
            Assignment.objects.create(
                owner=self.bob, course=self.bob_course, title=f'Bob Done {i}', due_date=days_from_today(1),
                is_completed=True,
            )
        Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Alice Late', due_date=days_from_today(-1),
        )

        response = self.client.get(reverse('planner:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_count'], 2)
        self.assertEqual(response.context['completed_count'], 0)
        self.assertEqual(response.context['pending_count'], 2)
        self.assertEqual(response.context['overdue_count'], 1)
        self.assertEqual([a.title for a in response.context['overdue_assignments']], ['Alice Late'])
        self.assertEqual([a.title for a in response.context['upcoming_assignments']], ['Alice Project'])
        self.assertEqual(list(response.context['courses']), [self.alice_course])
        self.assertNotContains(response, 'Bob')
        self.assertNotContains(response, 'BIO200')

    def test_dashboard_upcoming_is_ordered_and_excludes_completed(self):
        Assignment.objects.create(owner=self.alice, course=self.alice_course, title='Soon', due_date=days_from_today(1))
        Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Finished', due_date=days_from_today(2),
            is_completed=True,
        )
        response = self.client.get(reverse('planner:dashboard'))
        self.assertEqual([a.title for a in response.context['upcoming_assignments']], ['Soon', 'Alice Project'])
        self.assertEqual(response.context['completed_count'], 1)

    def test_dashboard_empty_state_for_new_user(self):
        Course.objects.filter(owner=self.alice).delete()
        response = self.client.get(reverse('planner:dashboard'))
        self.assertEqual(response.context['total_count'], 0)
        self.assertContains(response, 'You have not added any courses yet.')
        self.assertContains(response, 'Nothing upcoming.')


class CsrfProtectionTests(TwoUserTestCase):
    """The default test client skips CSRF checks; this client enforces them like a browser would."""

    def setUp(self):
        super().setUp()
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.csrf_client.force_login(self.alice)

    def test_state_changing_posts_without_token_are_rejected(self):
        posts = [
            (reverse('planner:course_create'), {'name': 'No Token', 'code': 'NOTOKEN'}),
            (reverse('planner:course_update', args=[self.alice_course.pk]), {'name': 'Changed', 'code': 'INF601'}),
            (reverse('planner:course_delete', args=[self.alice_course.pk]), {}),
            (reverse('planner:assignment_create'), {'course': self.alice_course.pk, 'title': 'No Token',
                                                    'due_date': '2026-12-01'}),
            (reverse('planner:assignment_toggle', args=[self.alice_assignment.pk]), {}),
            (reverse('planner:assignment_delete', args=[self.alice_assignment.pk]), {}),
            (reverse('planner:logout'), {}),
        ]
        for url, data in posts:
            with self.subTest(url=url):
                self.assertEqual(self.csrf_client.post(url, data).status_code, 403)

        self.alice_course.refresh_from_db()
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_course.name, 'Advanced Python')
        self.assertFalse(self.alice_assignment.is_completed)
        self.assertFalse(Course.objects.filter(code='NOTOKEN').exists())
        self.assertFalse(Assignment.objects.filter(title='No Token').exists())

    def test_post_with_valid_token_succeeds(self):
        # Load a page to receive the CSRF cookie, then submit the token like a real form would.
        self.csrf_client.get(reverse('planner:course_create'))
        token = self.csrf_client.cookies['csrftoken'].value
        response = self.csrf_client.post(
            reverse('planner:assignment_toggle', args=[self.alice_assignment.pk]),
            {'csrfmiddlewaretoken': token},
        )
        self.assertEqual(response.status_code, 302)
        self.alice_assignment.refresh_from_db()
        self.assertTrue(self.alice_assignment.is_completed)

    def test_registration_without_token_rejected(self):
        anonymous = Client(enforce_csrf_checks=True)
        response = anonymous.post(reverse('planner:register'), {
            'username': 'csrfuser', 'password1': 'Unit-Test-Passw0rd!', 'password2': 'Unit-Test-Passw0rd!',
        })
        self.assertEqual(response.status_code, 403)


class TemplateEscapingTests(TwoUserTestCase):
    XSS = '<script>alert("xss")</script>'

    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)
        self.course = Course.objects.create(owner=self.alice, code='XSS1', name=self.XSS, description=self.XSS)
        self.assignment = Assignment.objects.create(
            owner=self.alice, course=self.course, title=self.XSS, description=self.XSS, due_date=days_from_today(1),
        )

    def test_user_content_is_escaped_on_every_page(self):
        urls = [
            reverse('planner:dashboard'),
            reverse('planner:course_list'),
            reverse('planner:course_detail', args=[self.course.pk]),
            reverse('planner:course_update', args=[self.course.pk]),
            reverse('planner:assignment_list'),
            reverse('planner:assignment_update', args=[self.assignment.pk]),
            reverse('planner:assignment_create'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, self.XSS)
                self.assertContains(response, '&lt;script&gt;')

    def test_success_message_is_escaped(self):
        response = self.client.post(
            reverse('planner:assignment_toggle', args=[self.assignment.pk]), follow=True,
        )
        self.assertNotContains(response, self.XSS)
        self.assertContains(response, 'marked as completed')


class InvalidInputTests(TwoUserTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    def test_nonexistent_ids_return_404_not_500(self):
        urls = [
            ('get', reverse('planner:course_detail', args=[0])),
            ('get', reverse('planner:course_update', args=[123456])),
            ('post', reverse('planner:course_delete', args=[123456])),
            ('get', reverse('planner:assignment_update', args=[123456])),
            ('post', reverse('planner:assignment_delete', args=[123456])),
            ('post', reverse('planner:assignment_toggle', args=[123456])),
        ]
        for method, url in urls:
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url).status_code, 404)

    def test_non_numeric_ids_do_not_match_urls(self):
        self.assertEqual(self.client.get('/courses/abc/').status_code, 404)
        self.assertEqual(self.client.post('/assignments/abc/toggle/').status_code, 404)

    def test_invalid_course_query_parameter_is_ignored(self):
        for value in ('abc', '-1', '99999', "1 OR 1=1"):
            with self.subTest(course=value):
                response = self.client.get(reverse('planner:assignment_create'), {'course': value})
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('course', response.context['form'].initial)

    def test_invalid_payload_does_not_mutate(self):
        url = reverse('planner:assignment_update', args=[self.alice_assignment.pk])
        response = self.client.post(url, {'course': '', 'title': '', 'due_date': '2026-13-45'})
        self.assertEqual(response.status_code, 200)
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_assignment.title, 'Alice Project')
        self.assertEqual(self.alice_assignment.due_date, days_from_today(7))
