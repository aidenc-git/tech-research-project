# quick_minio_check.py
from datetime import timedelta
import io
from minio import Minio
from minio.error import S3Error

ENDPOINT = "127.0.0.1:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET    = "studentportalvideos"

def main():
    client = Minio(
        ENDPOINT,
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        secure=False,
    )

    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)

    obj_name = "health/test3.txt"
    data_bytes = b"minio ok"
    data_stream = io.BytesIO(data_bytes)  # << wrap as stream

    client.put_object(
        BUCKET,
        obj_name,
        data=data_stream,           # stream with .read()
        length=len(data_bytes),     # total length
        content_type="text/plain",
    )
    print("Uploaded", obj_name)

    found = any(o.object_name == obj_name for o in client.list_objects(BUCKET, prefix="health/", recursive=True))
    print("Found:" if found else "Not found:", obj_name)

    url = client.presigned_get_object(BUCKET, obj_name, expires=timedelta(hours=1))
    print("Presigned URL:", url)

    response = client.get_object(BUCKET, obj_name)
    print("Downloaded content:", response.read().decode("utf-8"))
    response.close()
    response.release_conn()

if __name__ == "__main__":
    try:
        main()
    except S3Error as e:
        print("S3Error:", e)
