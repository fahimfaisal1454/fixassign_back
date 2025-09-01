from django.contrib import admin
from .models import Acknowledgment

@admin.register(Acknowledgment)
class AcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'date', 'created_at')
    search_fields = ('title',)
    list_filter = ('date', 'created_at')
