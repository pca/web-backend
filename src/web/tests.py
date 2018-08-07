from django.test import TestCase
from django.urls import reverse

from pca.client import pca_client


class WebTestCase(TestCase):
    def test_profile_view(self):
        wca_profile_data = {
            'id': 1,
            'wca_id': None,
            'name': 'Juan Dela Cruz',
            'gender': 'm',
            'country_iso2': 'PH',
            'delegate_status': None,
            'avatar': {
                'url': 'https://www.worldcubeassociation.org/assets/missing_avatar_thumb-f0ea801c804765a22892b57636af829edbef25260a65d90aaffbd7873bde74fc.png',
                'thumb_url': 'https://www.worldcubeassociation.org/assets/missing_avatar_thumb-f0ea801c804765a22892b57636af829edbef25260a65d90aaffbd7873bde74fc.png',
                'is_default': True,
            },
            'created_at': '2017-01-12T07:53:16.000Z',
            'updated_at': '2018-07-29T14:08:47.000Z',
        }
        wca_profile = pca_client.create_user(wca_profile_data)

        self.client.force_login(wca_profile.user)
        response = self.client.get(reverse('web:profile'))

        assert response.status_code == 200

    def test_profile_anonymous_view(self):
        response = self.client.get(reverse('web:profile'))

        assert response.status_code == 302

    def test_competitions_view(self):
        response = self.client.get(reverse('web:competitions'))

        assert response.status_code == 200

    def test_national_rankings_view(self):
        response = self.client.get(reverse('web:national_rankings'))

        assert response.status_code == 200

    def test_regional_rankings_view(self):
        response = self.client.get(reverse('web:regional_rankings'))

        assert response.status_code == 200

    def test_regional_rankings_404_view(self):
        url = reverse('web:regional_rankings') + '?region=region404notfound'
        response = self.client.get(url)

        assert response.status_code == 404

    def test_city_provincial_rankings_view(self):
        response = self.client.get(reverse('web:cityprovincial_rankings'))

        assert response.status_code == 200

    def test_city_provincial_rankings_404_view(self):
        url = reverse('web:cityprovincial_rankings') + '?cityprovince=city404notfound'
        response = self.client.get(url)

        assert response.status_code == 404
