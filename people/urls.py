from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeacherViewSet, StaffViewSet, StudentViewSet, 
    PrincipalListViewSet, PresidentListViewSet
)

router = DefaultRouter()

router.register(r'staff', StaffViewSet)
router.register(r"students", StudentViewSet, basename="students")
router.register(r'principal-list', PrincipalListViewSet)
router.register(r'president-list', PresidentListViewSet)
router.register(r'teachers', TeacherViewSet, basename='teachers')
urlpatterns = [
    path('', include(router.urls)),
] 