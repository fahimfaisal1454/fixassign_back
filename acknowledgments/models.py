from django.db import models
from django.core.validators import FileExtensionValidator

class Acknowledgment(models.Model):
    title = models.CharField(max_length=255)
    # Frontend sends the file under "image" – keep the field name "image"
    image = models.FileField(
        upload_to='acknowledgments/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tif', 'tiff', 'pdf']
        )]
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']  # newest first

    def __str__(self):
        return self.title
