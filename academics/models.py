from django.db import models
from django.db.models import Q, F, CheckConstraint, UniqueConstraint, Index
from django.core.exceptions import ValidationError
from django.conf import settings
from people.models import Student
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
    DAY_CHOICES = [
        ("Mon", "Monday"),
        ("Tue", "Tuesday"),
        ("Wed", "Wednesday"),
        ("Thu", "Thursday"),
        ("Fri", "Friday"),
        ("Sat", "Saturday"),
        ("Sun", "Sunday"),
    ]

    class_name = models.ForeignKey( "master.ClassName",on_delete=models.PROTECT, related_name="timetable_rows")
    section = models.ForeignKey( "master.Section",on_delete=models.PROTECT, related_name="timetable_rows")
    subject = models.ForeignKey( "master.Subject", on_delete=models.PROTECT, related_name="timetable_rows")
    teacher = models.ForeignKey( "people.Teacher", on_delete=models.SET_NULL,  null=True, blank=True, related_name="timetable_rows")
    classroom = models.ForeignKey(Classroom,on_delete=models.PROTECT,related_name="timetable_rows",null=True,blank=True, )

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
def clean(self):
        super().clean()
        if self.class_name_id and self.section_id and self.classroom_id:
            cap = getattr(self.classroom, "capacity", None)
            if cap and cap > 0:
                size = Student.objects.filter(class_name=self.class_name, section=self.section).count()
                if size > cap:
                    raise ValidationError({
                        "classroom": (
                            f"Room capacity ({cap}) is less than class size ({size}). "
                            f"Select a larger room or split the section."
                        )
                    })

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




class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("EXCUSED", "Excused"),
    ]

    timetable = models.ForeignKey("academics.TimetableEntry", on_delete=models.PROTECT, related_name="attendance_records")
    date = models.DateField()
    student = models.ForeignKey("people.Student", on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")
    remarks = models.CharField(max_length=255, blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="marked_attendance")
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["timetable", "date", "student"], name="uniq_attendance_row")
        ]
        ordering = ["-date", "timetable_id", "student_id"]

    def __str__(self):
        return f"{self.date} • {self.timetable} • {self.student} • {self.status}"


class GradeScale(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # keep only one scale active
        if self.is_active:
            GradeScale.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class GradeScale(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # keep only one scale active
        if self.is_active:
            GradeScale.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class GradeBand(models.Model):
    """
    Non-overlapping, unique grade bands within a GradeScale.
    Example (0–100): A+ 80–100, A 70–79, ...
    """
    scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE, related_name="bands")
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    letter = models.CharField(max_length=5)
    gpa = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        ordering = ["-min_score"]
        constraints = [
            # min ≤ max
            CheckConstraint(
                check=Q(min_score__lte=F("max_score")),
                name="grades_min_le_max",
            ),
            # keep inside 0–100 (adjust if your total isn’t 100)
            CheckConstraint(
                check=Q(min_score__gte=0) & Q(max_score__lte=100),
                name="grades_within_0_100",
            ),
            # one letter per scale
            UniqueConstraint(
                fields=["scale", "letter"],
                name="uniq_scale_letter",
            ),
            # prevent exact duplicate range within same scale
            UniqueConstraint(
                fields=["scale", "min_score", "max_score"],
                name="uniq_scale_exact_range",
            ),
        ]
        indexes = [
            Index(fields=["scale", "min_score", "max_score"], name="idx_scale_range"),
        ]

    def clean(self):
        super().clean()

        if self.min_score > self.max_score:
            raise ValidationError("min_score cannot be greater than max_score.")

        # Overlap rule (same scale):
        # existing.min ≤ self.max  AND  existing.max ≥ self.min
        overlap_q = Q(min_score__lte=self.max_score) & Q(max_score__gte=self.min_score)
        clash = (
            GradeBand.objects
            .filter(scale=self.scale)
            .exclude(pk=self.pk)
            .filter(overlap_q)
            .first()
        )
        if clash:
            raise ValidationError(
                f"This range ({self.min_score}-{self.max_score}) overlaps with "
                f"{clash.letter} ({clash.min_score}-{clash.max_score}) in the same scale."
            )

    def __str__(self):
        return f"{self.letter} {self.min_score}-{self.max_score} → {self.gpa}"


# ─────────────────────────────────────────────────────────────────────────────
# Exams & marks
# ─────────────────────────────────────────────────────────────────────────────

class Exam(models.Model):
    class_name = models.ForeignKey("master.ClassName", on_delete=models.CASCADE)
    section = models.ForeignKey("master.Section", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("class_name", "section", "name")

    def __str__(self):
        return f"{self.name} ({self.class_name} {self.section})"


class ExamMark(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="marks")
    student = models.ForeignKey("people.Student", on_delete=models.CASCADE)
    subject = models.ForeignKey("master.Subject", on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    letter = models.CharField(max_length=5, blank=True)

    class Meta:
        unique_together = ("exam", "student", "subject")

    def clean(self):
        # subject must belong to exam.class_name
        if getattr(self.subject, "class_name_id", None) != self.exam.class_name_id:
            raise ValidationError("Subject does not belong to the exam’s class.")

        # ✅ Ensure the student belongs to the same class/section as the exam
        stu = self.student
        if getattr(stu, "class_name_id", None) != self.exam.class_name_id or getattr(stu, "section_id", None) != self.exam.section_id:
            raise ValidationError("Student is not in the class/section for this exam.")

    def _apply_grade(self):
        scale = GradeScale.objects.filter(is_active=True).first()
        if not scale:
            self.gpa = None
            self.letter = ""
            return
        band = scale.bands.filter(min_score__lte=self.score, max_score__gte=self.score).first()
        if band:
            self.gpa = band.gpa
            self.letter = band.letter
        else:
            # score falls outside bands (e.g., no coverage); clear grade
            self.gpa = None
            self.letter = ""

    def save(self, *args, **kwargs):
        self.full_clean()
        self._apply_grade()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} • {self.subject} • {self.score} → {self.letter}/{self.gpa}"