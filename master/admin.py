from django.contrib import admin
from .models import ClassName, Subject, Section, ClassSubject


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ClassName)
class ClassNameAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "year")
    search_fields = ("name",)
    filter_horizontal = ("sections",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "class_name", "is_theory", "is_practical")
    list_filter = ("class_name", "is_theory", "is_practical")
    search_fields = ("name",)


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "class_name", "section", "subject", "teacher", "is_compulsory", "order")
    list_filter = ("class_name", "section", "subject", "teacher")
    search_fields = ("subject__name", "section__name", "class_name__name", "teacher__full_name")
