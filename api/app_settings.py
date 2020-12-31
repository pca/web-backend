from django.conf import settings

WCA_CALLBACK_URL = getattr(
    settings,
    "WCA_CALLBACK_URL",
    "http://localhost:8000/accounts/worldcubeassociation/login/callback/",
)
