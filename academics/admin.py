from django.contrib import admin
from .models import Period, Classroom, TimetableEntry, ExamRoutine, Syllabus, Result, Routine, GalleryItem


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "start_time", "end_time")
    ordering = ("order",)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ("day_of_week", "period", "class_name", "section", "subject", "start_time", "end_time", "created_at")
    list_filter = ("day_of_week", "class_name", "section", "subject")
    search_fields = ("class_name__name", "section__name", "subject__name")




admin.site.register(ExamRoutine)
admin.site.register(Syllabus)
admin.site.register(Result)
admin.site.register(Routine)
admin.site.register(GalleryItem)
