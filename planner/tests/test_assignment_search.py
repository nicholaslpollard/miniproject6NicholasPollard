
# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.urls import reverse

from planner.models import Assignment, Course

from .helpers import TwoUserTestCase, days_from_today


class AssignmentSearchTests(TwoUserTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)
        self.url = reverse('planner:assignment_list')

        self.math_course = Course.objects.create(
            owner=self.alice,
            code='MAT250',
            name='Statistics',
        )

        self.math_assignment = Assignment.objects.create(
            owner=self.alice,
            course=self.math_course,
            title='Research Paper',
            description='Prepare graphs and histograms',
            due_date=days_from_today(3),
        )

        self.completed_assignment = Assignment.objects.create(
            owner=self.alice,
            course=self.math_course,
            title='Statistics Final',
            due_date=days_from_today(-1),
            is_completed=True,
        )

    def search(self, query, filter_value='all'):
        return self.client.get(self.url, {
            'q': query,
            'filter': filter_value,
        })

    def test_search_by_assignment_title(self):
        response = self.search('research')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['assignments']),
            [self.math_assignment],
        )

    def test_search_is_case_insensitive(self):
        response = self.search('RESEARCH')
        self.assertEqual(
            list(response.context['assignments']),
            [self.math_assignment],
        )

    def test_search_by_description(self):
        response = self.search('histograms')
        self.assertEqual(
            list(response.context['assignments']),
            [self.math_assignment],
        )

    def test_search_by_course_name(self):
        response = self.search('Statistics')
        self.assertEqual(
            set(response.context['assignments']),
            {self.math_assignment, self.completed_assignment},
        )

    def test_search_by_course_code(self):
        response = self.search('MAT250')
        self.assertEqual(
            set(response.context['assignments']),
            {self.math_assignment, self.completed_assignment},
        )

    def test_search_combines_with_status_filter(self):
        response = self.search('Statistics', 'completed')
        self.assertEqual(
            list(response.context['assignments']),
            [self.completed_assignment],
        )

        response = self.search('Statistics', 'pending')
        self.assertEqual(
            list(response.context['assignments']),
            [self.math_assignment],
        )

    def test_search_never_returns_other_users_assignments(self):
        response = self.search('BIO200')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['assignments']), [])
        self.assertNotContains(response, 'Bob Secret Lab')

    def test_no_matching_results_message(self):
        response = self.search('nonexistentkeyword')
        self.assertContains(
            response,
            'No assignments match your search.',
        )

    def test_search_text_is_trimmed_and_limited(self):
        response = self.search('  research  ')
        self.assertEqual(response.context['search_query'], 'research')

        response = self.search('x' * 150)
        self.assertEqual(len(response.context['search_query']), 100)

    def test_filter_links_preserve_search_text(self):
        response = self.search('Statistics')
        self.assertContains(
            response,
            '?filter=completed&amp;q=Statistics',
        )
        self.assertContains(
            response,
            'name="q"',
        )

    def test_search_does_not_modify_assignments(self):
        before = Assignment.objects.count()
        response = self.search('Research')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Assignment.objects.count(), before)

    def test_special_characters_are_handled_safely(self):
        response = self.search('<script>alert(1)</script>')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script>')
        self.assertEqual(list(response.context['assignments']), [])
