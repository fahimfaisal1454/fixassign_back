from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError  # <- add this

class Teacher(models.Model):
    full_name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    teacher_intro = models.TextField(blank=True, null=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="teacher_profile",
    )

    def __str__(self):
        return self.full_name


class Staff(models.Model):
    full_name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.full_name


class Student(models.Model):
    GENDER = (("M","Male"),("F","Female"),("O","Other"))

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="student_profile", null=True, blank=True
    )

    full_name   = models.CharField(max_length=120)
    gender      = models.CharField(max_length=1, choices=GENDER, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # FKs to master data
    class_name  = models.ForeignKey("master.ClassName", on_delete=models.PROTECT, related_name="students")
    section     = models.ForeignKey("master.Section", on_delete=models.PROTECT, related_name="students",
                                    null=False, blank=False)  # <-- make optional

    roll_number = models.PositiveIntegerField()
    admission_no= models.CharField(max_length=64, unique=True, blank=True, null=True)

    guardian_name  = models.CharField(max_length=120, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True, null=True)
    address        = models.TextField(blank=True)
    photo          = models.ImageField(upload_to="student_photos/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["class_name__name","section__name","roll_number"]
        unique_together = (("class_name","section","roll_number"),)

    def clean(self):
        # If both chosen, ensure section belongs to class
        if self.section_id and self.class_name_id:
            section_class_id = getattr(self.section, "class_name_id", None)
            if section_class_id and section_class_id != self.class_name_id:
                raise ValidationError("Selected section does not belong to the selected class.")

    def __str__(self):
        sec = self.section or "-"
        return f"{self.full_name} • {self.class_name} {sec} • Roll {self.roll_number}"


class PrincipalList(models.Model):
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='principal_photos/', blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    from_date = models.DateField()
    to_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.to_date})"


class PresidentList(models.Model):
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='president_photos/', blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    from_date = models.DateField()
    to_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.to_date})"
