import os

from django.conf import settings

WCA_DEFAULT_CALLBACK_URL = getattr(
    settings,
    "WCA_DEFAULT_CALLBACK_URL",
    os.getenv(
        "WCA_DEFAULT_CALLBACK_URL",
        "http://localhost:8080/wca-callback",
    ),
)
WCA_ALLOWED_CALLBACK_URLS = getattr(
    settings, "WCA_ALLOWED_CALLBACK_URLS", os.getenv("WCA_ALLOWED_CALLBACK_URLS", "")
).split(",")

FB_PAGE_TOKEN = getattr(settings, "FB_PAGE_TOKEN", os.getenv("FB_PAGE_TOKEN"))
FB_PAGE_ID = getattr(settings, "FB_PAGE_ID", os.getenv("FB_PAGE_ID"))
FB_PAGE_FEED_LIMIT = getattr(
    settings, "FB_PAGE_FEED_LIMIT", os.getenv("FB_PAGE_FEED_LIMIT", 5)
)
