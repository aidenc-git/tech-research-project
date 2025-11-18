from api.models import PortalUser
u = PortalUser.objects.create_superuser(
    email="aiden1@gmail.com",
    password="test123",
    name="Aiden1"
)
print(u.password)  # should start with 'pbkdf2_sha256$'
