from django.contrib import admin
from .models import (
    Period, Classroom, TimetableEntry,
    ExamRoutine, Syllabus, Result, Routine, GalleryItem,
    AttendanceRecord, GradeScale, GradeBand,
    Exam, ExamMark, Assignment,
)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "start_time", "end_time")
    ordering = ("order",)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ("class_name", "section", "subject", "teacher", "day_of_week", "period", "start_time", "end_time")
    list_filter = ("day_of_week", "class_name", "section", "teacher")
    search_fields = ("class_name__name", "section__name", "subject__name", "teacher__first_name", "teacher__last_name")


@admin.register(ExamRoutine)
class ExamRoutineAdmin(admin.ModelAdmin):
    list_display = ("exam_name", "class_name", "section", "subject", "date", "start_time", "end_time")
    list_filter = ("date", "class_name", "section")


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ("class_name", "section", "subject", "file")
    search_fields = ("class_name", "section", "subject")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("year", "class_name", "exam_name", "file")
    list_filter = ("year", "class_name")
    search_fields = ("exam_name",)


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("class_name", "category", "file")
    list_filter = ("category",)


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("caption", "uploaded_at")
    search_fields = ("caption",)


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "timetable", "student", "status", "marked_by", "marked_at")
    list_filter = ("status", "date", "marked_by")
    search_fields = ("student__first_name", "student__last_name")


class GradeBandInline(admin.TabularInline):
    model = GradeBand
    extra = 1


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    inlines = [GradeBandInline]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "class_name", "section", "is_published", "created_at")
    list_filter = ("is_published", "class_name", "section")
    search_fields = ("name",)


@admin.register(ExamMark)
class ExamMarkAdmin(admin.ModelAdmin):
    list_display = ("exam", "student", "subject", "score", "letter", "gpa")
    list_filter = ("exam", "subject", "letter")
    search_fields = ("student__first_name", "student__last_name", "subject__name")
@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "class_name", "section", "subject", "teacher", "due_date", "created_at")
    list_filter = ("class_name", "section", "subject", "teacher")
    search_fields = ("title", "instructions")