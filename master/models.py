from django.db import models

# ---------- NEW ----------
class Section(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
# -------------------------

class ClassName(models.Model):
    name = models.CharField(max_length=255)
    # ✅ a class can have many sections (A,B,C…)
    sections = models.ManyToManyField(Section, related_name="classes", blank=True)

    class Meta:
        unique_together = [("name",)]  # same class name only once
        ordering = ["name"]

    def __str__(self):
        return self.name

# master/models.py

class Subject(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    class_name = models.ForeignKey(ClassName, on_delete=models.CASCADE, related_name='subjects')

    is_theory = models.BooleanField(default=True)
    is_practical = models.BooleanField(default=False)

    class Meta:
        # one "Biology" per class
        unique_together = (("class_name", "name"),)
        ordering = ["class_name__name", "name"]

    def __str__(self):
        return f"{self.name} - {self.class_name.name}"



class GalleryItem(models.Model):
    caption = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='gallery/')
    category = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.caption or 'Untitled Image'} - {self.category or 'Uncategorized'}"

class Banner(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='banners/')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.title or "Untitled Banner"
