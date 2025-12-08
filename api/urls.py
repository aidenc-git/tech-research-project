# api/urls.py

from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, VideoViewSet, VideoProgressViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"progress", VideoProgressViewSet, basename="progress")

urlpatterns = router.urls
