from minio import Minio

client = Minio(
    "127.0.0.1:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

print("MinIO buckets: ")
print(client.list_buckets())  # Should show your buckets
