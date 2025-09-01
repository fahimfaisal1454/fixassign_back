from django.db import models

# Create your models here.

class ContactInfo(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.name

class Allegation(models.Model):
    name = models.CharField(max_length=150)
    contact = models.CharField(max_length=100, blank=True)
    details = models.TextField()
    date_reported = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date_reported}"
