# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from planner.models import Assignment, Course

User = get_user_model()


class CourseModelTests(TestCase):
    def setUp(self):
        # Users are created without passwords; they exist only in the test database.
        self.alice = User.objects.create_user(username='alice')
        self.bob = User.objects.create_user(username='bob')

    def test_create_course_for_user(self):
        course = Course.objects.create(
            owner=self.alice, code='INF601', name='Advanced Python', description='Django projects',
        )
        course.refresh_from_db()
        self.assertEqual(course.owner, self.alice)
        self.assertEqual(course.code, 'INF601')
        self.assertEqual(course.name, 'Advanced Python')
        self.assertEqual(course.description, 'Django projects')
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)
        self.assertIn(course, self.alice.courses.all())

    def test_description_is_optional(self):
        course = Course(owner=self.alice, code='INF601', name='Advanced Python')
        course.full_clean()  # should not raise
        course.save()
        self.assertEqual(course.description, '')

    def test_str(self):
        course = Course(owner=self.alice, code='INF601', name='Advanced Python')
        self.assertEqual(str(course), 'INF601 - Advanced Python')

    def test_required_fields(self):
        course = Course()
        with self.assertRaises(ValidationError) as ctx:
            course.full_clean()
        for field in ('owner', 'code', 'name'):
            self.assertIn(field, ctx.exception.message_dict)

    def test_max_lengths_enforced(self):
        course = Course(owner=self.alice, code='X' * 21, name='N' * 101)
        with self.assertRaises(ValidationError) as ctx:
            course.full_clean()
        self.assertIn('code', ctx.exception.message_dict)
        self.assertIn('name', ctx.exception.message_dict)

    def test_code_unique_per_user_validation(self):
        Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        duplicate = Course(owner=self.alice, code='INF601', name='Another name')
        with self.assertRaises(ValidationError) as ctx:
            duplicate.full_clean()
        self.assertIn('You already have a course with this code.', str(ctx.exception))

    def test_code_unique_per_user_database_constraint(self):
        Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.create(owner=self.alice, code='INF601', name='Duplicate')

    def test_same_code_allowed_for_different_users(self):
        Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        other = Course(owner=self.bob, code='INF601', name='Advanced Python')
        other.full_clean()  # should not raise
        other.save()
        self.assertEqual(Course.objects.filter(code='INF601').count(), 2)

    def test_default_ordering_by_code(self):
        Course.objects.create(owner=self.alice, code='MATH101', name='Algebra')
        Course.objects.create(owner=self.alice, code='CS101', name='Intro')
        codes = list(Course.objects.values_list('code', flat=True))
        self.assertEqual(codes, ['CS101', 'MATH101'])

    def test_deleting_course_deletes_its_assignments(self):
        course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        Assignment.objects.create(owner=self.alice, course=course, title='Project', due_date=date(2026, 12, 1))
        course.delete()
        self.assertFalse(Assignment.objects.exists())

    def test_deleting_user_deletes_their_courses_only(self):
        Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        bob_course = Course.objects.create(owner=self.bob, code='INF601', name='Advanced Python')
        self.alice.delete()
        self.assertEqual(list(Course.objects.all()), [bob_course])

    def test_cannot_change_owner_when_assignments_belong_to_previous_owner(self):
        course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        Assignment.objects.create(owner=self.alice, course=course, title='Project', due_date=date(2026, 12, 1))
        course.owner = self.bob
        with self.assertRaises(ValidationError) as ctx:
            course.full_clean()
        self.assertIn('owner', ctx.exception.message_dict)

    def test_direct_save_rejects_owner_change_when_assignments_exist(self):
        course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        Assignment.objects.create(owner=self.alice, course=course, title='Project', due_date=date(2026, 12, 1))
        course.owner = self.bob
        with self.assertRaises(ValidationError):
            course.save()
        course.refresh_from_db()
        self.assertEqual(course.owner, self.alice)

    def test_direct_save_allows_updating_other_fields_with_assignments(self):
        course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        Assignment.objects.create(owner=self.alice, course=course, title='Project', due_date=date(2026, 12, 1))
        course.code = 'INF602'
        course.name = 'Even More Python'
        course.description = 'Updated description'
        course.save()
        course.refresh_from_db()
        self.assertEqual(course.owner, self.alice)
        self.assertEqual(course.code, 'INF602')
        self.assertEqual(course.name, 'Even More Python')
        self.assertEqual(course.description, 'Updated description')

    def test_direct_save_allows_owner_change_without_assignments(self):
        course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        course.owner = self.bob
        course.save()
        course.refresh_from_db()
        self.assertEqual(course.owner, self.bob)

    def test_owner_change_allowed_after_assignments_reassigned(self):
        course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        Assignment.objects.create(owner=self.alice, course=course, title='Project', due_date=date(2026, 12, 1))
        # Moving the assignments in the same step as the course keeps ownership consistent.
        course.assignments.update(owner=self.bob)
        course.owner = self.bob
        course.full_clean()
        course.save()
        course.refresh_from_db()
        self.assertEqual(course.owner, self.bob)
        self.assertEqual(list(course.assignments.values_list('owner', flat=True)), [self.bob.pk])


class AssignmentModelTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice')
        self.bob = User.objects.create_user(username='bob')
        self.alice_course = Course.objects.create(owner=self.alice, code='INF601', name='Advanced Python')
        self.bob_course = Course.objects.create(owner=self.bob, code='CS101', name='Intro to CS')

    def make_assignment(self, **kwargs):
        values = {
            'owner': self.alice,
            'course': self.alice_course,
            'title': 'Mini Project 6',
            'due_date': date(2026, 12, 1),
        }
        values.update(kwargs)
        return Assignment(**values)

    def test_create_assignment(self):
        assignment = self.make_assignment(description='Study planner')
        assignment.full_clean()
        assignment.save()
        assignment.refresh_from_db()
        self.assertEqual(assignment.owner, self.alice)
        self.assertEqual(assignment.course, self.alice_course)
        self.assertEqual(assignment.title, 'Mini Project 6')
        self.assertEqual(assignment.description, 'Study planner')
        self.assertEqual(assignment.due_date, date(2026, 12, 1))
        self.assertIsNotNone(assignment.created_at)
        self.assertIsNotNone(assignment.updated_at)

    def test_defaults(self):
        assignment = self.make_assignment()
        assignment.save()
        self.assertFalse(assignment.is_completed)
        self.assertEqual(assignment.description, '')

    def test_relationships(self):
        assignment = self.make_assignment()
        assignment.save()
        self.assertIn(assignment, self.alice_course.assignments.all())
        self.assertIn(assignment, self.alice.assignments.all())
        self.assertFalse(self.bob.assignments.exists())

    def test_str(self):
        assignment = self.make_assignment()
        self.assertEqual(str(assignment), 'Mini Project 6 (due 2026-12-01)')

    def test_completed_status_can_change(self):
        assignment = self.make_assignment()
        assignment.save()
        assignment.is_completed = True
        assignment.save()
        assignment.refresh_from_db()
        self.assertTrue(assignment.is_completed)
        assignment.is_completed = False
        assignment.save()
        assignment.refresh_from_db()
        self.assertFalse(assignment.is_completed)

    def test_required_fields(self):
        assignment = Assignment()
        with self.assertRaises(ValidationError) as ctx:
            assignment.full_clean()
        for field in ('owner', 'course', 'title', 'due_date'):
            self.assertIn(field, ctx.exception.message_dict)

    def test_title_max_length(self):
        assignment = self.make_assignment(title='T' * 201)
        with self.assertRaises(ValidationError) as ctx:
            assignment.full_clean()
        self.assertIn('title', ctx.exception.message_dict)

    def test_course_owned_by_another_user_fails_validation(self):
        assignment = self.make_assignment(course=self.bob_course)
        with self.assertRaises(ValidationError) as ctx:
            assignment.full_clean()
        self.assertIn('course', ctx.exception.message_dict)

    def test_course_owned_by_another_user_cannot_be_saved(self):
        with self.assertRaises(ValidationError):
            Assignment.objects.create(
                owner=self.alice, course=self.bob_course, title='Sneaky', due_date=date(2026, 12, 1),
            )
        self.assertFalse(Assignment.objects.exists())

    def test_ordering_by_due_date(self):
        later = self.make_assignment(title='Later', due_date=date(2026, 12, 15))
        sooner = self.make_assignment(title='Sooner', due_date=date(2026, 11, 15))
        later.save()
        sooner.save()
        self.assertEqual(list(Assignment.objects.all()), [sooner, later])

    def test_deleting_assignment_keeps_course(self):
        assignment = self.make_assignment()
        assignment.save()
        assignment.delete()
        self.assertTrue(Course.objects.filter(pk=self.alice_course.pk).exists())

    def test_deleting_user_deletes_their_assignments(self):
        self.make_assignment().save()
        self.alice.delete()
        self.assertFalse(Assignment.objects.exists())
        self.assertTrue(Course.objects.filter(pk=self.bob_course.pk).exists())
