# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.urls import reverse

from planner.models import Assignment, Course

from .helpers import TwoUserTestCase, days_from_today


class AssignmentViewTests(TwoUserTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    def assignment_data(self, **overrides):
        data = {
            'course': self.alice_course.pk,
            'title': 'Reading Quiz',
            'description': 'Chapter 4',
            'due_date': days_from_today(3).isoformat(),
        }
        data.update(overrides)
        return data

    # ----- list -----

    def test_list_shows_only_own_assignments(self):
        response = self.client.get(reverse('planner:assignment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['assignments']), [self.alice_assignment])
        self.assertContains(response, 'Alice Project')
        self.assertNotContains(response, 'Bob Secret Lab')

    def test_list_empty_state(self):
        Assignment.objects.filter(owner=self.alice).delete()
        response = self.client.get(reverse('planner:assignment_list'))
        self.assertContains(response, 'You have not added any assignments yet.')

    # ----- create -----

    def test_create_assignment(self):
        response = self.client.post(reverse('planner:assignment_create'), self.assignment_data())
        self.assertRedirects(response, reverse('planner:assignment_list'))
        assignment = Assignment.objects.get(title='Reading Quiz')
        self.assertEqual(assignment.owner, self.alice)
        self.assertEqual(assignment.course, self.alice_course)
        self.assertEqual(assignment.due_date, days_from_today(3))
        self.assertFalse(assignment.is_completed)

    def test_create_form_course_choices_limited_to_own_courses(self):
        Course.objects.create(owner=self.alice, code='CS101', name='Intro')
        response = self.client.get(reverse('planner:assignment_create'))
        choices = response.context['form'].fields['course'].queryset
        self.assertEqual(set(choices.values_list('owner', flat=True)), {self.alice.pk})
        self.assertEqual(choices.count(), 2)
        self.assertNotContains(response, 'Bob Secret Biology')
        self.assertNotContains(response, f'value="{self.bob_course.pk}"')

    def test_create_preselects_own_course_from_query_string(self):
        response = self.client.get(reverse('planner:assignment_create'), {'course': self.alice_course.pk})
        self.assertEqual(response.context['form'].initial['course'], str(self.alice_course.pk))

    def test_create_ignores_other_users_course_in_query_string(self):
        response = self.client.get(reverse('planner:assignment_create'), {'course': self.bob_course.pk})
        self.assertNotIn('course', response.context['form'].initial)
        self.assertNotContains(response, 'Bob Secret Biology')

    def test_create_with_forged_course_id_rejected(self):
        response = self.client.post(
            reverse('planner:assignment_create'), self.assignment_data(course=self.bob_course.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('course', response.context['form'].errors)
        self.assertFalse(Assignment.objects.filter(title='Reading Quiz').exists())
        self.assertEqual(self.bob_course.assignments.count(), 1)

    def test_create_ignores_forged_owner_field(self):
        self.client.post(reverse('planner:assignment_create'), self.assignment_data(owner=self.bob.pk))
        assignment = Assignment.objects.get(title='Reading Quiz')
        self.assertEqual(assignment.owner, self.alice)

    def test_create_requires_fields(self):
        response = self.client.post(reverse('planner:assignment_create'), {})
        self.assertEqual(response.status_code, 200)
        for field in ('course', 'title', 'due_date'):
            self.assertIn(field, response.context['form'].errors)
        self.assertEqual(Assignment.objects.filter(owner=self.alice).count(), 1)

    def test_create_rejects_invalid_date_and_course_values(self):
        response = self.client.post(
            reverse('planner:assignment_create'), self.assignment_data(due_date='not-a-date', course='abc'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('due_date', response.context['form'].errors)
        self.assertIn('course', response.context['form'].errors)
        self.assertEqual(Assignment.objects.filter(owner=self.alice).count(), 1)

    def test_create_without_courses_redirects_to_add_course(self):
        self.client.force_login(self.alice)
        Course.objects.filter(owner=self.alice).delete()
        response = self.client.get(reverse('planner:assignment_create'))
        self.assertRedirects(response, reverse('planner:course_create'))

    def test_create_follows_safe_next_and_ignores_external_next(self):
        course_url = reverse('planner:course_detail', args=[self.alice_course.pk])
        response = self.client.post(
            reverse('planner:assignment_create'), self.assignment_data(title='One', next=course_url),
        )
        self.assertRedirects(response, course_url)
        response = self.client.post(
            reverse('planner:assignment_create'), self.assignment_data(title='Two', next='https://evil.example/'),
        )
        self.assertRedirects(response, reverse('planner:assignment_list'))

    # ----- update -----

    def test_update_assignment(self):
        url = reverse('planner:assignment_update', args=[self.alice_assignment.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, self.assignment_data(title='Updated', is_completed='on'))
        self.assertRedirects(response, reverse('planner:assignment_list'))
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_assignment.title, 'Updated')
        self.assertTrue(self.alice_assignment.is_completed)
        self.assertEqual(self.alice_assignment.owner, self.alice)

    def test_update_with_forged_course_id_rejected(self):
        url = reverse('planner:assignment_update', args=[self.alice_assignment.pk])
        response = self.client.post(url, self.assignment_data(course=self.bob_course.pk))
        self.assertIn('course', response.context['form'].errors)
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_assignment.course, self.alice_course)
        self.assertEqual(self.alice_assignment.title, 'Alice Project')

    def test_update_ignores_forged_owner_field(self):
        url = reverse('planner:assignment_update', args=[self.alice_assignment.pk])
        self.client.post(url, self.assignment_data(owner=self.bob.pk))
        self.alice_assignment.refresh_from_db()
        self.assertEqual(self.alice_assignment.owner, self.alice)

    def test_cannot_view_or_update_other_users_assignment(self):
        url = reverse('planner:assignment_update', args=[self.bob_assignment.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, 'Bob Secret Lab', status_code=404)
        response = self.client.post(url, self.assignment_data(title='Hacked'))
        self.assertEqual(response.status_code, 404)
        self.bob_assignment.refresh_from_db()
        self.assertEqual(self.bob_assignment.title, 'Bob Secret Lab')

    # ----- delete -----

    def test_delete_assignment(self):
        response = self.client.post(reverse('planner:assignment_delete', args=[self.alice_assignment.pk]))
        self.assertRedirects(response, reverse('planner:assignment_list'))
        self.assertFalse(Assignment.objects.filter(pk=self.alice_assignment.pk).exists())
        self.assertTrue(Course.objects.filter(pk=self.alice_course.pk).exists())

    def test_get_cannot_delete_assignment(self):
        response = self.client.get(reverse('planner:assignment_delete', args=[self.alice_assignment.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Assignment.objects.filter(pk=self.alice_assignment.pk).exists())

    def test_cannot_delete_other_users_assignment(self):
        response = self.client.post(reverse('planner:assignment_delete', args=[self.bob_assignment.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Assignment.objects.filter(pk=self.bob_assignment.pk).exists())

    # ----- toggle -----

    def test_toggle_marks_complete_then_incomplete(self):
        url = reverse('planner:assignment_toggle', args=[self.alice_assignment.pk])
        self.client.post(url)
        self.alice_assignment.refresh_from_db()
        self.assertTrue(self.alice_assignment.is_completed)
        self.client.post(url)
        self.alice_assignment.refresh_from_db()
        self.assertFalse(self.alice_assignment.is_completed)

    def test_toggle_returns_to_safe_next_page(self):
        dashboard = reverse('planner:dashboard')
        response = self.client.post(
            reverse('planner:assignment_toggle', args=[self.alice_assignment.pk]), {'next': dashboard},
        )
        self.assertRedirects(response, dashboard)

    def test_toggle_ignores_external_next(self):
        response = self.client.post(
            reverse('planner:assignment_toggle', args=[self.alice_assignment.pk]),
            {'next': '//evil.example/'},
        )
        self.assertRedirects(response, reverse('planner:assignment_list'))

    def test_get_cannot_toggle(self):
        response = self.client.get(reverse('planner:assignment_toggle', args=[self.alice_assignment.pk]))
        self.assertEqual(response.status_code, 405)
        self.alice_assignment.refresh_from_db()
        self.assertFalse(self.alice_assignment.is_completed)

    def test_cannot_toggle_other_users_assignment(self):
        response = self.client.post(reverse('planner:assignment_toggle', args=[self.bob_assignment.pk]))
        self.assertEqual(response.status_code, 404)
        self.bob_assignment.refresh_from_db()
        self.assertFalse(self.bob_assignment.is_completed)


class AssignmentFilterTests(TwoUserTestCase):
    def setUp(self):
        super().setUp()
        # alice_assignment (from helpers) is pending and due in 7 days.
        self.completed = Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Done Essay',
            due_date=days_from_today(-2), is_completed=True,
        )
        self.overdue = Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Late Homework', due_date=days_from_today(-1),
        )
        # Bob also has an overdue and a completed assignment that must never appear.
        Assignment.objects.create(
            owner=self.bob, course=self.bob_course, title='Bob Overdue', due_date=days_from_today(-3),
        )
        Assignment.objects.create(
            owner=self.bob, course=self.bob_course, title='Bob Done', due_date=days_from_today(-3),
            is_completed=True,
        )
        self.client.force_login(self.alice)

    def titles_for(self, filter_value):
        response = self.client.get(reverse('planner:assignment_list'), {'filter': filter_value})
        self.assertEqual(response.status_code, 200)
        return [a.title for a in response.context['assignments']]

    def test_all_filter(self):
        self.assertEqual(self.titles_for('all'), ['Done Essay', 'Late Homework', 'Alice Project'])

    def test_pending_filter(self):
        self.assertEqual(self.titles_for('pending'), ['Late Homework', 'Alice Project'])

    def test_completed_filter(self):
        self.assertEqual(self.titles_for('completed'), ['Done Essay'])

    def test_overdue_filter(self):
        self.assertEqual(self.titles_for('overdue'), ['Late Homework'])

    def test_due_today_is_not_overdue(self):
        Assignment.objects.create(
            owner=self.alice, course=self.alice_course, title='Due Today', due_date=days_from_today(0),
        )
        self.assertNotIn('Due Today', self.titles_for('overdue'))
        self.assertIn('Due Today', self.titles_for('pending'))

    def test_unknown_filter_falls_back_to_all(self):
        for value in ('bogus', '', "' OR 1=1 --", '<script>'):
            with self.subTest(filter=value):
                response = self.client.get(reverse('planner:assignment_list'), {'filter': value})
                self.assertEqual(response.context['selected_filter'], 'all')
                self.assertEqual(len(response.context['assignments']), 3)

    def test_filters_never_include_other_users_records(self):
        for value in ('all', 'pending', 'completed', 'overdue'):
            with self.subTest(filter=value):
                for title in self.titles_for(value):
                    self.assertFalse(title.startswith('Bob'))

    def test_filter_empty_state_messages(self):
        Assignment.objects.filter(owner=self.alice, due_date__lt=days_from_today(0)).delete()
        response = self.client.get(reverse('planner:assignment_list'), {'filter': 'overdue'})
        self.assertContains(response, 'Nothing is overdue.')
        response = self.client.get(reverse('planner:assignment_list'), {'filter': 'completed'})
        self.assertContains(response, 'No completed assignments yet.')

    def test_status_badges(self):
        response = self.client.get(reverse('planner:assignment_list'))
        self.assertContains(response, 'text-bg-success">Completed')
        self.assertContains(response, 'text-bg-danger">Overdue')
        self.assertContains(response, 'text-bg-warning">Pending')
