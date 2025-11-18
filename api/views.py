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
from .minio_client import get_minio

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
    queryset = Video.objects.select_related("course", "uploaded_by").all().order_by("-uploaded_at")
    serializer_class = VideoSerializer
    permission_classes = [permissions.AllowAny]  # change to IsAuthenticated for real auth
    parser_classes = [MultiPartParser, FormParser]  # so multipart/form-data works

    @action(methods=["post"], detail=False, url_path="upload")
    def upload(self, request, *args, **kwargs):
        """
        POST /api/videos/upload/
        form-data:
          - file: <video file>
          - title: string
          - course: <course_id>  (foreign key id)
          - uploaded_by: <user_id>  (foreign key id)
          - description: string (optional)
          - difficulty_level: basic|intermediate|advanced (optional)
          - tags: JSON string or object (optional)
          - thumbnail_url, duration, transcript (optional)
        """
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        file = ser.validated_data.pop("file")
        original_name = _safe_name(file.name)
        ext = os.path.splitext(original_name)[1] or ""
        object_name = f"videos/{uuid4().hex}{ext}"

        # Ensure bucket exists (cheap check on each call; OK for dev)
        client = get_minio()
        bucket = settings.MINIO_BUCKET
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        # Upload stream to MinIO
        # NOTE: Django InMemoryUploadedFile/TemporaryUploadedFile have .file + .size
        client.put_object(
            bucket,
            object_name,
            data=file.file,
            length=file.size,
            content_type=file.content_type or "application/octet-stream",
        )

        # Persist metadata in Postgres; store object path in file_url
        video: Video = Video.objects.create(
            **ser.validated_data,
            file_url=object_name,
        )

        # Return a presigned URL (1 hour) for immediate playback/testing
        presigned = client.presigned_get_object(bucket, object_name, expires=timedelta(hours=1))

        out = VideoSerializer(video).data
        out["presigned_url"] = presigned
        out["object_url"] = f"{settings.MINIO_PUBLIC_ENDPOINT}/{bucket}/{object_name}"

        return Response(out, status=status.HTTP_201_CREATED)    
