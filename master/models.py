from django.db import models

# Create your models here.

class ClassName(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Subject(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name='subjects')


    def __str__(self):
        return f"{self.name} - {self.class_name.name}"
    



class GalleryItem(models.Model):
    caption = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=100, blank=True, null=True)  # 👈 Added field
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.caption or 'Untitled Image'} - {self.category or 'Uncategorized'}"

    

class Banner(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='banners/')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.title or "Untitled Banner"  
