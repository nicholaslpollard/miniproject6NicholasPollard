# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.urls import reverse

from planner.models import Assignment, Course

from .helpers import TwoUserTestCase


class CourseViewTests(TwoUserTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    # ----- list -----

    def test_list_shows_only_own_courses(self):
        response = self.client.get(reverse('planner:course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['courses']), [self.alice_course])
        self.assertContains(response, 'Advanced Python')
        self.assertNotContains(response, 'Bob Secret Biology')
        self.assertNotContains(response, 'BIO200')

    def test_list_empty_state(self):
        Course.objects.filter(owner=self.alice).delete()
        response = self.client.get(reverse('planner:course_list'))
        self.assertContains(response, 'You have not added any courses yet.')

    # ----- create -----

    def test_create_course_sets_owner_from_session(self):
        response = self.client.post(reverse('planner:course_create'), {
            'name': 'Statistics', 'code': 'math250', 'description': 'Intro stats',
        })
        course = Course.objects.get(owner=self.alice, code='MATH250')
        self.assertRedirects(response, reverse('planner:course_detail', args=[course.pk]))
        self.assertEqual(course.name, 'Statistics')
        self.assertEqual(course.description, 'Intro stats')

    def test_create_ignores_forged_owner_field(self):
        self.client.post(reverse('planner:course_create'), {
            'name': 'Statistics', 'code': 'MATH250', 'owner': self.bob.pk,
        })
        course = Course.objects.get(code='MATH250')
        self.assertEqual(course.owner, self.alice)
        self.assertFalse(Course.objects.filter(owner=self.bob, code='MATH250').exists())

    def test_create_requires_name_and_code(self):
        response = self.client.post(reverse('planner:course_create'), {'name': '', 'code': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        self.assertIn('code', response.context['form'].errors)
        self.assertEqual(Course.objects.filter(owner=self.alice).count(), 1)

    def test_create_rejects_too_long_code(self):
        response = self.client.post(reverse('planner:course_create'), {'name': 'Long', 'code': 'X' * 21})
        self.assertIn('code', response.context['form'].errors)
        self.assertEqual(Course.objects.filter(owner=self.alice).count(), 1)

    def test_duplicate_code_shows_friendly_error(self):
        response = self.client.post(reverse('planner:course_create'), {'name': 'Again', 'code': 'INF601'})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'code', 'You already have a course with this code.')
        self.assertEqual(Course.objects.filter(owner=self.alice, code='INF601').count(), 1)

    def test_duplicate_code_check_is_case_insensitive(self):
        response = self.client.post(reverse('planner:course_create'), {'name': 'Again', 'code': ' inf601 '})
        self.assertFormError(response.context['form'], 'code', 'You already have a course with this code.')
        self.assertEqual(Course.objects.filter(owner=self.alice).count(), 1)

    def test_code_used_by_another_user_is_allowed(self):
        self.client.post(reverse('planner:course_create'), {'name': 'Biology', 'code': 'BIO200'})
        self.assertTrue(Course.objects.filter(owner=self.alice, code='BIO200').exists())
        self.assertTrue(Course.objects.filter(owner=self.bob, code='BIO200').exists())

    # ----- detail -----

    def test_detail_shows_course_and_its_assignments(self):
        response = self.client.get(reverse('planner:course_detail', args=[self.alice_course.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advanced Python')
        self.assertContains(response, 'Alice Project')
        self.assertContains(response, 'will also permanently delete its 1 assignment.')

    def test_detail_of_other_users_course_returns_404(self):
        response = self.client.get(reverse('planner:course_detail', args=[self.bob_course.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Bob Secret Biology', status_code=404)

    def test_detail_of_nonexistent_course_returns_404(self):
        response = self.client.get(reverse('planner:course_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    # ----- update -----

    def test_update_course(self):
        url = reverse('planner:course_update', args=[self.alice_course.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'name': 'Advanced Python II', 'code': 'inf602', 'description': 'New'})
        self.assertRedirects(response, reverse('planner:course_detail', args=[self.alice_course.pk]))
        self.alice_course.refresh_from_db()
        self.assertEqual(self.alice_course.name, 'Advanced Python II')
        self.assertEqual(self.alice_course.code, 'INF602')
        self.assertEqual(self.alice_course.owner, self.alice)

    def test_update_keeping_same_code_is_not_a_duplicate(self):
        url = reverse('planner:course_update', args=[self.alice_course.pk])
        response = self.client.post(url, {'name': 'Renamed', 'code': 'INF601'})
        self.assertEqual(response.status_code, 302)
        self.alice_course.refresh_from_db()
        self.assertEqual(self.alice_course.name, 'Renamed')

    def test_update_to_existing_code_rejected(self):
        Course.objects.create(owner=self.alice, code='CS101', name='Intro')
        url = reverse('planner:course_update', args=[self.alice_course.pk])
        response = self.client.post(url, {'name': 'Advanced Python', 'code': 'CS101'})
        self.assertFormError(response.context['form'], 'code', 'You already have a course with this code.')
        self.alice_course.refresh_from_db()
        self.assertEqual(self.alice_course.code, 'INF601')

    def test_update_ignores_forged_owner_field(self):
        url = reverse('planner:course_update', args=[self.alice_course.pk])
        self.client.post(url, {'name': 'Advanced Python', 'code': 'INF601', 'owner': self.bob.pk})
        self.alice_course.refresh_from_db()
        self.assertEqual(self.alice_course.owner, self.alice)

    def test_cannot_update_other_users_course(self):
        url = reverse('planner:course_update', args=[self.bob_course.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url, {'name': 'Hacked', 'code': 'HACK'})
        self.assertEqual(response.status_code, 404)
        self.bob_course.refresh_from_db()
        self.assertEqual(self.bob_course.name, 'Bob Secret Biology')
        self.assertEqual(self.bob_course.code, 'BIO200')

    # ----- delete -----

    def test_delete_course_with_post_also_deletes_assignments(self):
        response = self.client.post(reverse('planner:course_delete', args=[self.alice_course.pk]))
        self.assertRedirects(response, reverse('planner:course_list'))
        self.assertFalse(Course.objects.filter(pk=self.alice_course.pk).exists())
        self.assertFalse(Assignment.objects.filter(pk=self.alice_assignment.pk).exists())
        # Bob's data is untouched.
        self.assertTrue(Course.objects.filter(pk=self.bob_course.pk).exists())
        self.assertTrue(Assignment.objects.filter(pk=self.bob_assignment.pk).exists())

    def test_get_cannot_delete_course(self):
        response = self.client.get(reverse('planner:course_delete', args=[self.alice_course.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Course.objects.filter(pk=self.alice_course.pk).exists())

    def test_cannot_delete_other_users_course(self):
        response = self.client.post(reverse('planner:course_delete', args=[self.bob_course.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Course.objects.filter(pk=self.bob_course.pk).exists())
        self.assertTrue(Assignment.objects.filter(pk=self.bob_assignment.pk).exists())

    def test_delete_ignores_external_next_url(self):
        response = self.client.post(
            reverse('planner:course_delete', args=[self.alice_course.pk]), {'next': 'https://evil.example/'},
        )
        self.assertRedirects(response, reverse('planner:course_list'))
