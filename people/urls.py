from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeacherViewSet, StaffViewSet, StudentViewSet, 
    PrincipalListViewSet, PresidentListViewSet
)

router = DefaultRouter()
router.register(r'teachers', TeacherViewSet)
router.register(r'staff', StaffViewSet)
router.register(r'students', StudentViewSet)
router.register(r'principal-list', PrincipalListViewSet)
router.register(r'president-list', PresidentListViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 