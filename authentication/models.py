from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('General', 'General'),
        ('Teacher', 'Teacher'),
    )

    role = models.CharField(max_length=40, choices=ROLE_CHOICES, default='General',blank=True, null=True)
    profile_picture = models.ImageField(upload_to='image/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'Admin'
        elif not self.role:  # If the role is not provided, assign the default 'Assistant Accountant'
            self.role = 'General'
        super().save(*args, **kwargs)  # Call the original save method

    def __str__(self):
        return self.username
