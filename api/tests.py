import json

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from api import views


class LocationAPITestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_list_regions(self):
        url = reverse('api:regions')
        request = self.factory.get(url)
        response = views.ListRegions.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_list_citiesprovinces(self):
        url = reverse('api:citiesprovinces')
        request = self.factory.get(url)
        response = views.ListCitiesProvinces.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200


class CompetitionsAPITestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_list_competitions(self):
        url = reverse('api:competitions')
        request = self.factory.get(url)
        response = views.ListCompetitions.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200


class RankingsAPITestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_national_rankings(self):
        url = reverse('api:national_rankings')
        request = self.factory.get(url)
        response = views.ListNational.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_regional_rankings(self):
        url = reverse('api:regional_rankings')
        request = self.factory.get(url)
        response = views.ListRegionalRankings.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_city_provincial_rankings(self):
        url = reverse('api:cityprovincial_rankings')
        request = self.factory.get(url)
        response = views.ListCityProvincialRankings.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200
