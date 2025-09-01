from django.db import models
from people.models import Student

# Create your models here.

class ClassRoutine(models.Model):
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=20, blank=True)
    day_of_week = models.CharField(max_length=10)  # e.g., Monday, Tuesday
    period = models.CharField(max_length=20)
    subject = models.CharField(max_length=100)
    teacher = models.CharField(max_length=150)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.class_name} {self.section} - {self.day_of_week} {self.period}"


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
    category = models.CharField(max_length=50, blank=True, null= True) #e.g., "public", "internal"
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
    