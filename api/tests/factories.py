import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from ..models import RegionUpdateRequest

User = get_user_model()


class UserFactory(DjangoModelFactory):
    wca_id = "2021DELA01"
    region = User.REGION_NCR

    class Meta:
        model = User


class RegionUpdateRequestFactory(DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    region = User.REGION_4A

    class Meta:
        model = RegionUpdateRequest
