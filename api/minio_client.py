# api/minio_client.py
from minio import Minio
from django.conf import settings

def get_minio_client():
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,                      # True only if you're using HTTPS
        #secure=settings.MINIO_USE_SSL,
    )
