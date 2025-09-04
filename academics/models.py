from django.db import models
from people.models import Student  # (left as-is, even if unused)
from django.conf import settings
from master.models import ClassName, Subject

# Create your models here.

class ClassRoutine(models.Model):
    """
    Timetable row with proper relations:
    - class_name -> FK to master.ClassName
    - subject    -> FK to master.Subject
    - teacher    -> FK to authentication.User (role should be 'Teacher')
    Section stays a simple CharField, like your current design.
    """
    DAYS = [
        ("Mon", "Mon"),
        ("Tue", "Tue"),
        ("Wed", "Wed"),
        ("Thu", "Thu"),
        ("Fri", "Fri"),
        ("Sat", "Sat"),
        ("Sun", "Sun"),
    ]

    class_name = models.ForeignKey(
        ClassName,
        on_delete=models.PROTECT,
        related_name="routines",
    )
    section = models.CharField(max_length=20, blank=True)
    day_of_week = models.CharField(max_length=10)  # e.g., Monday, Tuesday (kept as-is)
    period = models.CharField(max_length=20)       # kept as-is for your existing UI
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="routines",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="class_routines",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        indexes = [
            models.Index(fields=["day_of_week", "start_time", "end_time"]),
            models.Index(fields=["class_name", "section"]),
            models.Index(fields=["teacher", "day_of_week"]),
        ]

    def __str__(self):
        sec = f" {self.section}" if self.section else ""
        t_label = getattr(self.teacher, "username", "Unassigned")
        return f"{self.class_name}{sec} - {self.day_of_week} {self.period} [{self.subject.name}] ({t_label})"


class ExamRoutine(models.Model):
    exam_name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.exam_name} - {self.class_name} {self.section} {self.subject}"


class Syllabus(models.Model):
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100)
    file = models.FileField(upload_to='syllabus_files/', blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.class_name} {self.section} {self.subject}"


class Result(models.Model):
    year = models.PositiveIntegerField()
    category = models.CharField(max_length=50, blank=True, null=True)  # e.g., "public", "internal"
    class_name = models.ForeignKey(
        "master.ClassName",
        on_delete=models.CASCADE,
        related_name="results"
    )
    exam_name = models.CharField(max_length=100)
    file = models.FileField(upload_to='result_files/')

    def __str__(self):
        return f"{self.year} ({self.class_name}) - {self.exam_name}"


class Routine(models.Model):
    class_name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, blank=True, null=True)  # e.g., "class_routine", "exam_routine"
    file = models.FileField(upload_to='routine_files/')

    def __str__(self):
        return f"{self.class_name} - {self.category if self.category else 'Routine'}"
