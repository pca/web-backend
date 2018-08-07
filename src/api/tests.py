import json
from pathlib import Path

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from api import views
from pca.models import DatabaseConfig
from wca.client import wca_client


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
    @classmethod
    def setUpTestData(cls):
        DatabaseConfig.objects.create(
            active_database='wca1',
            inactive_database='wca2',
        )
        wca_client.import_wca_test_database()

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_national_rankings(self):
        url = reverse('api:national_rankings')
        request = self.factory.get(url)
        response = views.ListNationalRankings.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_national_rankings_selected_events(self):
        url = reverse('api:national_rankings') + '?events=222,333,444&type=all'
        request = self.factory.get(url)
        response = views.ListNationalRankings.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_regional_rankings(self):
        url = reverse('api:regional_rankings') + '?q=region1'
        request = self.factory.get(url)
        response = views.ListRegionalRankings.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_regional_rankings_empty_region(self):
        url = reverse('api:regional_rankings') + '?q='
        request = self.factory.get(url)
        response = views.ListRegionalRankings.as_view()(request)
        response.render()
        assert response.status_code == 404

    def test_regional_rankings_region_404(self):
        url = reverse('api:regional_rankings') + '?q=region404notfound'
        request = self.factory.get(url)
        response = views.ListRegionalRankings.as_view()(request)
        response.render()
        assert response.status_code == 404

    def test_city_provincial_rankings(self):
        url = reverse('api:cityprovincial_rankings') + '?q=pasig'
        request = self.factory.get(url)
        response = views.ListCityProvincialRankings.as_view()(request)
        response.render()
        content = json.loads(response.content)
        assert 'results' in content
        assert response.status_code == 200

    def test_city_provincial_rankings_empty_city(self):
        url = reverse('api:cityprovincial_rankings') + '?q='
        request = self.factory.get(url)
        response = views.ListCityProvincialRankings.as_view()(request)
        response.render()
        assert response.status_code == 404
