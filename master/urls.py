from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassNameViewSet, SubjectViewSet, GalleryItemViewSet, BannerItemViewSet,
    SectionViewSet
)

router = DefaultRouter()
router.register(r'sections', SectionViewSet)
router.register(r'classes', ClassNameViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'gallery', GalleryItemViewSet)
router.register(r'banners', BannerItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
