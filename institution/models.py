from django.db import models


class InstitutionInfo(models.Model):
    name = models.CharField(max_length=255)
    government_approval_number = models.CharField(max_length=100, blank=True)
    government_approval_date = models.DateField(blank=True, null=True)
    history = models.TextField(blank=True)
    mission = models.TextField(blank=True, null=True)
    objective = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    address_code = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='institution_logos/', blank=True, null=True)
    institution_image = models.ImageField(upload_to='institution_images/', blank=True, null=True)

    def __str__(self):
        return self.name


class PrincipalVicePrincipal(models.Model):
    DESIGNATION_CHOICES = [
        ("principal", "Principal"),
        ("vice_principal", "Vice Principal"),
        ("headmaster", "Headmaster"),
        ("headmistress", "Headmistress"),
    ]
    category = models.CharField(max_length=100, null= True, blank= True)
    full_name = models.CharField(max_length=150)
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.designation})"



class ManagingCommitteeMember(models.Model):
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='committee_photos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
   
    def __str__(self):
        return f"{self.full_name} ({self.role})"
    



class Notice(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='notices/', blank=True, null=True)  # Changed to FileField
    category = models.CharField(max_length=100, blank=True, null=True)  # e.g., "general", "admission", "exam"
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)


    def __str__(self):
        return self.title
