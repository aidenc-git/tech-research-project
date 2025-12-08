from api.models import PortalUser
u = PortalUser.objects.get(email="aiden4@gmail.com")  # or whatever email you used
u.check_password("Test123")
