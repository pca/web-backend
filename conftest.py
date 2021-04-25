import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from api.tests.factories import RegionUpdateRequestFactory, UserFactory
from wca.tests.factories import (
    ContinentFactory,
    CountryFactory,
    EventFactory,
    PersonFactory,
)

register(UserFactory, "user")
register(RegionUpdateRequestFactory, "region_update_request")

register(CountryFactory, "country")
register(ContinentFactory, "continent")
register(EventFactory, "event")
register(PersonFactory, "person")


@pytest.fixture
def api_client():
    return APIClient()
