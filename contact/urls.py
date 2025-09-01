from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactInfoViewSet, AllegationViewSet

router = DefaultRouter()
router.register(r'contacts', ContactInfoViewSet)
router.register(r'allegations', AllegationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 