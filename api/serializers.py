from rest_framework import serializers
from .models import PortalUser, Course, Video, VideoProgress, Like, Comment, Bookmark, Rating, SearchLog
from django.contrib.auth.hashers import make_password


AUTH_USER_MODEL = "users"

class PortalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        fields = "__all__"
        

    # override create to hash password if needed
    def create(self, validated_data):
        # Hash the password before saving
        validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().update(instance, validated_data)

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "course_id",
            "title",
            "description",
            "created_by",
            "created_at",            
            "instructor",      # will be user_id
            "category",
            "level",
        ]

class VideoSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.course_id', read_only=True)
    file = serializers.FileField(write_only=True)  # for uploads

    class Meta:
        model = Video
        fields = "__all__"
        read_only_fields = ["video_id", "file_path", "uploaded_by", "uploaded_at"]
    
    def get_play_url(self, obj):
        if not obj.file_url:
            return None

        client = get_minio_client()
        bucket = settings.MINIO_BUCKET_NAME
        try:
            return client.get_presigned_url(
                method="GET",
                bucket_name=bucket,
                object_name=obj.file_url,
                expires=timedelta(hours=1),
            )
        except Exception:
            return None
    
      
    def validate_difficulty_level(self, value):
        if value is None:
            return value
        allowed = {"basic", "intermediate", "advanced"}
        if value not in allowed:
            raise serializers.ValidationError(f"Must be one of {allowed}")
        return value

    def to_internal_value(self, data):
        # Allow tags to be sent as JSON string or object
        if "tags" in data and isinstance(data.get("tags"), str):
            try:
                data._mutable = True  # when QueryDict
            except Exception:
                pass
            try:
                data["tags"] = json.loads(data["tags"])
            except Exception:
                raise serializers.ValidationError({"tags": "Invalid JSON"})
        return super().to_internal_value(data)

    def create(self, validated_data):
        file = validated_data.pop("file")
        user = self.context["request"].user

        # MinIO client
        from minio import Minio
        from django.conf import settings
        import uuid

        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )

        bucket = settings.MINIO_BUCKET_NAME
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)

        # Generate unique file name
        filename = f"{uuid.uuid4()}_{file.name}"
        file_path = f"{bucket}/{filename}"

        # Upload to MinIO
        minio_client.put_object(
            bucket,
            filename,
            file,
            length=file.size,
            content_type=file.content_type,
        )

        # Save metadata in Postgres
        video = Video.objects.create(
            uploaded_by=user,
            file_path=file_path,
            **validated_data,
        )
        return video


class VideoProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoProgress
        fields = "__all__"

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"

class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = "__all__"

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"

class SearchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchLog
        fields = "__all__"

