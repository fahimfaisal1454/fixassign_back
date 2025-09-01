# school/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()
router.register('classes', ClassNameViewSet)
router.register('subjects', SubjectViewSet)
router.register('gallery', GalleryItemViewSet)
router.register('banner', BannerItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
