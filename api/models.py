# Extendable User model
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.conf import settings

#from django.contrib.postgres.fields import JSONField
from pgvector.django import VectorField  # requires pgvector extension

class PortalUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.password = make_password(password)
        else:
            raise ValueError("Password must be set")
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not password:
            raise ValueError("Superuser must have a password")
        
        return self.create_user(email, password, **extra_fields)


class PortalUser(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(
        max_length=20,
        choices=[("student", "student"), ("instructor", "instructor"), ("admin", "admin")],
        default="student",
    )
    profile_picture = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # required by Django auth
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

# 👇 this is important so things expecting `id` (like SimpleJWT) work
    @property
    def id(self):
        return self.user_id
    
    USERNAME_FIELD = "email"        # login with email
    REQUIRED_FIELDS = ["name"]      # prompted when creating superuser

    objects = PortalUserManager()

    class Meta:
        db_table = "users"          # ✅ map to existing table
        managed = False

    def set_password(self, raw_password):
        super().set_password(raw_password)
        self.password = self.password  # Django stores hash in .password
        self.password = None  # avoid confusion
    
    def check_password(self, raw_password):
        return super().check_password(raw_password)    
        
    def __str__(self):
        return self.email


    def has_perm(self, perm, obj=None):
        """
        Does the user have a specific permission?
        For now: superusers have all perms.
        """
        return self.is_superuser

    def has_module_perms(self, app_label):
        """
        Does the user have permissions to view the app `app_label`?
        For now: superusers can see all apps in the admin.
        """
        return self.is_superuser


class Course(models.Model):
    course_id = models.AutoField(primary_key=True, db_column='course_id')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    #instructor = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="courses")
    category = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        PortalUser,
        db_column="created_by",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_created",
    )

    
    # NEW: instructor, mapped to courses.instructor_id
    instructor = models.ForeignKey(
        PortalUser,
        db_column="instructor_id",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_taught",
    )


    class Meta:
        db_table = "courses"
        managed = False

    def __str__(self):
        return self.title

   
class Video(models.Model):
    video_id = models.AutoField(primary_key=True, db_column='video_id')
    course = models.ForeignKey(
        Course,
        models.CASCADE,
        db_column='course_id',
        related_name='videos',
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        'PortalUser',  # assumes you mapped your users table to PortalUser
        on_delete=models.SET_NULL,
        db_column='uploaded_by',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    file_url = models.CharField(max_length=500)
    thumbnail_url = models.CharField(max_length=500, null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    transcript = models.TextField(null=True, blank=True)
    difficulty_level = models.CharField(
        max_length=20,
        choices=[('basic', 'Basic'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        null=True,
        blank=True
    )
    tags = models.JSONField(null=True, blank=True)
    embedding_vector = VectorField(dimensions=768, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "videos"
        managed = False  # Django won’t try to recreate/alter the table


class VideoProgress(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="video_progress")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="progress")
    watched_seconds = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_progress"
        managed = False
        unique_together = ("user", "video")

class Like(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="likes")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "likes"
        managed = False
        unique_together = ("user", "video")

class Comment(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="comments")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "comments"
        managed = False

class Bookmark(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="bookmarks")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookmarks"
        managed = False
        unique_together = ("user", "video")

class Rating(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="ratings")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="ratings")
    rating = models.IntegerField()  # e.g. 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ratings"
        managed = False
        unique_together = ("user", "video")

class SearchLog(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.SET_NULL, null=True, blank=True)
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "search_logs"
        managed = False


