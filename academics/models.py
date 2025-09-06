from django.db import models
from django.core.exceptions import ValidationError


# ─────────────────────────────────────────────────────────────────────────────
# Period & Classroom
# ─────────────────────────────────────────────────────────────────────────────

class Period(models.Model):
    """
    School-wide time blocks (e.g., 1st period 09:00–09:45).
    """
    name = models.CharField(max_length=50)                # "1st", "2nd", etc.
    order = models.PositiveSmallIntegerField(unique=True) # 1, 2, 3…
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["order"]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Period start_time must be before end_time.")

    def __str__(self):
        return f"{self.name} ({self.start_time}–{self.end_time})"


class Classroom(models.Model):
    """
    A physical room.
    """
    name = models.CharField(max_length=50, unique=True)  # "101", "Lab-A"
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────────────────────────────────────
# Timetable
# ─────────────────────────────────────────────────────────────────────────────

class TimetableEntry(models.Model):
    """Simple class timetable row (no room/teacher)."""

    DAY_CHOICES = [
        ("Mon", "Monday"),
        ("Tue", "Tuesday"),
        ("Wed", "Wednesday"),
        ("Thu", "Thursday"),
        ("Fri", "Friday"),
        ("Sat", "Saturday"),
        ("Sun", "Sunday"),
    ]

    class_name = models.ForeignKey(
        "master.ClassName",
        on_delete=models.PROTECT,
        related_name="timetable_rows",
    )
    section = models.ForeignKey(
        "master.Section",
        on_delete=models.PROTECT,
        related_name="timetable_rows",
    )
    subject = models.ForeignKey(
        "master.Subject",
        on_delete=models.PROTECT,
        related_name="timetable_rows",
    )

    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)  # Mon..Sun
    period = models.CharField(max_length=50, blank=True)               # "1st", "2nd"
    start_time = models.TimeField()
    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day_of_week", "start_time", "class_name__name", "section__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["class_name", "section", "day_of_week", "period", "start_time", "end_time"],
                name="uniq_class_section_day_period_time",
            )
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")
        # subject must belong to class (Subject has FK class_name)
        if self.subject_id and self.class_name_id:
            if getattr(self.subject, "class_name_id", None) != self.class_name_id:
                raise ValidationError("Selected subject does not belong to the selected class.")

    def __str__(self):
        return f"{self.class_name} {self.section} • {self.day_of_week} {self.period or ''} {self.start_time}-{self.end_time}"


# ─────────────────────────────────────────────────────────────────────────────
# Other Academic Models
# ─────────────────────────────────────────────────────────────────────────────

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
    file = models.FileField(upload_to="syllabus_files/", blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.class_name} {self.section} {self.subject}"


class Result(models.Model):
    year = models.PositiveIntegerField()
    category = models.CharField(max_length=50, blank=True, null=True)  # e.g., "public", "internal"
    class_name = models.ForeignKey("master.ClassName", on_delete=models.CASCADE, related_name="results")
    exam_name = models.CharField(max_length=100)
    file = models.FileField(upload_to="result_files/")

    def __str__(self):
        return f"{self.year} ({self.class_name}) - {self.exam_name}"


class Routine(models.Model):
    class_name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, blank=True, null=True)  # e.g., "class_routine", "exam_routine"
    file = models.FileField(upload_to="routine_files/")

    def __str__(self):
        return f"{self.class_name} - {self.category if self.category else 'Routine'}"


class GalleryItem(models.Model):
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Image {self.id}"
