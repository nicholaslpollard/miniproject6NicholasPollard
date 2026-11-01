# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Assignment, Course


class BootstrapFormMixin:
    """Add Bootstrap CSS classes to every widget in the form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            elif isinstance(widget, forms.Select):
                css_class = 'form-select'
            else:
                css_class = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css_class}".strip()


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    """
    Sign-up form built on Django's UserCreationForm (password hashing and validation included).

    Only username, email and the two password fields are accepted, so a request cannot
    set is_staff, is_superuser, groups or permissions.
    """

    email = forms.EmailField(required=False, help_text='Optional.')

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email')


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """Django's standard login form with Bootstrap styling."""


class CourseForm(BootstrapFormMixin, forms.ModelForm):
    """Create or edit a course. The owner is supplied by the view, never by the user."""

    class Meta:
        model = Course
        fields = ('name', 'code', 'description')
        labels = {'name': 'Course name', 'code': 'Course code'}
        help_texts = {'code': 'For example INF601. Codes are saved in uppercase.'}
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.instance.owner = owner

    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        # The owner isn't a form field, so Django won't check the (owner, code)
        # constraint for us. Check it here to show a friendly error.
        duplicates = Course.objects.filter(owner=self.owner, code=code).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('You already have a course with this code.')
        return code


class AssignmentForm(BootstrapFormMixin, forms.ModelForm):
    """Create or edit an assignment. Only the user's own courses can be chosen."""

    class Meta:
        model = Assignment
        fields = ('course', 'title', 'description', 'due_date', 'is_completed')
        labels = {'is_completed': 'Completed'}
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.owner = owner
        # Limiting the queryset means a submitted course ID belonging to someone
        # else fails validation with "Select a valid choice".
        self.fields['course'].queryset = Course.objects.filter(owner=owner)
        self.fields['course'].empty_label = 'Select a course'
