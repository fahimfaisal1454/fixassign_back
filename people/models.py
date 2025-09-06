from django.db import models
from django.conf import settings

class Teacher(models.Model):
    full_name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    teacher_intro = models.TextField(blank=True, null=True)

    # NEW: link to login account (unique per teacher)
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
    full_name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    roll_number = models.CharField(max_length=50, blank=True)
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    guardian_name = models.CharField(max_length=150, blank=True)
    guardian_contact = models.CharField(max_length=20, blank=True)
    digital_id_code = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.full_name} ({self.roll_number})"
    


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
