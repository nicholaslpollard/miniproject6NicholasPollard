# INF601 - Advanced Programming in Python
# Nicholas Pollard
# Mini Project 6

from django.contrib import admin

from .models import Assignment, Course

admin.site.site_header = 'Study Planner Administration'
admin.site.site_title = 'Study Planner Admin'
admin.site.index_title = 'Manage courses and assignments'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'owner', 'created_at', 'updated_at')
    list_filter = ('owner',)
    search_fields = ('code', 'name', 'owner__username')
    ordering = ('owner__username', 'code')
    list_select_related = ('owner',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('owner', 'code', 'name', 'description')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'owner', 'due_date', 'is_completed')
    list_filter = ('is_completed', 'due_date', 'owner')
    search_fields = ('title', 'course__code', 'course__name', 'owner__username')
    ordering = ('due_date', 'title')
    list_select_related = ('course', 'owner')
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('owner', 'course', 'title', 'description')}),
        ('Status', {'fields': ('due_date', 'is_completed')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Show each course's owner in the dropdown so mismatches are easy to avoid.
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'course':
            formfield.queryset = formfield.queryset.select_related('owner')
            formfield.label_from_instance = lambda course: f'{course} ({course.owner})'
        return formfield
