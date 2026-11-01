# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Course(models.Model):
    """A course owned by a single user."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'code'],
                name='unique_course_code_per_owner',
                violation_error_message='You already have a course with this code.',
            ),
        ]

    def __str__(self):
        return f'{self.code} - {self.name}'

    def has_mismatched_assignments(self):
        """Return True if any of this course's assignments belong to a different user."""
        if not self.pk or not self.owner_id:
            return False
        return self.assignments.exclude(owner_id=self.owner_id).exists()

    def clean(self):
        super().clean()
        # Changing a course's owner would leave its assignments owned by someone else.
        if self.has_mismatched_assignments():
            raise ValidationError({
                'owner': 'This course has assignments belonging to another user. '
                         'Reassign or remove those assignments first.',
            })

    def save(self, *args, **kwargs):
        # Safety net for code paths that skip full_clean(), such as a direct save().
        if self.has_mismatched_assignments():
            raise ValidationError('A course cannot be saved while it has assignments '
                                  'belonging to another user.')
        super().save(*args, **kwargs)


class Assignment(models.Model):
    """An assignment owned by a user and linked to one of that user's courses."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'title']

    def __str__(self):
        return f'{self.title} (due {self.due_date})'

    def clean(self):
        super().clean()
        if self.owner_id and self.course_id and self.course.owner_id != self.owner_id:
            raise ValidationError({
                'course': 'The selected course belongs to a different user.',
            })

    def save(self, *args, **kwargs):
        # Safety net for code paths that skip full_clean(), such as objects.create().
        if self.owner_id and self.course_id and self.course.owner_id != self.owner_id:
            raise ValidationError('An assignment must belong to the same user as its course.')
        super().save(*args, **kwargs)
