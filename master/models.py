from django.db import models
from django.core.exceptions import ValidationError
from datetime import date

# If you plan to link a teacher later, keep this import; it's safe if unused now.
try:
    from people.models import Teacher
except Exception:
    Teacher = None


class Section(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


def current_year():
    return date.today().year


class ClassName(models.Model):
    # was unique=True (removed); uniqueness is now (name, year)
    name = models.CharField(max_length=255)

    # NEW: single-year academic year (e.g., 2025)
    year = models.PositiveIntegerField(default=current_year, db_index=True)

    sections = models.ManyToManyField(Section, related_name="classes", blank=True)

    class Meta:
        ordering = ["year", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "year"],
                name="uniq_classname_name_year",
            )
        ]

    def __str__(self):
        return f"{self.name} [{self.year}]"


class Subject(models.Model):
    # Non-null to keep uniqueness stable
    name = models.CharField(max_length=255)
    class_name = models.ForeignKey(
        ClassName, on_delete=models.CASCADE, related_name="subjects"
    )

    # Flags for type
    is_theory = models.BooleanField(default=True)
    is_practical = models.BooleanField(default=False)

    class Meta:
        # A subject name appears once per class (and class carries the year)
        unique_together = (("class_name", "name"),)
        ordering = ["class_name__year", "class_name__name", "name"]

    def __str__(self):
        return f"{self.name} - {self.class_name.name} [{self.class_name.year}]"


class ClassSubject(models.Model):
    """
    A subject assigned to a Section of a Class.
    We store class_name for fast filtering and validation.
    """
    class_name = models.ForeignKey(
        ClassName, on_delete=models.CASCADE, related_name="assigned_subjects"
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="class_subjects"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="class_subjects"
    )

    # Optional teacher-link
    teacher = models.ForeignKey(
        "people.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="class_subjects",
    )

    is_compulsory = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # The same subject can't repeat within the same section
        unique_together = (("section", "subject"),)
        indexes = [models.Index(fields=["class_name", "section"])]
        ordering = [
            "class_name__year",
            "class_name__name",
            "section__name",
            "order",
            "subject__name",
        ]

    def clean(self):
        # Subject must belong to the same class (which now includes year)
        if self.subject_id and self.class_name_id and self.subject.class_name_id != self.class_name_id:
            raise ValidationError("Subject must belong to the selected class.")
        # Section must be a member of class_name.sections
        if self.section_id and self.class_name_id and not self.class_name.sections.filter(id=self.section_id).exists():
            raise ValidationError("Section does not belong to the selected class.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.class_name.name} [{self.class_name.year}] ({self.section.name}) - {self.subject.name}"
