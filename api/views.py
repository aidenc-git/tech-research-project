import os
import unicodedata
from uuid import uuid4
from datetime import timedelta

from django.conf import settings
from django.utils.text import get_valid_filename

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import *
from .serializers import *
from .minio_client import get_minio_client
from django.conf import settings
from minio.error import S3Error


def _safe_name(name: str) -> str:
    # normalize unicode + strip weird chars
    name = unicodedata.normalize("NFKD", name)
    return get_valid_filename(name)


class PortalUserViewSet(viewsets.ModelViewSet):
    queryset = PortalUser.objects.all()
    serializer_class = PortalUserSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    

#class VideoViewSet(viewsets.ModelViewSet):
#    queryset = Video.objects.all()
#    serializer_class = VideoSerializer
#    permission_classes = [permissions.IsAuthenticated]


class VideoProgressViewSet(viewsets.ModelViewSet):
    queryset = VideoProgress.objects.all()
    serializer_class = VideoProgressSerializer

class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class BookmarkViewSet(viewsets.ModelViewSet):
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

class SearchLogViewSet(viewsets.ModelViewSet):
    queryset = SearchLog.objects.all()
    serializer_class = SearchLogSerializer
    
class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.select_related("course", "uploaded_by").all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"], url_path="play")
    def play(self, request, pk=None):
        """
        Return a presigned URL for this video.
        Response JSON **must** be: { "url": "<signed-url>" }
        """
        video = self.get_object()

        # IMPORTANT: file_url should be object path in the bucket, e.g.
        #   "Web Development/test.mp4"
        object_name = video.file_url  

        client = get_minio_client()
        bucket = settings.MINIO_BUCKET_NAME  # e.g. "studentportalvideos"

        try:
            presigned_url = client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(hours=1),
            )
            return Response({"url": presigned_url})
        except Exception as e:
            # This will cause frontend to get HTTP 500
            return Response(
                {"detail": "Unable to get video URL", "error": str(e)},
                status=500,
            )
