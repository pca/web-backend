import factory
from factory.django import DjangoModelFactory

from ..models import Continent, Country, Event, Person


class ContinentFactory(DjangoModelFactory):
    id = "_Asia"
    name = "Asia"
    record_name = "AsR"
    latitude = 34364439
    longitude = 108330700
    zoom = 2

    class Meta:
        model = Continent


class CountryFactory(DjangoModelFactory):
    id = "Philippines"
    name = "Philippines"
    continent = factory.SubFactory(ContinentFactory)
    iso2 = "PH"

    class Meta:
        model = Country


class EventFactory(DjangoModelFactory):
    id = "333"
    name = "3x3x3 Cube"
    rank = 10
    format = "time"
    cell_name = "3x3x3 Cube"

    class Meta:
        model = Event


class PersonFactory(DjangoModelFactory):
    id = "2021DELA01"
    subid = 1
    name = "Juan dela Cruz"
    country = factory.SubFactory(CountryFactory)
    gender = Person.GENDER_MALE

    class Meta:
        model = Person
