from rest_framework.routers import SimpleRouter
from .views import AcknowledgmentViewSet

router = SimpleRouter()
router.register(r'acknowledgment', AcknowledgmentViewSet, basename='acknowledgment')

urlpatterns = router.urls
