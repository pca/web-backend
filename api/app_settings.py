import os

from django.conf import settings

WCA_CALLBACK_URL = getattr(
    settings,
    "WCA_CALLBACK_URL",
    os.getenv(
        "WCA_CALLBACK_URL",
        "http://localhost:8000/accounts/worldcubeassociation/login/callback/",
    ),
)
FB_PAGE_TOKEN = getattr(settings, "FB_PAGE_TOKEN", os.getenv("FB_PAGE_TOKEN"))
FB_PAGE_ID = getattr(settings, "FB_PAGE_ID", os.getenv("FB_PAGE_ID"))
