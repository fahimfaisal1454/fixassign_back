from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.conf import settings

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
    """
    A single row in the class timetable with optional teacher & room.
    """

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

    # NEW: optional teacher & classroom
    teacher = models.ForeignKey(
        "people.Teacher",
        on_delete=models.PROTECT,
        related_name="timetable_rows",
        null=True,
        blank=True,
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.PROTECT,
        related_name="timetable_rows",
        null=True,
        blank=True,
    )

    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)  # Mon..Sun
    period = models.CharField(max_length=50, blank=True)               # "1st", "2nd" (optional)
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Kept for backwards compatibility; prefer using classroom FK above.
    room = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day_of_week", "start_time", "class_name__name", "section__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["class_name", "section", "day_of_week", "period", "start_time", "end_time"],
                name="uniq_class_section_day_period_time",
            )
        ]

    # ----- helpers -----------------------------------------------------------

    @staticmethod
    def _overlap_q(start, end):
        """
        Build a Q() condition for time range overlap:
        [start, end) overlaps [other.start, other.end)
        """
        return Q(start_time__lt=end) & Q(end_time__gt=start)

    def clean(self):
        # 1) time sanity
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

        # 2) subject must belong to class (assuming Subject has FK class_name)
        if self.subject_id and self.class_name_id:
            subj_class_id = getattr(self.subject, "class_name_id", None)
            if subj_class_id and subj_class_id != self.class_name_id:
                raise ValidationError("Selected subject does not belong to the selected class.")

        # Prepare base queryset of "other" rows this could conflict with
        others = (
            TimetableEntry.objects
            .filter(day_of_week=self.day_of_week)
            .exclude(pk=self.pk)
            .filter(self._overlap_q(self.start_time, self.end_time))
        )

        # 3) Teacher cannot be in two places at the same time
        if self.teacher_id:
            teacher_conflict = others.filter(teacher_id=self.teacher_id).first()
            if teacher_conflict:
                raise ValidationError(
                    f"Teacher is already scheduled at {teacher_conflict.start_time}–"
                    f"{teacher_conflict.end_time} for {teacher_conflict.class_name} "
                    f"{teacher_conflict.section}."
                )

        # 4) Room/classroom cannot hold two classes at the same time
        # Prefer FK if provided; else use legacy room text
        if self.classroom_id:
            room_conflict = others.filter(classroom_id=self.classroom_id).first()
            if room_conflict:
                raise ValidationError(
                    f"Classroom '{self.classroom}' is already occupied at "
                    f"{room_conflict.start_time}–{room_conflict.end_time}."
                )
        elif (self.room or "").strip():
            room_conflict = others.filter(room__iexact=self.room.strip()).first()
            if room_conflict:
                raise ValidationError(
                    f"Room '{self.room}' is already occupied at "
                    f"{room_conflict.start_time}–{room_conflict.end_time}."
                )

        # 5) Two teachers cannot teach the same class/section at the same time
        class_slot_conflict = others.filter(
            class_name_id=self.class_name_id,
            section_id=self.section_id,
        ).exclude(teacher_id=self.teacher_id).first()
        if class_slot_conflict:
            raise ValidationError(
                "This class/section is already assigned to another teacher in the same time range."
            )

    def save(self, *args, **kwargs):
        # Ensure validations run on programmatic saves as well
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        teacher_part = f" • {self.teacher}" if self.teacher_id else ""
        room_part = f" • {self.classroom or self.room}" if (self.classroom_id or self.room) else ""
        period_part = f" {self.period}" if self.period else ""
        return (
            f"{self.class_name} {self.section} • {self.day_of_week}{period_part} "
            f"{self.start_time}-{self.end_time}{teacher_part}{room_part}"
        )


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



class TeacherAssignment(models.Model):
    """
    Assign a teacher to a class/section/subject on a given day & period (+optional room).
    This is separate from TimetableEntry and can live side-by-side.
    """
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
        related_name="teacher_assignments",
    )
    section = models.ForeignKey(
        "master.Section",
        on_delete=models.PROTECT,
        related_name="teacher_assignments",
    )
    subject = models.ForeignKey(
        "master.Subject",
        on_delete=models.PROTECT,
        related_name="teacher_assignments",
    )
    # Use the project’s configured user model
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teacher_assignments",
    )

    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)  # Mon..Sun
    period = models.CharField(max_length=50)  # textual slot like "1st", "2nd"
    room = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day_of_week", "period", "class_name__name", "section__name"]
        # Hard constraints that don’t require time fields:
        constraints = [
            # A class/section can only have one teacher in a slot
            models.UniqueConstraint(
                fields=["class_name", "section", "day_of_week", "period"],
                name="uniq_class_section_day_period_assignment",
            ),
            # A teacher can only teach once in a slot
            models.UniqueConstraint(
                fields=["teacher", "day_of_week", "period"],
                name="uniq_teacher_day_period_assignment",
            ),
            # If room is provided, one room per slot (skip when room is null/blank)
            models.UniqueConstraint(
                fields=["room", "day_of_week", "period"],
                name="uniq_room_day_period_assignment",
                condition=models.Q(room__isnull=False) & ~models.Q(room=""),
            ),
        ]

    def clean(self):
        # Ensure subject belongs to selected class
        if self.subject_id and self.class_name_id:
            if getattr(self.subject, "class_name_id", None) != self.class_name_id:
                raise ValidationError("Selected subject does not belong to the selected class.")

    def __str__(self):
        return f"{self.class_name} {self.section} • {self.day_of_week} {self.period} • {self.subject} • {self.teacher}"