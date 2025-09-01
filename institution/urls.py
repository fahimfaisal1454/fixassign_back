from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'institutions', InstitutionInfoViewSet)
router.register(r'principal-vice-principal', PrincipalVicePrincipalViewSet)
router.register(r'committee-members', ManagingCommitteeMemberViewSet)
router.register(r'notices', NoticeViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 