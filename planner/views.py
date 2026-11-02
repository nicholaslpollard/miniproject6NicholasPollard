
# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AssignmentForm, CourseForm, RegistrationForm
from .models import Assignment, Course

ASSIGNMENT_FILTERS = {
    'all': 'All',
    'pending': 'Pending',
    'completed': 'Completed',
    'overdue': 'Overdue',
}


def get_safe_next_url(request, default):
    """Return the 'next' URL only if it points to this site; otherwise return default."""
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return next_url
    return default


def form_data(request):
    """Submitted data for a POST (even an empty one), or None so GET shows an unbound form."""
    return request.POST if request.method == 'POST' else None


# ---------- Public pages ----------

def home(request):
    return render(request, 'planner/home.html')


def about(request):
    return render(request, 'planner/about.html')


def features(request):
    return render(request, 'planner/features.html')


def help_page(request):
    return render(request, 'planner/help.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('planner:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('planner:dashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


# ---------- Dashboard ----------

@login_required
def dashboard(request):
    today = timezone.localdate()
    assignments = Assignment.objects.filter(owner=request.user).select_related('course')
    pending = assignments.filter(is_completed=False)

    context = {
        'total_count': assignments.count(),
        'completed_count': assignments.filter(is_completed=True).count(),
        'pending_count': pending.count(),
        'overdue_count': pending.filter(due_date__lt=today).count(),
        'overdue_assignments': pending.filter(due_date__lt=today)[:5],
        'upcoming_assignments': pending.filter(due_date__gte=today)[:5],
        'courses': Course.objects.filter(owner=request.user).annotate(
            assignment_count=Count('assignments'),
            pending_count=Count('assignments', filter=Q(assignments__is_completed=False)),
        ),
    }
    return render(request, 'planner/dashboard.html', context)


# ---------- Courses ----------

@login_required
def course_list(request):
    courses = Course.objects.filter(owner=request.user).annotate(
        assignment_count=Count('assignments'),
        pending_count=Count('assignments', filter=Q(assignments__is_completed=False)),
    )
    return render(request, 'planner/course_list.html', {'courses': courses})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk, owner=request.user)
    assignments = course.assignments.filter(owner=request.user).select_related('course')
    return render(request, 'planner/course_detail.html', {
        'course': course,
        'assignments': assignments,
    })


def save_course_form(request, form, success_message):
    """Save a valid CourseForm, turning a rare duplicate-code race into a form error."""
    try:
        with transaction.atomic():
            course = form.save()
    except IntegrityError:
        form.add_error('code', 'You already have a course with this code.')
        return None
    messages.success(request, success_message.format(course=course))
    return course


@login_required
def course_create(request):
    form = CourseForm(form_data(request), owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            course = save_course_form(request, form, 'Course "{course}" was created.')
            if course:
                return redirect('planner:course_detail', pk=course.pk)
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'planner/course_form.html', {'form': form})


@login_required
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk, owner=request.user)
    form = CourseForm(form_data(request), instance=course, owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            course = save_course_form(request, form, 'Course "{course}" was updated.')
            if course:
                return redirect('planner:course_detail', pk=course.pk)
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'planner/course_form.html', {'form': form, 'course': course})


@login_required
@require_POST
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, owner=request.user)
    name = str(course)
    course.delete()  # also deletes the course's assignments (on_delete=CASCADE)
    messages.success(request, f'Course "{name}" and its assignments were deleted.')
    return redirect('planner:course_list')


# ---------- Assignments ----------

@login_required
def assignment_list(request):
    selected = request.GET.get('filter', 'all')
    if selected not in ASSIGNMENT_FILTERS:
        selected = 'all'

    # Search assignments using a trimmed, length-limited query.
    search_query = request.GET.get('q', '').strip()[:100]

    today = timezone.localdate()
    assignments = Assignment.objects.filter(owner=request.user).select_related('course')
    if selected == 'pending':
        assignments = assignments.filter(is_completed=False)
    elif selected == 'completed':
        assignments = assignments.filter(is_completed=True)
    elif selected == 'overdue':
        assignments = assignments.filter(is_completed=False, due_date__lt=today)

    # Search only within the current user's filtered assignments.
    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(course__name__icontains=search_query)
            | Q(course__code__icontains=search_query)
        )

    return render(request, 'planner/assignment_list.html', {
        'assignments': assignments,
        'filters': ASSIGNMENT_FILTERS,
        'selected_filter': selected,
        'search_query': search_query,
    })


@login_required
def assignment_create(request):
    if not Course.objects.filter(owner=request.user).exists():
        messages.info(request, 'Add a course before creating assignments.')
        return redirect('planner:course_create')

    initial = {}
    course_id = request.GET.get('course', '')
    if course_id.isdigit() and Course.objects.filter(pk=course_id, owner=request.user).exists():
        initial['course'] = course_id

    form = AssignmentForm(form_data(request), initial=initial, owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Assignment "{assignment.title}" was created.')
            return redirect(get_safe_next_url(request, reverse('planner:assignment_list')))
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'planner/assignment_form.html', {'form': form})


@login_required
def assignment_update(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, owner=request.user)
    form = AssignmentForm(form_data(request), instance=assignment, owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            assignment = form.save()
            messages.success(request, f'Assignment "{assignment.title}" was updated.')
            return redirect(get_safe_next_url(request, reverse('planner:assignment_list')))
        messages.error(request, 'Please correct the errors below.')
    return render(request, 'planner/assignment_form.html', {'form': form, 'assignment': assignment})


@login_required
@require_POST
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, owner=request.user)
    title = assignment.title
    assignment.delete()
    messages.success(request, f'Assignment "{title}" was deleted.')
    return redirect(get_safe_next_url(request, reverse('planner:assignment_list')))


@login_required
@require_POST
def assignment_toggle(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, owner=request.user)
    assignment.is_completed = not assignment.is_completed
    assignment.save(update_fields=['is_completed', 'updated_at'])
    status = 'completed' if assignment.is_completed else 'not completed'
    messages.success(request, f'"{assignment.title}" marked as {status}.')
    return redirect(get_safe_next_url(request, reverse('planner:assignment_list')))
